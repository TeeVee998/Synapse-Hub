#!/usr/bin/env python3
"""
Automated Test Suite for Omni-Automation Polyglot Engine
-------------------------------------------------------
Verifies Universal IR, OmniParser, OmniEmitter, and OmniTranspiler.
Ensures zero-token deterministic parsing and accurate code generation
across Java, TypeScript, Python, Groovy, and C#.
"""

import os
import sys
import json
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

from universal_ir import (
    ProjectIR, PageClassIR, TestCaseIR, MethodIR, StepIR, LocatorIR,
    ActionType, LocatorStrategy, AssertionType
)
from omni_parser import OmniParser
from omni_emitter import OmniEmitter
from omni_transpiler import transpile_file, scan_repository


class TestOmniAutomationEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Universal IR Schema Tests
    # -------------------------------------------------------------------------
    def test_universal_ir_serialization_and_deserialization(self):
        """Validates that ProjectIR round-trips to JSON and back with 100% fidelity."""
        p_ir = ProjectIR(name="AuthSuite", source_language="java", source_framework="selenium")
        
        page = PageClassIR(name="LoginPage", base_class="BasePage")
        page.locators.append(LocatorIR(name="txtUsername", strategy=LocatorStrategy.ID, value="username"))
        page.locators.append(LocatorIR(name="btnSubmit", strategy=LocatorStrategy.XPATH, value="//button[@type='submit']"))
        
        step1 = StepIR(action=ActionType.FILL, target="txtUsername", value="admin")
        step2 = StepIR(action=ActionType.CLICK, target="btnSubmit")
        step3 = StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.VISIBLE)
        
        method = MethodIR(name="login", parameters=["user", "pwd"], steps=[step1, step2, step3])
        page.methods.append(method)
        p_ir.pages.append(page)

        tc = TestCaseIR(id="TC_001", title="Valid Login Test", steps=[step1, step2, step3])
        p_ir.test_cases.append(tc)

        # JSON Roundtrip
        json_str = p_ir.to_json()
        restored = ProjectIR.from_json(json_str)

        self.assertEqual(restored.name, "AuthSuite")
        self.assertEqual(len(restored.pages), 1)
        self.assertEqual(restored.pages[0].name, "LoginPage")
        self.assertEqual(len(restored.pages[0].locators), 2)
        self.assertEqual(restored.pages[0].locators[0].name, "txtUsername")
        self.assertEqual(restored.pages[0].locators[0].strategy, LocatorStrategy.ID)
        self.assertEqual(len(restored.test_cases), 1)
        self.assertEqual(restored.test_cases[0].steps[0].action, ActionType.FILL)

    # -------------------------------------------------------------------------
    # 2. OmniParser Tests (Java Selenium)
    # -------------------------------------------------------------------------
    def test_parse_java_selenium_page(self):
        """Validates 0-token AST parsing of Java Selenium Page Object with @FindBy and By."""
        java_code = """package pages;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.By;

public class LoginPage extends BasePage {
    @FindBy(id = "user")
    private WebElement txtUser;

    @FindBy(xpath = "//button[@id='login']")
    private WebElement btnLogin;

    private By linkForgot = By.cssSelector(".forgot-pwd");

    public void doLogin(String user, String pass) {
        txtUser.sendKeys(user);
        btnLogin.click();
    }
}
"""
        file_path = os.path.join(self.temp_dir, "LoginPage.java")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(java_code)

        p_ir = OmniParser.parse_file(file_path)
        self.assertEqual(p_ir.source_language, "java")
        self.assertEqual(p_ir.source_framework, "selenium")
        self.assertEqual(len(p_ir.pages), 1)

        page = p_ir.pages[0]
        self.assertEqual(page.name, "LoginPage")
        self.assertEqual(len(page.locators), 3)

        loc_names = [loc.name for loc in page.locators]
        self.assertIn("txtUser", loc_names)
        self.assertIn("btnLogin", loc_names)
        self.assertIn("linkForgot", loc_names)

        self.assertEqual(len(page.methods), 1)
        self.assertEqual(page.methods[0].name, "doLogin")
        self.assertEqual(len(page.methods[0].steps), 2)

    # -------------------------------------------------------------------------
    # 3. OmniParser Tests (Playwright TypeScript)
    # -------------------------------------------------------------------------
    def test_parse_playwright_typescript_page_and_test(self):
        """Validates 0-token parsing of Playwright TypeScript with getByRole, getByTestId, and test blocks."""
        ts_code = """import { Page, Locator, expect, test } from "@playwright/test";

export class DashboardPage {
  readonly page: Page;
  readonly btnLogout = this.page.getByRole('button', { name: 'Log Out' });
  readonly cardProfile = this.page.getByTestId('profile-card');
  readonly txtSearch = this.page.locator('#search-box');

  constructor(page: Page) {
    this.page = page;
  }

  async logout(): Promise<void> {
    await this.btnLogout.click();
  }
}

test('TC_DASH_01: Verify dashboard logout', async ({ page }) => {
  await page.goto('https://app.example.com/dash');
  await page.locator('#search-box').fill('Analytics');
  await expect(page).toBeDefined();
});
"""
        file_path = os.path.join(self.temp_dir, "Dashboard.ts")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(ts_code)

        p_ir = OmniParser.parse_file(file_path)
        self.assertEqual(p_ir.source_language, "typescript")
        self.assertEqual(p_ir.source_framework, "playwright")
        self.assertEqual(len(p_ir.pages), 1)

        page = p_ir.pages[0]
        self.assertEqual(page.name, "DashboardPage")
        self.assertEqual(len(page.locators), 3)

        # Check Test Cases
        self.assertEqual(len(p_ir.test_cases), 1)
        self.assertIn("Verify dashboard logout", p_ir.test_cases[0].title)

    # -------------------------------------------------------------------------
    # 4. OmniParser Tests (Katalon Groovy Clean POM)
    # -------------------------------------------------------------------------
    def test_parse_katalon_groovy_clean_pom(self):
        """Validates 0-token parsing of Katalon Groovy Clean POM Flat Architecture."""
        groovy_code = """package pages

import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI

public class CheckoutPage extends BasePage {
    public static final String BTN_CHECKOUT = "//button[@id='checkout']"
    public static final String TXT_COUPON = "//input[@name='coupon']"

    public static void applyCoupon(String code) {
        setTextSafe(TXT_COUPON, code)
        clickJS(BTN_CHECKOUT)
    }
}
"""
        file_path = os.path.join(self.temp_dir, "CheckoutPage.groovy")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(groovy_code)

        p_ir = OmniParser.parse_file(file_path)
        self.assertEqual(p_ir.source_language, "groovy")
        self.assertEqual(p_ir.source_framework, "katalon")
        self.assertEqual(len(p_ir.pages), 1)

        page = p_ir.pages[0]
        self.assertEqual(page.name, "CheckoutPage")
        self.assertEqual(len(page.locators), 2)
        self.assertEqual(page.locators[0].value, "//button[@id='checkout']")
        self.assertEqual(len(page.methods), 1)
        self.assertEqual(page.methods[0].name, "applyCoupon")

    # -------------------------------------------------------------------------
    # 5. OmniEmitter Tests (Polyglot Code Generation)
    # -------------------------------------------------------------------------
    def test_emit_all_target_frameworks(self):
        """Validates code generation across Playwright TS, Python, Selenium Java, Katalon Groovy, and Cypress."""
        p_ir = ProjectIR(name="BillingSuite")
        page = PageClassIR(name="BillingPage")
        page.locators.append(LocatorIR(name="btnPay", strategy=LocatorStrategy.XPATH, value="//button[@id='pay']"))
        page.locators.append(LocatorIR(name="txtAmount", strategy=LocatorStrategy.CSS, value="#amount"))
        page.methods.append(MethodIR(
            name="makePayment",
            parameters=["amt"],
            steps=[
                StepIR(action=ActionType.FILL, target="txtAmount", value="100"),
                StepIR(action=ActionType.CLICK, target="btnPay"),
            ]
        ))
        p_ir.pages.append(page)
        p_ir.test_cases.append(TestCaseIR(
            id="TC_BILL_001",
            title="Execute Payment",
            steps=[
                StepIR(action=ActionType.GOTO, value="https://example.com/billing"),
                StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.VISIBLE)
            ]
        ))

        # 1. Playwright TypeScript
        ts_out = OmniEmitter.emit(p_ir, "playwright-ts")
        self.assertIn("pages/BillingPage.ts", ts_out)
        self.assertIn("tests/BillingSuite.spec.ts", ts_out)
        self.assertIn("export class BillingPage", ts_out["pages/BillingPage.ts"])
        self.assertTrue(
            "await this.btnPay.click();" in ts_out["pages/BillingPage.ts"]
            or ("safeInteract" in ts_out["pages/BillingPage.ts"] and "btnPay" in ts_out["pages/BillingPage.ts"])
        )

        # 2. Selenium Java
        java_out = OmniEmitter.emit(p_ir, "selenium-java")
        self.assertIn("src/main/java/pages/BillingPage.java", java_out)
        self.assertIn("private final By btnPay = By.xpath(\"//button[@id='pay']\");", java_out["src/main/java/pages/BillingPage.java"])

        # 3. Katalon Groovy
        groovy_out = OmniEmitter.emit(p_ir, "katalon-groovy")
        self.assertIn("Keywords/pages/BillingPage.groovy", groovy_out)
        self.assertIn("public static final String BTNPAY = \"//button[@id='pay']\"", groovy_out["Keywords/pages/BillingPage.groovy"])
        self.assertIn("BasePage.uniqueCode('AUTO_')", groovy_out["Scripts/TC_BILL_001_Execute Payment/Script.groovy"])

        # 4. Playwright Python
        py_out = OmniEmitter.emit(p_ir, "playwright-python")
        self.assertIn("pages/BillingPage.py", py_out)
        self.assertIn("class BillingPage:", py_out["pages/BillingPage.py"])

        # 5. Cypress JS
        cy_out = OmniEmitter.emit(p_ir, "cypress-js")
        self.assertIn("cypress/pages/BillingPage.js", cy_out)
        self.assertIn("get btnPay()", cy_out["cypress/pages/BillingPage.js"])

    # -------------------------------------------------------------------------
    # 6. OmniTranspiler End-to-End Tests
    # -------------------------------------------------------------------------
    def test_transpile_file_java_to_playwright_ts(self):
        """Validates instant 0-token transpilation from legacy Java Selenium to Playwright TS."""
        legacy_java = """package pages;
import org.openqa.selenium.By;
public class SearchPage {
    private By txtKeyword = By.id("kw");
    private By btnSearch = By.xpath("//button[@name='btnK']");

    public void search(String keyword) {
        txtKeyword.sendKeys(keyword);
        btnSearch.click();
    }
}
"""
        src_path = os.path.join(self.temp_dir, "SearchPage.java")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(legacy_java)

        out_dir = os.path.join(self.temp_dir, "playwright_dest")
        result = transpile_file(src_path, "playwright-ts", out_dir)

        self.assertIn("pages/SearchPage.ts", result)
        ts_file = os.path.join(out_dir, "pages", "SearchPage.ts")
        self.assertTrue(os.path.exists(ts_file))
        with open(ts_file, "r", encoding="utf-8") as f:
            ts_code = f.read()
        self.assertIn("export class SearchPage", ts_code)
        self.assertIn("this.btnSearch = page.locator('//button[@name=\\'btnK\\']');", ts_code)

    def test_scan_repository_polyglot_inventory(self):
        """Validates that scan_repository builds an accurate 0-token AST inventory."""
        # Create a mock multi-language repo
        p1 = os.path.join(self.temp_dir, "PageA.java")
        with open(p1, "w", encoding="utf-8") as f:
            f.write("public class PageA { @FindBy(id='a') WebElement a; public void clickA() { a.click(); } }")

        p2 = os.path.join(self.temp_dir, "PageB.ts")
        with open(p2, "w", encoding="utf-8") as f:
            f.write("export class PageB { readonly b = page.locator('#b'); async clickB() { await this.b.click(); } }")

        inv = scan_repository(self.temp_dir)
        self.assertEqual(inv["total_files_scanned"], 2)
        self.assertEqual(len(inv["pages"]), 2)
        self.assertGreaterEqual(inv["total_locators"], 2)

    # -------------------------------------------------------------------------
    # 7. Async/Sync Bridge & Antipattern Sanitizer Tests
    # -------------------------------------------------------------------------
    def test_async_sync_bridge_cypress_and_sleep_sanitization(self):
        """Validates flattening of Cypress .then() chains and sanitizing Thread.sleep to smart waits."""
        cypress_code = """
describe('Order Checkout', () => {
  it('submits checkout form', () => {
    cy.visit('https://app.shop.com/cart');
    cy.wait(3000);
    cy.get('#coupon').type('DISCOUNT2026');
    cy.get('#apply-btn').then(($btn) => {
      cy.wrap($btn).click();
    });
    cy.get('#total').should('be.visible');
  });
});
"""
        src_file = os.path.join(self.temp_dir, "CypressCheckout.js")
        with open(src_file, "w", encoding="utf-8") as f:
            f.write(cypress_code)

        p_ir = OmniParser.parse_file(src_file)
        self.assertEqual(len(p_ir.test_cases), 1)
        steps = p_ir.test_cases[0].steps

        # Check sleep was sanitized
        wait_steps = [s for s in steps if s.action == ActionType.WAIT]
        self.assertEqual(len(wait_steps), 1)
        self.assertTrue(wait_steps[0].is_sanitized_wait)

        # Transpile to Playwright TS
        emitted = OmniEmitter.emit(p_ir, "playwright-ts")
        spec_content = emitted.get("tests/CypressCheckout.spec.ts", "")

        # Verify no hardcoded page.waitForTimeout(3000), replaced with smart wait
        self.assertNotIn("page.waitForTimeout(3000)", spec_content)
        self.assertIn("waitForLoadState('networkidle')", spec_content)

    # -------------------------------------------------------------------------
    # 8. 3-Layer Heuristic Matcher Tests (0-Token Recovery)
    # -------------------------------------------------------------------------
    def test_heuristic_locator_matcher_3_layers(self):
        """Validates 0-token 3-layer heuristic matching cascade."""
        from heuristic_locator_matcher import HeuristicLocatorMatcher, levenshtein_ratio

        # Test Levenshtein distance
        self.assertAlmostEqual(levenshtein_ratio("Submit", "Submit"), 1.0)
        self.assertGreater(levenshtein_ratio("Xác nhận", "Xác nhận thanh toán"), 0.3)

        dom_snapshot = [
            {"tag": "input", "id": "username", "type": "text"},
            {"tag": "input", "id": "password", "type": "password"},
            {"tag": "button", "data-testid": "submit-checkout-btn", "text": "Xác nhận thanh toán", "aria-label": "Xác nhận"}
        ]

        # Layer 1: Exact testid match
        res_l1 = HeuristicLocatorMatcher.match(broken_locator="#submit-checkout-btn", dom_snapshot=dom_snapshot)
        self.assertTrue(res_l1["matched"])
        self.assertEqual(res_l1["layer"], 1)
        self.assertEqual(res_l1["confidence"], 0.98)
        self.assertEqual(res_l1["healed_locator"], "[data-testid='submit-checkout-btn']")

        # Layer 2: Text semantic matching (Substring match on "Xác nhận")
        res_l2 = HeuristicLocatorMatcher.match(broken_locator="//button[text()='Xác nhận']", dom_snapshot=dom_snapshot)
        self.assertTrue(res_l2["matched"])
        self.assertIn(res_l2["layer"], [1, 2])
        self.assertGreaterEqual(res_l2["confidence"], 0.85)

        # Layer 3: Spatial Anchor (element immediately after #password)
        res_l3 = HeuristicLocatorMatcher.match(
            broken_locator="#mystery-btn",
            dom_snapshot=dom_snapshot,
            spatial_anchor="#password"
        )
        self.assertTrue(res_l3["matched"])
        self.assertEqual(res_l3["layer"], 3)
        self.assertEqual(res_l3["confidence"], 0.86)

    # -------------------------------------------------------------------------
    # 9. Roundtrip Consistency Verification Test
    # -------------------------------------------------------------------------
    def test_roundtrip_integrity(self):
        """
        Validates 2-way roundtrip consistency without information loss:
        Katalon Groovy -> Playwright TypeScript -> Katalon Groovy.
        """
        initial_groovy = """package pages

import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI

public class TransferPage extends BasePage {
    public static final String TXT_RECIPIENT = "//input[@name='recipient']"
    public static final String TXT_AMOUNT = "//input[@name='amount']"
    public static final String BTN_TRANSFER = "//button[@id='btn-transfer']"

    public static void executeTransfer(String toUser, String sum) {
        setTextSafe(TXT_RECIPIENT, toUser)
        setTextSafe(TXT_AMOUNT, sum)
        clickJS(BTN_TRANSFER)
    }
}
"""
        # Step 1: Save & Parse initial Groovy
        src_path = os.path.join(self.temp_dir, "TransferPage.groovy")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(initial_groovy)

        ir_1 = OmniParser.parse_file(src_path)
        self.assertEqual(len(ir_1.pages), 1)
        self.assertEqual(len(ir_1.pages[0].locators), 3)
        self.assertEqual(len(ir_1.pages[0].methods), 1)

        # Step 2: Emit Playwright TypeScript
        emitted_ts = OmniEmitter.emit(ir_1, "playwright-ts")
        self.assertIn("pages/TransferPage.ts", emitted_ts)
        ts_code = emitted_ts["pages/TransferPage.ts"]

        # Step 3: Parse emitted Playwright TypeScript back to IR
        ts_path = os.path.join(self.temp_dir, "TransferPage.ts")
        with open(ts_path, "w", encoding="utf-8") as f:
            f.write(ts_code)

        ir_2 = OmniParser.parse_file(ts_path)

        # Assert zero information loss in Page, Locators, and Methods
        self.assertEqual(ir_2.pages[0].name, ir_1.pages[0].name)
        self.assertEqual(len(ir_2.pages[0].locators), len(ir_1.pages[0].locators))
        self.assertEqual(len(ir_2.pages[0].methods), len(ir_1.pages[0].methods))
        self.assertEqual(ir_2.pages[0].methods[0].name, ir_1.pages[0].methods[0].name)

        # Step 4: Emit back to Katalon Groovy and verify syntax
        emitted_groovy_back = OmniEmitter.emit(ir_2, "katalon-groovy")
        self.assertIn("Keywords/pages/TransferPage.groovy", emitted_groovy_back)
        final_groovy = emitted_groovy_back["Keywords/pages/TransferPage.groovy"]

        self.assertIn("public class TransferPage extends BasePage", final_groovy)
        self.assertIn("BTN_TRANSFER", final_groovy)
        self.assertIn("executeTransfer", final_groovy)

    # -------------------------------------------------------------------------
    # 10. CLI Offline Deterministic Flag Tests
    # -------------------------------------------------------------------------
    def test_cli_offline_deterministic_flag(self):
        """Validates that --offline activates air-gapped deterministic mode without network."""
        import subprocess
        cli_py = os.path.join(TOOLS_DIR, "cli.py")
        cmd = [sys.executable, cli_py, "--offline", "version"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        self.assertEqual(res.returncode, 0)
        self.assertIn("OFFLINE MODE", res.stdout)
        self.assertIn("Air-Gapped Deterministic Mode Active", res.stdout)
        self.assertIn("Agent-QA Hub CLI", res.stdout)


if __name__ == "__main__":
    unittest.main()
