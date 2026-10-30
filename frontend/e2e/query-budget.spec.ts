import {test,expect} from '@playwright/test';
test.use({baseURL:'http://127.0.0.1:8003'});
test('internal screens fetch only their visible reports and do not start demo invalidations',async({page})=>{
 await page.request.post('/api/v1/auth/login',{headers:{'x-csrf-protection':'1'},data:{role:'Manager',password:'synthetic-demo-only'}});
 await page.route('**/api/v1/auth/me',async route=>{
  const response=await route.fetch();const body=await response.json();
  await route.fulfill({response,json:{...body,demo:false,display_name:'Synthetic traffic test'}});
 });
 const paths:string[]=[];page.on('request',r=>paths.push(new URL(r.url()).pathname));
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Analysis dashboard',exact:true})).toBeVisible();
 await expect(page.locator('.dash-kpi')).toHaveCount(6);
 expect(paths).toContain('/api/v1/metrics/overview');
 expect(paths).not.toContain('/api/v1/calls');expect(paths).not.toContain('/api/v1/live-token');
 const start=paths.length;
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'LeadSquared insights',exact:true}).click();
 await expect(page.locator('.crm-summary .kpi')).toHaveCount(6);
 expect(paths.slice(start)).toContain('/api/v1/reports/leadsquared');
 expect(paths.slice(start)).not.toContain('/api/v1/metrics/overview');
 expect(paths.slice(start)).not.toContain('/api/v1/calls');
 expect(paths).not.toContain('/api/v1/live-token');
});
