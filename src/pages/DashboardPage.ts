import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for the OrangeHRM "Dashboard" module.
 * URL: /web/index.php/dashboard/index
 */
export class DashboardPage {
  readonly page: Page;

  // Header / top bar
  readonly pageHeader: Locator;
  readonly userDropdown: Locator;
  readonly logoutMenuItem: Locator;
  readonly upgradeButton: Locator;

  // Dashboard widgets
  readonly timeAtWorkWidget: Locator;
  readonly myActionsWidget: Locator;
  readonly quickLaunchWidget: Locator;
  readonly buzzLatestPostsWidget: Locator;
  readonly employeesOnLeaveTodayWidget: Locator;
  readonly employeeDistributionBySubUnitWidget: Locator;
  readonly employeeDistributionByLocationWidget: Locator;

  // Quick Launch actions
  readonly assignLeaveButton: Locator;
  readonly leaveListButton: Locator;
  readonly timesheetsButton: Locator;
  readonly applyLeaveButton: Locator;
  readonly myLeaveButton: Locator;
  readonly myTimesheetButton: Locator;

  constructor(page: Page) {
    this.page = page;

    this.pageHeader = page.getByRole('heading', { name: 'Dashboard', level: 6 });
    this.userDropdown = page.locator('.oxd-userdropdown-tab');
    this.logoutMenuItem = page.getByRole('menuitem', { name: 'Logout' });
    this.upgradeButton = page.getByRole('button', { name: 'Upgrade' });

    // Widgets are identified by their card title text.
    this.timeAtWorkWidget = page.locator('.oxd-grid-item', { hasText: 'Time at Work' });
    this.myActionsWidget = page.locator('.oxd-grid-item', { hasText: 'My Actions' });
    this.quickLaunchWidget = page.locator('.oxd-grid-item', { hasText: 'Quick Launch' });
    this.buzzLatestPostsWidget = page.locator('.oxd-grid-item', { hasText: 'Buzz Latest Posts' });
    this.employeesOnLeaveTodayWidget = page.locator('.oxd-grid-item', { hasText: 'Employees on Leave Today' });
    this.employeeDistributionBySubUnitWidget = page.locator('.oxd-grid-item', {
      hasText: 'Employee Distribution by Sub Unit',
    });
    this.employeeDistributionByLocationWidget = page.locator('.oxd-grid-item', {
      hasText: 'Employee Distribution by Location',
    });

    // Quick Launch buttons
    this.assignLeaveButton = page.getByRole('button', { name: 'Assign Leave' });
    this.leaveListButton = page.getByRole('button', { name: 'Leave List' });
    this.timesheetsButton = page.getByRole('button', { name: 'Timesheets' });
    this.applyLeaveButton = page.getByRole('button', { name: 'Apply Leave' });
    this.myLeaveButton = page.getByRole('button', { name: 'My Leave' });
    this.myTimesheetButton = page.getByRole('button', { name: 'My Timesheet' });
  }

  /** Navigate directly to the Dashboard module. */
  async goto(): Promise<void> {
    await this.page.goto('/web/index.php/dashboard/index');
    await this.waitForLoaded();
  }

  /** Wait until the Dashboard module has finished rendering. */
  async waitForLoaded(): Promise<void> {
    await expect(this.pageHeader).toBeVisible();
    await expect(this.quickLaunchWidget).toBeVisible();
  }

  /** Assert the Dashboard page header is displayed. */
  async expectLoaded(): Promise<void> {
    await expect(this.page).toHaveURL(/\/dashboard\/index/);
    await expect(this.pageHeader).toBeVisible();
  }

  /** Return all Quick Launch action labels rendered on the dashboard. */
  async getQuickLaunchLabels(): Promise<string[]> {
    return this.quickLaunchWidget
      .locator('button .oxd-text')
      .allInnerTexts();
  }

  /** Click a Quick Launch action by its visible label. */
  async clickQuickLaunch(label: string): Promise<void> {
    await this.quickLaunchWidget.getByRole('button', { name: label, exact: true }).click();
  }

  /** Open the user dropdown menu in the top bar. */
  async openUserMenu(): Promise<void> {
    await this.userDropdown.click();
    await expect(this.logoutMenuItem).toBeVisible();
  }

  /** Log out of the application via the top-bar user menu. */
  async logout(): Promise<void> {
    await this.openUserMenu();
    await this.logoutMenuItem.click();
    await expect(this.page).toHaveURL(/\/auth\/login/);
  }
}
