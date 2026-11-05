import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for the OrangeHRM Login page.
 * URL: https://opensource-demo.orangehrmlive.com/web/index.php/auth/login
 */
export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly loginHeading: Locator;
  readonly errorMessage: Locator;
  readonly dashboardHeading: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByRole('textbox', { name: 'Username' });
    this.passwordInput = page.getByRole('textbox', { name: 'Password' });
    this.loginButton = page.getByRole('button', { name: 'Login' });
    this.loginHeading = page.getByRole('heading', { name: 'Login' });
    this.errorMessage = page.locator('.oxd-alert-content-text');
    this.dashboardHeading = page.getByRole('heading', { name: 'Dashboard' });
  }

  /** Navigate to the login page. */
  async goto(): Promise<void> {
    await this.page.goto('/web/index.php/auth/login');
    await this.page.waitForLoadState('domcontentloaded');
    await expect(this.page).toHaveURL(/\/web\/index\.php\/auth\/login/);
    await expect(this.loginHeading).toBeVisible({ timeout: 15000 });
  }

  /** Fill credentials and submit the login form. */
  async login(username: string, password: string): Promise<void> {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  /** Assert that login succeeded and the dashboard is displayed. */
  async expectLoginSuccess(): Promise<void> {
    await expect(this.page).toHaveURL(/\/dashboard\/index/);
    await expect(this.dashboardHeading).toBeVisible();
  }

  /** Assert that login failed with the given error message. */
  async expectLoginError(message: string): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
    await expect(this.errorMessage).toHaveText(message);
  }
}
