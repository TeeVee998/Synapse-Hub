package com.enterprise.pages

import org.openqa.selenium.By
import org.openqa.selenium.JavascriptExecutor
import org.openqa.selenium.Keys
import org.openqa.selenium.WebDriver
import org.openqa.selenium.WebElement
import com.kms.katalon.core.webui.driver.DriverFactory

/**
 * Enterprise Clean POM common methods reusable across Page Classes.
 * Kế thừa trực tiếp từ BasePage.
 */
class PomPatterns extends BasePage {

    /**
     * Hành vi tìm kiếm 2 pha: Bấm Search -> Điền từ khóa -> Enter -> Chờ bảng cập nhật
     */
    public static void searchRecord(String keyword) {
        WebDriver driver = DriverFactory.getWebDriver()
        List<WebElement> inputs = driver.findElements(By.cssSelector("input.p-inputtext[placeholder*='Tìm kiếm'], input[placeholder*='tên'], input[placeholder*='mã']"))
        if (inputs.isEmpty() || !inputs.get(0).isDisplayed()) {
            WebElement searchToggle = findElement(By.cssSelector("button.p-button-icon-only[icon*='search'], button[title*='Tìm kiếm']"))
            searchToggle.click()
            waitForElementVisible(By.cssSelector("input.p-inputtext[placeholder*='Tìm kiếm'], input[placeholder*='tên'], input[placeholder*='mã']"), 5)
        }
        WebElement input = findElement(By.cssSelector("input.p-inputtext[placeholder*='Tìm kiếm'], input[placeholder*='tên'], input[placeholder*='mã']"))
        jsSetInput(input, keyword)
        input.sendKeys(Keys.ENTER)
        waitForAngular(5)
        waitForElementVisible(By.cssSelector("p-table table tbody tr"), 5)
    }

    /**
     * Chỉnh sửa bản ghi tại dòng đầu tiên và xác thực theo tên mới
     */
    public static void editRecord(String oldKeyword, String newName) {
        searchRecord(oldKeyword)
        WebElement editBtn = findElement(By.cssSelector("p-table tbody tr:first-child button[icon*='pencil'], p-table tbody tr:first-child button[icon*='edit']"))
        clickElement(editBtn)
        waitForElementVisible(By.cssSelector("input[formcontrolname='name'], input[name='name']"), 5)

        WebElement nameInput = findElement(By.cssSelector("input[formcontrolname='name'], input[name='name']"))
        jsSetInput(nameInput, newName)

        WebElement saveBtn = findElement(By.xpath("//button[@title='Xác nhận' or contains(.,'Lưu') or contains(.,'Xác nhận')]"))
        clickElement(saveBtn)
        waitForAngular(5)

        searchRecord(newName)
        WebElement firstRow = findElement(By.cssSelector("p-table tbody tr:first-child"))
        assert firstRow.getText().contains(newName) : "Lỗi: Bản ghi chưa cập nhật tên mới!"
    }

    /**
     * Xóa bản ghi tại dòng đầu tiên và xác nhận p-confirmdialog
     */
    public static void deleteRecord(String keyword) {
        WebDriver driver = DriverFactory.getWebDriver()
        searchRecord(keyword)
        WebElement deleteBtn = findElement(By.cssSelector("p-table tbody tr:first-child button.p-button-danger, p-table tbody tr:first-child button[icon*='trash']"))
        clickElement(deleteBtn)
        waitForElementVisible(By.xpath("//div[contains(@class,'p-dialog-footer') or contains(@class,'p-confirm-dialog')]//button[contains(@class,'p-confirm-dialog-accept') or contains(.,'Xóa') or contains(.,'Đồng ý') or contains(.,'Xác nhận')]"), 5)

        WebElement confirmBtn = findElement(By.xpath("//div[contains(@class,'p-dialog-footer') or contains(@class,'p-confirm-dialog')]//button[contains(@class,'p-confirm-dialog-accept') or contains(.,'Xóa') or contains(.,'Đồng ý') or contains(.,'Xác nhận')]"))
        clickElement(confirmBtn)
        waitForAngular(5)

        verifyRecordNotExists(keyword)
    }

    /**
     * Điền ngày vào p-calendar an toàn với Angular
     */
    public static void setCalendarDate(WebElement element, String dateStr) {
        WebDriver driver = DriverFactory.getWebDriver()
        JavascriptExecutor js = (JavascriptExecutor) driver
        js.executeScript("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
        """, element, dateStr)
    }

    /**
     * Chọn nhiều lựa chọn trong p-multiselect
     */
    public static void selectMultiOptions(WebElement multiSelectEl, List<String> optionTexts) {
        clickElement(multiSelectEl)
        waitForElementVisible(By.cssSelector(".p-multiselect-panel"), 5)
        WebDriver driver = DriverFactory.getWebDriver()
        for (String opt : optionTexts) {
            WebElement item = driver.findElement(By.xpath("//li[contains(@class, 'p-multiselect-item') and contains(., '" + opt + "')]"))
            clickElement(item)
        }
        WebElement closeBtn = driver.findElement(By.cssSelector(".p-multiselect-close"))
        if (closeBtn != null && closeBtn.isDisplayed()) {
            closeBtn.click()
        }
    }

    /**
     * Kiểm tra bản ghi tồn tại trong bảng p-table
     */
    public static void verifyRecordExists(String keyword) {
        WebDriver driver = DriverFactory.getWebDriver()
        List<WebElement> rows = driver.findElements(By.cssSelector("p-table table tbody tr"))
        assert !rows.isEmpty() : "Lỗi: Bảng không có dữ liệu nào!"
        String firstRowText = rows.get(0).getText()
        assert firstRowText.contains(keyword) : "Lỗi: Không tìm thấy từ khóa '${keyword}' trong hàng đầu tiên!"
    }

    /**
     * Kiểm tra bản ghi đã bị xóa hoàn toàn khỏi bảng
     */
    public static void verifyRecordNotExists(String keyword) {
        WebDriver driver = DriverFactory.getWebDriver()
        searchRecord(keyword)
        List<WebElement> rows = driver.findElements(By.cssSelector("p-table table tbody tr"))
        if (rows.isEmpty()) return
        String firstRowText = rows.get(0).getText()
        assert !firstRowText.contains(keyword) || firstRowText.contains("Không có dữ liệu") : "Lỗi: Bản ghi '${keyword}' vẫn còn tồn tại trong bảng!"
    }

    /**
     * Gán giá trị an toàn kích hoạt Angular Change Detection
     */
    public static void jsSetInput(WebElement element, String value) {
        WebDriver driver = DriverFactory.getWebDriver()
        JavascriptExecutor js = (JavascriptExecutor) driver
        js.executeScript("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, element, value)
    }
}
