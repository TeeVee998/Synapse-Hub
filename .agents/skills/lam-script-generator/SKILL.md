---
name: lam-script-generator
description: "Transform user stories and acceptance criteria into Clean POM automation scripts."
---

# LAM Script Generator — Large Action Model for Test Automation

Inspired by the **LaVague AI Web Agent & Large Action Model (LAM)** framework, this skill bridges the gap between natural language requirements (User Stories, Acceptance Criteria) and durable, deterministic automation code conforming to Clean POM Flat Architecture.

---

## 1. The Dual-Engine LAM Architecture

```mermaid
flowchart TD
    UserStory["<b>Natural Language User Story</b><br/>'Add new record with dynamic code and verify success'"] --> WorldModel["<b>1. World Model (Reasoning Engine)</b><br/>• Analyzes business goal<br/>• Decomposes into atomic user action sequence<br/>• Determines preconditions & expected assertions"]
    
    WorldModel --> ActionEngine["<b>2. Action Engine (Code Generator)</b><br/>• Queries Page Classes via Knowledge Graph<br/>• Maps action to existing methods: LoginPage.login(), TablePage.openAddModal()<br/>• Injects dynamic uniqueCode timestamp"]
    
    ActionEngine --> CodeGen["<b>3. Durable Clean POM Script (.groovy / .ts)</b><br/>• 100% Zero raw XPath in scripts<br/>• Infinite CI/CD replays with 0 LLM Tokens"]
```

1. **World Model (Reasoning Engine):**
   - Parses natural language requirements or QA/BA Acceptance Criteria.
   - Infers the step sequence: `Login` $\rightarrow$ `Navigate to Menu` $\rightarrow$ `Open Add Modal` $\rightarrow$ `Input Dynamic Data` $\rightarrow$ `Save & Assert Toast`.
2. **Action Engine (Code Generator):**
   - Instead of speculative coordinates, Action Engine queries the project Knowledge Graph to select existing Page Classes and standardized methods.
   - Generates clean, robust test scripts adhering strictly to Clean POM.
3. **Zero-Token Replayability:**
   - Once verified, the generated script is committed to the test suite on disk.
   - All subsequent CI/CD pipeline runs execute deterministically without consuming any LLM tokens.

---

## 2. Transformation Workflow: User Story to Clean POM

### Input (User Story):
```text
"Verify adding a new Industry record:
1. Login as system administrator.
2. Navigate to Industry Data menu.
3. Click Add New button.
4. Fill required fields with dynamic code 'IND_' and valid name.
5. Save and assert green success notification.
6. Verify the new record appears in the data table."
```

### Output (Clean POM Groovy Script):
```groovy
import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI
import internal.GlobalVariable as GlobalVariable
import pages.LoginPage
import pages.IndustryDataPage
import common.BasePage

// 1. Arrange & Preconditions
LoginPage.login(GlobalVariable.ADMIN_USER, GlobalVariable.ADMIN_PASS)
IndustryDataPage.navigate()

// 2. Dynamic Test Data Generation
String uniqueCode = BasePage.uniqueCode("IND_")
String entityName = "Automated Test Industry " + uniqueCode

// 3. Act
IndustryDataPage.clickAddNew()
IndustryDataPage.inputDetails(uniqueCode, entityName)
IndustryDataPage.clickSave()

// 4. Assert
IndustryDataPage.assertSuccessToast()
IndustryDataPage.searchAndVerifyRecord(uniqueCode, entityName)

// 5. Teardown Cleanup
IndustryDataPage.deleteRecordByCode(uniqueCode)
```

---

## 3. Mandatory Generation Constraints
- Zero raw XPaths, CSS selectors, or `findTestObject` in the generated script.
- Always generate dynamic identifiers with prefixes via `BasePage.uniqueCode()`.
- Always generate mandatory teardown cleanup for created entities.
