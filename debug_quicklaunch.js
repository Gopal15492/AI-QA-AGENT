const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://opensource-demo.orangehrmlive.com/web/index.php/auth/login');
  await page.getByRole('textbox', { name: 'Username' }).fill('Admin');
  await page.getByRole('textbox', { name: 'Password' }).fill('admin123');
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForSelector('.oxd-grid-item', { timeout: 20000 });

  const q = page.locator('.oxd-grid-item', { hasText: 'Quick Launch' }).first();
  console.log('Q count:', await q.count());
  const text = await q.innerText();
  console.log('Q innerText:\n' + text.slice(0, 2000));

  const buttons = await q.locator('button').allTextContents();
  console.log('BUTTONS:', JSON.stringify(buttons, null, 2));

  await browser.close();
})();
