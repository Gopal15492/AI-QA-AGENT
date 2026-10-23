import { test } from '@playwright/test';
import { LoginPage } from '../src/pages/LoginPage';

const USERNAME =
  process.env.OHRM_USERNAME ?? process.env.ORANGEHRM_USERNAME ?? 'Admin';
const PASSWORD =
  process.env.OHRM_PASSWORD ?? process.env.ORANGEHRM_PASSWORD ?? 'admin123';

test.describe('Login', () => {
  test('logs in with valid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(USERNAME, PASSWORD);
    await loginPage.expectLoginSuccess();
  });

  test('shows an error for invalid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(USERNAME, 'invalid-password');
    await loginPage.expectLoginError('Invalid credentials');
  });
});
