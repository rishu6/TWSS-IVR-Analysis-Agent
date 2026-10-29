import {test,expect} from '@playwright/test';
test.use({baseURL:'http://127.0.0.1:8003'});

test('each analytical tab restores its own filters and page size',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await page.getByRole('button',{name:'Enter demo workspace'}).click();
  const nav=page.getByRole('navigation',{name:'Main navigation'});
  const saved=new Map<string,string>();
  const tabs=[['Overview','Sales','ANSWERED'],['Live calls','Support',''],['Detailed call flow','Admissions','MISSED'],['Agent analytics','Sales','MISSED'],['Departments','Support','ANSWERED'],['LeadSquared insights','Admissions','ANSWERED']];
  for(const [name,department,status] of tabs){
    await nav.getByRole('link',{name,exact:true}).click();
    // A newly visited tab must not inherit the previous tab's selection.
    await expect(page.getByLabel('Department',{exact:true})).toHaveValue('');
    await expect(page.getByLabel('Search calls')).toHaveValue('');
    if(name!=='Detailed call flow'){
      await expect(page.getByLabel('Report from date')).toHaveValue('');
      await page.getByLabel('Report from date').fill('2026-10-27');
      await page.getByLabel('Report through date').fill('2026-10-27');
    }else{
      await page.getByLabel('Flow from date').fill('2026-10-27');
      await page.getByLabel('Flow through date').fill('2026-10-27');
      await page.getByRole('button',{name:'Apply date range',exact:true}).click();
    }
    await page.getByLabel('Department',{exact:true}).selectOption(department);
    if(name!=='Live calls')await page.getByLabel('Call status',{exact:true}).selectOption(status);
    await page.getByRole('button',{name:'Apply filters',exact:true}).click();
    await expect.poll(()=>new URL(page.url()).searchParams.get('department'),{message:name}).toBe(department);
    await page.getByLabel('Search calls').fill(name);
    await expect.poll(()=>new URL(page.url()).searchParams.get('q'),{message:name}).toBe(name);
    saved.set(name,new URL(page.url()).search);
  }
  for(const [name,department,status] of tabs){
    await nav.getByRole('link',{name,exact:true}).click();
    expect(new URL(page.url()).search).toBe(saved.get(name));
    await expect(page.getByLabel('Department',{exact:true})).toHaveValue(department);
    await expect(page.getByLabel('Search calls')).toHaveValue(name);
    if(name!=='Live calls')await expect(page.getByLabel('Call status',{exact:true})).toHaveValue(status);
  }
  await nav.getByRole('link',{name:'Overview',exact:true}).click();
  await page.getByRole('button',{name:'Clear filters',exact:true}).click();
  await nav.getByRole('link',{name:'Agent analytics',exact:true}).click();
  expect(new URL(page.url()).search).toBe(saved.get('Agent analytics'));
  await nav.getByRole('link',{name:'Detailed call flow',exact:true}).click();
  await page.getByLabel('Rows per page',{exact:true}).selectOption('50');
  await nav.getByRole('link',{name:'LeadSquared insights',exact:true}).click();
  await expect(page.getByLabel('Rows per page',{exact:true})).toHaveValue('10');
  await page.getByLabel('Rows per page',{exact:true}).selectOption('25');
  await nav.getByRole('link',{name:'Detailed call flow',exact:true}).click();
  await expect(page.getByLabel('Rows per page',{exact:true})).toHaveValue('50');
  await page.reload();
  await expect(page.getByLabel('Rows per page',{exact:true})).toHaveValue('50');
  expect(errors).toEqual([]);
});
