import { test, expect } from '@playwright/test';
import { LoginPage } from '../src/pages/LoginPage';
import { DashboardPage } from '../src/pages/DashboardPage';

/**
 * Dashboard module - overview tests.
 * Module under test: Dashboard (present in the OrangeHRM app).
 *
 * Credentials are read from the environment so they are never committed:
 *   OHRM_USERNAME / OHRM_PASSWORD
 */
const USERNAME = process.env.OHRM_USERNAME ?? 'Admin';
const PASSWORD = process.env.OHRM_PASSWORD ?? '';

test.describe('Dashboard - Overview', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);

    await loginPage.goto();
    await loginPage.login(USERNAME, PASSWORD);
  });

  test('displays the Dashboard module header and URL after login', async () => {
    await dashboardPage.expectLoaded();
    await expect(dashboardPage.pageHeader).toHaveText('Dashboard');
  });

  test('renders all expected dashboard widgets', async () => {
    await dashboardPage.waitForLoaded();

    await expect(dashboardPage.timeAtWorkWidget).toBeVisible();
    await expect(dashboardPage.myActionsWidget).toBeVisible();
    await expect(dashboardPage.quickLaunchWidget).toBeVisible();
    await expect(dashboardPage.buzzLatestPostsWidget).toBeVisible();
    await expect(dashboardPage.employeesOnLeaveTodayWidget).toBeVisible();
    await expect(dashboardPage.employeeDistributionBySubUnitWidget).toBeVisible();
    await expect(dashboardPage.employeeDistributionByLocationWidget).toBeVisible();
  });

  test('shows the logged-in user in the top bar with a working user menu', async () => {
    await dashboardPage.openUserMenu();
    await expect(dashboardPage.logoutMenuItem).toBeVisible();
  });
});
