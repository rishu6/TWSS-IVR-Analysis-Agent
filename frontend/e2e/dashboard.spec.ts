import { test, expect } from '@playwright/test';

test('manager explores a four-agent call, CRM duplicates and exports', async ({ page }) => {
  const errors:string[]=[];
  page.on('pageerror', error=>errors.push(error.message));
  await page.goto('/');
  await page.getByRole('button', {name:'Enter demo workspace'}).click();
  await expect(page.getByRole('heading', {name:'Analysis dashboard'})).toBeVisible();
  await expect(page.getByText('3 answered / 8 inbound')).toBeVisible();
  await page.screenshot({path:test.info().outputPath('overview.png'),fullPage:true});
  await page.getByRole('button', {name:'Explore journey'}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('heading', {name:'+12025550101'})).toBeVisible();
  await expect(page.getByRole('dialog').getByText('Dev Patel', {exact:true}).first()).toBeVisible();
  await expect(page.getByRole('dialog').getByText('no answer', {exact:true})).toHaveCount(6); // timeline + leg outcomes
  await page.getByRole('button', {name:'Close call details'}).click();
  await page.getByRole('link', {name:'Call explorer',exact:true}).click();
  await page.getByRole('textbox', {name:'Search calls'}).fill('demo-missed');
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await page.getByRole('button', {name:'View demo-missed'}).click();
  await page.getByRole('button', {name:/LeadSquared/}).click();
  await expect(page.getByRole('dialog').locator('.lead-card')).toHaveCount(2);
  await expect(page.getByText('Multiple records match this number. No lead has been selected automatically.')).toBeVisible();
  await page.keyboard.press('Escape');
  await page.getByRole('button', {name:'Clear filters'}).click();
  await page.getByRole('link', {name:'Exports',exact:true}).click();
  const downloadPromise=page.waitForEvent('download');
  await page.getByRole('button', {name:'Download CSV'}).click();
  expect((await downloadPromise).suggestedFilename()).toBe('synthetic-calls.csv');
  expect(errors).toEqual([]);
});

test('viewer gets masked data, role restrictions and usable mobile layout', async ({ page }) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  await page.getByLabel('Demo role').selectOption('Viewer');
  await page.getByRole('button', {name:'Enter demo workspace'}).click();
  await page.getByRole('link', {name:'Call explorer',exact:true}).click();
  await expect(page.locator('tbody')).toBeVisible();
  await expect(page.locator('tbody')).not.toContainText('+1202555');
  const layout = await page.evaluate(()=>({width:document.documentElement.scrollWidth, viewport:window.innerWidth,
    overflow:[...document.querySelectorAll('*')].filter(e=>!e.closest('.table-wrap') && e.getBoundingClientRect().right>window.innerWidth)
      .map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right})).slice(0,12)}));
  expect(layout.width,JSON.stringify(layout)).toBeLessThanOrEqual(layout.viewport);
  await page.getByRole('link', {name:'Admin',exact:true}).click();
  await expect(page.getByText('Admin access required. Your current role is Viewer.')).toBeVisible();
  await page.getByRole('link', {name:'Exports',exact:true}).click();
  await expect(page.getByRole('button',{name:'Download CSV'})).toBeDisabled();
});
