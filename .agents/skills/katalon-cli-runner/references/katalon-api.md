# Katalon Built-in Keywords API Reference

This document provides a reference for Katalon Studio's most commonly used built-in keywords.

## WebUI Keywords

Katalon's WebUI keywords are accessed via `com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords` (commonly imported as `WebUI`).

### Navigation Keywords

- `WebUI.openBrowser(url)` - Open a browser and navigate to URL
- `WebUI.navigateToUrl(url)` - Navigate to a URL in the current browser
- `WebUI.closeBrowser()` - Close the current browser
- `WebUI.back()` - Navigate back in browser history
- `WebUI.forward()` - Navigate forward in browser history
- `WebUI.refresh()` - Refresh the current page
- `WebUI.switchToWindowIndex(index)` - Switch to a browser window by index
- `WebUI.switchToWindowTitle(title)` - Switch to a browser window by title
- `WebUI.switchToWindowUrl(url)` - Switch to a browser window by URL

### Element Interaction Keywords

- `WebUI.click(testObject)` - Click on an element
- `WebUI.doubleClick(testObject)` - Double-click on an element
- `WebUI.rightClick(testObject)` - Right-click on an element
- `WebUI.setText(testObject, text)` - Set text for an input field
- `WebUI.sendKeys(testObject, text)` - Send keyboard input to an element
- `WebUI.clearText(testObject)` - Clear text from an input field
- `WebUI.selectOptionByValue(testObject, value, isRegex)` - Select dropdown option by value
- `WebUI.selectOptionByLabel(testObject, label, isRegex)` - Select dropdown option by label
- `WebUI.selectOptionByIndex(testObject, index)` - Select dropdown option by index
- `WebUI.check(testObject)` - Check a checkbox
- `WebUI.uncheck(testObject)` - Uncheck a checkbox
- `WebUI.uploadFile(testObject, filePath)` - Upload a file to a file input

### Wait Keywords

- `WebUI.waitForElementPresent(testObject, timeoutInSeconds)` - Wait for element to be present in DOM
- `WebUI.waitForElementVisible(testObject, timeoutInSeconds)` - Wait for element to be visible
- `WebUI.waitForElementClickable(testObject, timeoutInSeconds)` - Wait for element to be clickable
- `WebUI.waitForElementNotPresent(testObject, timeoutInSeconds)` - Wait for element to not be present
- `WebUI.waitForElementNotVisible(testObject, timeoutInSeconds)` - Wait for element to not be visible
- `WebUI.waitForPageLoad(timeoutInSeconds)` - Wait for page to fully load
- `WebUI.delay(timeInSeconds)` - Pause execution for specified seconds

### Verification Keywords

- `WebUI.verifyElementPresent(testObject, timeoutInSeconds)` - Verify element is present
- `WebUI.verifyElementVisible(testObject)` - Verify element is visible
- `WebUI.verifyElementClickable(testObject)` - Verify element is clickable
- `WebUI.verifyElementNotPresent(testObject, timeoutInSeconds)` - Verify element is not present
- `WebUI.verifyElementText(testObject, expectedText)` - Verify element contains expected text
- `WebUI.verifyTextPresent(text, isRegex)` - Verify text is present on the page
- `WebUI.verifyElementAttributeValue(testObject, attribute, expectedValue, timeoutInSeconds)` - Verify element attribute value

### Get Keywords

- `WebUI.getText(testObject)` - Get text content of an element
- `WebUI.getAttribute(testObject, attribute)` - Get attribute value of an element
- `WebUI.getCSSValue(testObject, propertyName)` - Get CSS property value
- `WebUI.getUrl()` - Get current page URL
- `WebUI.getWindowTitle()` - Get current window title

### Screenshot Keywords

- `WebUI.takeScreenshot(filePath)` - Take a screenshot and save to file
- `WebUI.takeFullPageScreenshot(filePath)` - Take a full-page screenshot

## Mobile Keywords

Katalon's Mobile keywords are accessed via `com.kms.katalon.core.mobile.keyword.MobileBuiltInKeywords` (commonly imported as `Mobile`).

### Common Mobile Keywords

- `Mobile.startApplication(appPath)` - Start a mobile application
- `Mobile.closeApplication()` - Close the current application
- `Mobile.tap(testObject, timeout)` - Tap on a mobile element
- `Mobile.setText(testObject, text, timeout)` - Set text in a mobile input
- `Mobile.getText(testObject, timeout)` - Get text from a mobile element
- `Mobile.verifyElementExist(testObject, timeout)` - Verify mobile element exists
- `Mobile.scrollToText(text)` - Scroll until specified text is visible
- `Mobile.swipe(startX, startY, endX, endY)` - Perform a swipe gesture

## Web Service (API) Keywords

Katalon's Web Service keywords are accessed via `com.kms.katalon.core.webservice.keyword.WSBuiltInKeywords` (commonly imported as `WS`).

### API Keywords

- `WS.sendRequest(requestObject)` - Send a web service request
- `WS.verifyResponseStatusCode(response, statusCode)` - Verify HTTP response status code
- `WS.verifyElementPropertyValue(response, locator, expectedValue)` - Verify JSON/XML element value
- `WS.getElementPropertyValue(response, locator)` - Get value from JSON/XML response
- `WS.verifyElementsCount(response, locator, expectedCount)` - Verify count of elements in response

## Utility Keywords

### Checkpoint Keywords

- `findCheckpoint(checkpointName)` - Find a checkpoint by name

### Test Case Keywords

- `findTestCase(testCasePath)` - Find a test case by path
- `WebUI.callTestCase(testCase, variables)` - Call another test case

### Test Data Keywords

- `findTestData(testDataName)` - Find test data by name

### Object Repository Keywords

- `findTestObject(objectPath)` - Find a test object from Object Repository
- `findTestObject(objectPath, variables)` - Find a test object with variable bindings

## Global Variables

Access global variables defined in profiles using `internal.GlobalVariable`:

```groovy
import internal.GlobalVariable

// Access a global variable
String url = GlobalVariable.baseUrl
String username = GlobalVariable.username
int timeout = GlobalVariable.waitTimeout
```

## Failure Handling

Control how test execution handles failures using `com.kms.katalon.core.model.FailureHandling`:

- `FailureHandling.STOP_ON_FAILURE` - Stop test execution on failure (default)
- `FailureHandling.CONTINUE_ON_FAILURE` - Continue execution even if step fails
- `FailureHandling.OPTIONAL` - Mark step as optional, continue regardless of result

Example:
```groovy
WebUI.verifyElementPresent(findTestObject('optionalElement'), 5, FailureHandling.OPTIONAL)
```

## Annotations for Custom Keywords

When creating custom keywords, use the `@Keyword` annotation:

```groovy
import com.kms.katalon.core.annotation.Keyword

class MyKeywords {
    @Keyword
    def myCustomKeyword(String param) {
        // Implementation
    }
}
```
