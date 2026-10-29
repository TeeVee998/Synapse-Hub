param()

[System.Reflection.Assembly]::LoadWithPartialName("System.IO.Compression.FileSystem") | Out-Null

function Read-ExcelSheet {
    param(
        [string]$FilePath,
        [string]$SheetName = ""
    )

    if ([string]::IsNullOrWhiteSpace($FilePath) -or -not (Test-Path -LiteralPath $FilePath)) {
        if ($env:EXCEL_TEST_PATH -and (Test-Path -LiteralPath $env:EXCEL_TEST_PATH)) {
            $FilePath = $env:EXCEL_TEST_PATH
        } else {
            # Search workspace or Downloads for any recent xlsx file
            $found = Get-ChildItem -Path "." -Filter "*.xlsx" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1
            if (-not $found) {
                $found = Get-ChildItem -Path "$env:USERPROFILE\Downloads" -Filter "*.xlsx" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            }
            if ($found) { $FilePath = $found.FullName }
        }
    }

    if ([string]::IsNullOrWhiteSpace($FilePath) -or -not (Test-Path -LiteralPath $FilePath)) {
        throw "Excel file not found. Please provide a valid file_path."
    }

    $fullPath = (Get-Item $FilePath).FullName
    $zip = [System.IO.Compression.ZipFile]::OpenRead($fullPath)

    try {
        # 1. Read shared strings
        $sharedStrings = New-Object System.Collections.Generic.List[string]
        $ssEntry = $zip.GetEntry("xl/sharedStrings.xml")
        if ($ssEntry) {
            $stream = $ssEntry.Open()
            $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
            $ssXml = [xml]$reader.ReadToEnd()
            $reader.Close()
            $stream.Close()
            foreach ($si in $ssXml.sst.si) {
                $sharedStrings.Add($si.InnerText)
            }
        }

        # 2. Determine target sheet entry from workbook.xml
        $targetSheetEntryName = "xl/worksheets/sheet1.xml"
        $wbEntry = $zip.GetEntry("xl/workbook.xml")
        if ($wbEntry) {
            $stream = $wbEntry.Open()
            $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
            $wbXml = [xml]$reader.ReadToEnd()
            $reader.Close()
            $stream.Close()

            $sheets = $wbXml.workbook.sheets.sheet
            $matchedSheetIndex = 1
            if ($SheetName -and $sheets) {
                $idx = 1
                foreach ($s in $sheets) {
                    if ($s.name -eq $SheetName -or $s.name -like "*$SheetName*") {
                        $matchedSheetIndex = $idx
                        break
                    }
                    $idx++
                }
            }
            $targetSheetEntryName = "xl/worksheets/sheet$matchedSheetIndex.xml"
        }

        # Fallback if entry doesn't exist
        $sEntry = $zip.GetEntry($targetSheetEntryName)
        if (-not $sEntry) {
            $firstSheet = $zip.Entries | Where-Object { $_.FullName -like "xl/worksheets/sheet*.xml" } | Select-Object -First 1
            if ($firstSheet) { $sEntry = $firstSheet }
        }

        if (-not $sEntry) {
            throw "No worksheet found inside Excel archive."
        }

        $stream = $sEntry.Open()
        $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
        $sXml = [xml]$reader.ReadToEnd()
        $reader.Close()
        $stream.Close()

        $rows = $sXml.worksheet.sheetData.row
        $currentModule = "General"
        $testcases = @()

        foreach ($r in $rows) {
            $rowNum = [int]$r.r
            $cells = @{}
            foreach ($c in $r.c) {
                $colLetter = $c.r -replace '\d+'
                $val = ""
                if ($c.v) {
                    $raw = $c.v
                    if ($c.t -eq "s") {
                        $val = $sharedStrings[[int]$raw]
                    } else {
                        $val = $raw
                    }
                }
                $cells[$colLetter] = $val
            }

            $colA = if ($cells.ContainsKey("A")) { $cells["A"].Trim() } else { "" }
            $colB = if ($cells.ContainsKey("B")) { $cells["B"].Trim() } else { "" }

            if ($colB -match "PHAN HE|Phan he|PHÂN HỆ|Phân hệ|MODULE|Module") {
                $currentModule = $colB.Trim()
            } elseif ($colA -match "PHAN HE|Phan he|PHÂN HỆ|Phân hệ|MODULE|Module") {
                $currentModule = $colA.Trim()
            }

            if ($colA -match '^TC[-_]?\d+') {
                $testcases += [PSCustomObject]@{
                    Row = $rowNum
                    Module = $currentModule
                    ID = $colA
                    Name = if ($cells.ContainsKey("B")) { $cells["B"].Trim() } else { "" }
                    PreCondition = if ($cells.ContainsKey("C")) { $cells["C"].Trim() } else { "" }
                    Steps = if ($cells.ContainsKey("D")) { $cells["D"].Trim() } else { "" }
                    DataTest = if ($cells.ContainsKey("E")) { $cells["E"].Trim() } else { "" }
                    Expected = if ($cells.ContainsKey("F")) { $cells["F"].Trim() } else { "" }
                    Progress = if ($cells.ContainsKey("G")) { $cells["G"].Trim() } else { "" }
                    Status = if ($cells.ContainsKey("H")) { $cells["H"].Trim() } else { "" }
                    QC = if ($cells.ContainsKey("I")) { $cells["I"].Trim() } else { "" }
                }
            }
        }
        return $testcases
    } finally {
        $zip.Dispose()
    }
}

# Alias for backwards compatibility
function Read-EnterpriseSheet {
    param([string]$FilePath)
    return Read-ExcelSheet -FilePath $FilePath
}

# Stdio JSON-RPC Loop
$inputReader = [System.Console]::In
while (($line = $inputReader.ReadLine()) -ne $null) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $id = $null
    try {
        $req = $line | ConvertFrom-Json
        $id = $req.id
        $method = $req.method

        if ($method -eq "initialize") {
            $resp = @{
                jsonrpc = "2.0"
                id = $id
                result = @{
                    protocolVersion = "2024-11-05"
                    capabilities = @{ tools = @{} }
                    serverInfo = @{ name = "excel-qa-mcp-server"; version = "2.1.0" }
                }
            }
            [System.Console]::Out.WriteLine(($resp | ConvertTo-Json -Compress -Depth 10))
        } elseif ($method -eq "notifications/initialized") {
        } elseif ($method -eq "ping") {
            $resp = @{ jsonrpc = "2.0"; id = $id; result = @{} }
            [System.Console]::Out.WriteLine(($resp | ConvertTo-Json -Compress))
        } elseif ($method -eq "tools/list") {
            $resp = @{
                jsonrpc = "2.0"
                id = $id
                result = @{
                    tools = @(
                        @{
                            name = "read_excel_sheet"
                            description = "Extract test cases and matrix rows from an Excel worksheet."
                            inputSchema = @{
                                type = "object"
                                properties = @{
                                    file_path = @{ type = "string"; description = "Path to Excel file (.xlsx)" }
                                    sheet_name = @{ type = "string"; description = "Worksheet name (defaults to first sheet)" }
                                }
                            }
                        },
                        @{
                            name = "read_Enterprise_sheet"
                            description = "Compatibility alias for read_excel_sheet"
                            inputSchema = @{
                                type = "object"
                                properties = @{
                                    file_path = @{ type = "string"; description = "Path to Excel file (.xlsx)" }
                                }
                            }
                        }
                    )
                }
            }
            [System.Console]::Out.WriteLine(($resp | ConvertTo-Json -Compress -Depth 10))
        } elseif ($method -eq "tools/call") {
            $toolName = $req.params.name
            if ($toolName -eq "read_excel_sheet" -or $toolName -eq "read_Enterprise_sheet") {
                $fPath = $req.params.arguments.file_path
                $sName = if ($req.params.arguments.sheet_name) { $req.params.arguments.sheet_name } else { "" }
                $tcs = Read-ExcelSheet -FilePath $fPath -SheetName $sName
                $textResult = $tcs | ConvertTo-Json -Depth 5
                $resp = @{
                    jsonrpc = "2.0"
                    id = $id
                    result = @{
                        content = @(
                            @{ type = "text"; text = $textResult }
                        )
                    }
                }
                [System.Console]::Out.WriteLine(($resp | ConvertTo-Json -Compress -Depth 10))
            } else {
                $resp = @{
                    jsonrpc = "2.0"
                    id = $id
                    error = @{ code = -32601; message = "Tool not found: $toolName" }
                }
                [System.Console]::Out.WriteLine(($resp | ConvertTo-Json -Compress))
            }
        } else {
            if ($null -ne $id) {
                $resp = @{
                    jsonrpc = "2.0"
                    id = $id
                    error = @{ code = -32601; message = "Method not found: $method" }
                }
                [System.Console]::Out.WriteLine(($resp | ConvertTo-Json -Compress))
            }
        }
    } catch {
        $errMsg = $_.Exception.Message
        [System.Console]::Error.WriteLine("[MCP Excel Server Error] $errMsg")
        $errCode = if ($null -eq $id) { -32700 } else { -32603 }
        $resp = @{
            jsonrpc = "2.0"
            id = $id
            error = @{
                code = $errCode
                message = "MCP Server Exception: $errMsg"
            }
        }
        [System.Console]::Out.WriteLine(($resp | ConvertTo-Json -Compress))
    }
}
