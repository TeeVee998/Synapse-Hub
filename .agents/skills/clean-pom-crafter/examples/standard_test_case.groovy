import com.enterprise.pages.BasePage
import com.enterprise.pages.LoginPage
import com.enterprise.pages.DataMiningPage
import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI

// Bước 1: Đảm bảo phiên đăng nhập hợp lệ
LoginPage.ensureLoggedIn()

// Bước 2: Điều hướng đến phân hệ mục tiêu
DataMiningPage.navigateToCumCongNghiep()

// Bước 3: Chuẩn bị dữ liệu kiểm thử duy nhất
String testCode = BasePage.uniqueCode("CCN_")
String testName = "CCN Thử Nghiệm " + testCode

// Bước 4: Thực thi tạo mới
DataMiningPage.createCluster(testCode, testName, "Hà Nội", "Đang hoạt động")

// Bước 5: Tìm kiếm 2 pha và xác thực theo Mã
DataMiningPage.searchRecord(testCode)
DataMiningPage.verifyRecordExists(testCode)

// Bước 6: Chỉnh sửa và xác thực cập nhật
String updatedName = testName + " [ĐÃ CẬP NHẬT]"
DataMiningPage.editRecord(testCode, updatedName)

// Bước 7: Dọn dẹp dữ liệu (Xóa & Verify Không còn tồn tại)
DataMiningPage.deleteRecord(testCode)
