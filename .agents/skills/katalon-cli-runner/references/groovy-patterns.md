# Groovy Patterns for Katalon Studio

This document provides common Groovy patterns and best practices for Katalon Studio custom keywords and test scripts.

## Custom Keyword Structure

### Basic Custom Keyword Class

```groovy
package com.enterprise.keywords

import com.kms.katalon.core.annotation.Keyword
import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI
import internal.GlobalVariable

class LoginKeywords {

    @Keyword
    def login(String username, String password) {
        WebUI.setText(findTestObject('Page_Login/input_Username'), username)
        WebUI.setEncryptedText(findTestObject('Page_Login/input_Password'), password)
        WebUI.click(findTestObject('Page_Login/btn_Login'))
        WebUI.waitForPageLoad(GlobalVariable.timeout)
    }

    @Keyword
    def loginWithGlobalVariables() {
        login(GlobalVariable.username, GlobalVariable.password)
    }

    @Keyword
    def verifyLoginSuccess() {
        WebUI.verifyElementPresent(findTestObject('Page_Dashboard/header_Welcome'),
            GlobalVariable.timeout)
    }
}
```

### Static Keywords

When keywords don't need instance state, make them static:

```groovy
package com.enterprise.utils

import com.kms.katalon.core.annotation.Keyword
import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI

class NavigationUtils {

    @Keyword
    static def navigateToPage(String pageName) {
        String url = "${GlobalVariable.baseUrl}/${pageName}"
        WebUI.navigateToUrl(url)
    }

    @Keyword
    static def refreshUntilElementVisible(TestObject element, int maxAttempts = 5) {
        int attempts = 0
        while (attempts < maxAttempts) {
            if (WebUI.verifyElementVisible(element, FailureHandling.OPTIONAL)) {
                return true
            }
            WebUI.refresh()
            attempts++
        }
        return false
    }
}
```

## Common Patterns

### Wait and Retry Pattern

```groovy
@Keyword
def waitAndRetry(TestObject element, int maxAttempts = 3, int delaySeconds = 2) {
    for (int i = 0; i < maxAttempts; i++) {
        try {
            WebUI.waitForElementPresent(element, delaySeconds)
            return true
        } catch (Exception e) {
            if (i == maxAttempts - 1) {
                throw e
            }
            WebUI.delay(delaySeconds)
        }
    }
    return false
}
```

### Conditional Element Interaction

```groovy
@Keyword
def clickIfPresent(TestObject element, int timeout = 5) {
    if (WebUI.verifyElementPresent(element, timeout, FailureHandling.OPTIONAL)) {
        WebUI.click(element)
        return true
    }
    return false
}

@Keyword
def closePopupIfExists(TestObject closeButton) {
    if (WebUI.verifyElementVisible(closeButton, FailureHandling.OPTIONAL)) {
        WebUI.click(closeButton)
        WebUI.delay(1)
    }
}
```

### Dynamic Object Creation

```groovy
@Keyword
def clickDynamicElement(String xpath) {
    TestObject dynamicObject = new TestObject()
    dynamicObject.addProperty('xpath', ConditionType.EQUALS, xpath)
    WebUI.click(dynamicObject)
}

@Keyword
def findElementByText(String tagName, String text) {
    String xpath = "//${tagName}[contains(text(), '${text}')]"
    TestObject element = new TestObject()
    element.addProperty('xpath', ConditionType.EQUALS, xpath)
    return element
}
```

### Data-Driven Helpers

```groovy
@Keyword
def executeWithTestData(String testDataName, Closure action) {
    TestData data = findTestData(testDataName)
    int rowCount = data.getRowNumbers()

    for (int i = 1; i <= rowCount; i++) {
        def row = [:]
        data.getColumnNames().each { col ->
            row[col] = data.getValue(col, i)
        }
        action(row)
    }
}
```

### Page Object Pattern

```groovy
package com.enterprise.pages

import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI
import internal.GlobalVariable

class LoginPage {

    def open() {
        WebUI.navigateToUrl(GlobalVariable.loginUrl)
        return this
    }

    def login(String username, String password) {
        // Implementation
    }
}
```

### Error Handling and Logging

```groovy
import com.kms.katalon.core.util.KeywordUtil

@Keyword
def performActionWithErrorHandling(Closure action) {
    try {
        action()
        KeywordUtil.markPassed("Action completed successfully")
    } catch (Exception e) {
        KeywordUtil.logInfo("Error occurred: ${e.message}")
        WebUI.takeScreenshot()
        KeywordUtil.markFailed("Action failed: ${e.message}")
        throw e
    }
}

@Keyword
def safeClick(TestObject element, String elementName = "Element") {
    try {
        WebUI.waitForElementClickable(element, 10)
        WebUI.click(element)
        KeywordUtil.logInfo("Clicked on ${elementName}")
    } catch (Exception e) {
        KeywordUtil.markWarning("Could not click ${elementName}: ${e.message}")
        WebUI.takeScreenshot()
    }
}
```

### Best Practices

1. **Use Descriptive Names**: Use clear, readable keyword names.
2. **Handle Timeouts Gracefully**: Always set explicit wait timeouts rather than hard sleeps.
3. **Parameterize Magic Numbers**: Define constants for retries and timeouts.
4. **Failure Handling**: Use `FailureHandling.STOP_ON_FAILURE` for critical steps, `OPTIONAL` for transient dialogs.
