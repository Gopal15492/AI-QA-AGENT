import { test, expect } from '@playwright/test';
import { LoginPage } from '../src/pages/LoginPage';
import { DashboardPage } from '../src/pages/DashboardPage';

/**
 * Dashboard module - widget content tests.
 * Module under test: Dashboard (present in the OrangeHRM app).
 *
 * Credentials are read from the environment so they are never committed:
 *   OHRM_USERNAME / OHRM_PASSWORD
 */
const USERNAME = process.env.OHRM_USERNAME ?? 'Admin';
const PASSWORD = process.env.OHRM_PASSWORD ?? '';

test.describe('Dashboard - Widgets', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);

    await loginPage.goto();
    await loginPage.login(USERNAME, PASSWORD);
    await dashboardPage.waitForLoaded();
  });

  test('Quick Launch widget exposes all expected actions', async () => {
    const labels = await dashboardPage.getQuickLaunchLabels();

    expect(labels).toEqual(
      expect.arrayContaining([
        'Assign Leave',
        'Leave List',
        'Timesheets',
        'Apply Leave',
        'My Leave',
        'My Timesheet',
      ]),
    );
  });

  test('Time at Work widget displays the punch status', async () => {
    await expect(dashboardPage.timeAtWorkWidget).toContainText(/Punched In|Punched Out/);
  });

  test('Employee Distribution by Sub Unit widget lists the sub units', async () => {
    await expect(dashboardPage.employeeDistributionBySubUnitWidget).toBeVisible();
    await expect(dashboardPage.employeeDistributionBySubUnitWidget).toContainText('Engineering');
  });

  test('Employees on Leave Today widget renders its content area', async () => {
    await expect(dashboardPage.employeesOnLeaveTodayWidget).toBeVisible();
    await expect(dashboardPage.employeesOnLeaveTodayWidget).toContainText(/Employees on Leave Today/);
  });
});
