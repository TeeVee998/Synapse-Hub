package pages

class UserManagementPage extends BasePage {
    static final String USER_TABLE_ROW = "table#users tbody tr"

    static boolean verifyUserActive(String email) {
        return verifyElementPresent(uniqueLocator(USER_TABLE_ROW, email))
    }
}
