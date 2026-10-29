#!/usr/bin/env bash
# Triage Failures Script for Enterprise Automation
# Cross-platform: Compatible with macOS, Linux CI, and Windows Git Bash

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCREENSHOT_DIR="$WORKSPACE_DIR/Screenshots"
REPORTS_DIR="$WORKSPACE_DIR/Reports"

echo "=========================================================="
echo "  🔬 ENTERPRISE FAILURE AUTOPSY & TRIAGE SCANNER (CROSS-PLATFORM)"
echo "  Workspace: $WORKSPACE_DIR"
echo "=========================================================="

# 1. Quét báo cáo JUnit XML gần nhất
LATEST_JUNIT=$(find "$REPORTS_DIR" -type f -name "JUnit_Report.xml" 2>/dev/null | sort -r | head -n 1)

if [ -n "$LATEST_JUNIT" ]; then
    echo "📊 Báo cáo JUnit gần nhất: $(basename "$(dirname "$LATEST_JUNIT")")/JUnit_Report.xml"
    FAILED_JUNIT_TESTS=$(grep -B 1 '<failure' "$LATEST_JUNIT" 2>/dev/null | grep '<testcase' | sed -n 's/.*name="\([^"]*\)".*/\1/p')
    if [ -n "$FAILED_JUNIT_TESTS" ]; then
        echo "🚨 Các Test Cases báo FAILED trong JUnit XML:"
        echo "$FAILED_JUNIT_TESTS" | while read -r tc; do
            echo "   ❌ $tc"
        done
        echo "----------------------------------------------------------"
    else
        echo "✅ Không phát hiện ca thất bại nào trong JUnit XML gần nhất."
        echo "----------------------------------------------------------"
    fi
fi

# 2. Quét ảnh chụp FAILED_*.png
if [ ! -d "$SCREENSHOT_DIR" ]; then
    echo "ℹ️  Không tìm thấy thư mục Screenshots. Dự án đang sạch lỗi!"
    exit 0
fi

FAILED_COUNT=$(find "$SCREENSHOT_DIR" -maxdepth 1 -name "FAILED_*.png" 2>/dev/null | wc -l | tr -d ' ')

if [ "$FAILED_COUNT" -eq "0" ]; then
    echo "✅ Tuyệt vời! Không có ảnh lỗi nào trong $SCREENSHOT_DIR."
    exit 0
fi

echo "⚠️  Phát hiện $FAILED_COUNT ảnh lỗi kịch bản gần nhất:"
echo "----------------------------------------------------------"

# Hàm lấy thông tin file đa nền tảng (hỗ trợ Linux GNU stat, macOS BSD stat và fallback ls)
list_recent_screenshots() {
    if stat --version 2>&1 | grep -q "GNU"; then
        # Linux (GNU stat)
        find "$SCREENSHOT_DIR" -maxdepth 1 -name "FAILED_*.png" -type f -exec stat -c "%Y %y %n" {} + 2>/dev/null | \
            sort -rn | head -n 10 | awk '{print $1, $2, $3, $NF}'
    elif stat -f "%m" . >/dev/null 2>&1; then
        # macOS / BSD stat
        find "$SCREENSHOT_DIR" -maxdepth 1 -name "FAILED_*.png" -type f -exec stat -f "%m %Sm %N" -t "%Y-%m-%d %H:%M:%S" {} + 2>/dev/null | \
            sort -rn | head -n 10
    else
        # Fallback (POSIX ls)
        ls -lt "$SCREENSHOT_DIR"/FAILED_*.png 2>/dev/null | head -n 10 | awk '{print "0", $6, $7, $NF}'
    fi
}

list_recent_screenshots | while read -r epoch date time filepath; do
    filename=$(basename "$filepath")
    
    # Ánh xạ Page Class gợi ý dựa trên mã Test Case (Dynamic Pattern Matching)
    suggested_page="BasePage.groovy"
    if [[ "$filename" =~ TC-([0-9]+) ]]; then
        tc_num="${BASH_REMATCH[1]}"
        if [ "$tc_num" -ge 1 ] && [ "$tc_num" -le 7 ]; then
            suggested_page="TargetPlanPage.groovy"
        elif [ "$tc_num" -ge 8 ] && [ "$tc_num" -le 12 ]; then
            suggested_page="LoginPage.groovy"
        elif [ "$tc_num" -ge 13 ] && [ "$tc_num" -le 16 ]; then
            suggested_page="UserAdminPage.groovy"
        elif [ "$tc_num" -ge 17 ] && [ "$tc_num" -le 28 ]; then
            suggested_page="CommonCategoryPage.groovy"
        elif [ "$tc_num" -ge 29 ] && [ "$tc_num" -le 92 ]; then
            suggested_page="IndustryCategoryPage.groovy"
        elif [ "$tc_num" -ge 93 ] && [ "$tc_num" -le 122 ]; then
            suggested_page="PlanningPage.groovy"
        elif [ "$tc_num" -ge 123 ] && [ "$tc_num" -le 247 ]; then
            suggested_page="DataMiningPage.groovy"
        elif [ "$tc_num" -ge 248 ] && [ "$tc_num" -le 249 ]; then
            suggested_page="ReportPage.groovy"
        elif [ "$tc_num" -ge 250 ] && [ "$tc_num" -le 259 ]; then
            suggested_page="TokenMgmtPage.groovy"
        fi
    fi

    echo "📸 [$date $time] $filename"
    echo "   -> Đường dẫn ảnh : $filepath"
    echo "   -> Page Class cần vá : Keywords/pages/$suggested_page"
done

echo "----------------------------------------------------------"
echo "💡 Gợi ý AI: Dùng tool read_file mở ảnh hoặc dùng Playwright Live giữ nguyên browser để xác thực và vá Page Class."
