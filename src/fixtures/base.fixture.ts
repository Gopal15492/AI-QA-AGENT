import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

/**
 * Custom fixtures for the OrangeHRM test suite.
 * Extend the base Playwright test with page objects so specs stay clean.
 */
type Fixtures = {
  loginPage: LoginPage;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await use(loginPage);
  },
});

export { expect };
