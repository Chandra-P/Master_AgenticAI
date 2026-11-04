import { test, expect } from '@playwright/test';
import path from 'node:path';

test('Texas tax projection, strategy, review confirmation and evidence',async({page})=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/#Tax%20Planning');
 await expect(page.getByRole('heading',{name:'Your paycheck. A clearer tax picture.'})).toBeVisible();
 await expect(page.getByText('$2,137.60',{exact:true})).toBeVisible();
 await expect(page.getByText('$14,020.00',{exact:true}).first()).toBeVisible();
 await page.getByRole('button',{name:'Compare tax strategy'}).click();
 await expect(page.getByText('$220.00',{exact:true})).toBeVisible();
 await expect(page.getByText('$780.00',{exact:true})).toBeVisible();
 await page.getByLabel('Extra traditional 401(k) ($)').fill('300');
 await expect(page.getByText('$220.00',{exact:true})).toHaveCount(0);
 await page.getByLabel('Extra traditional 401(k) ($)').fill('0');
 await page.getByLabel('Extra eligible payroll HSA ($)').fill('100');
 await page.getByRole('button',{name:'Compare tax strategy'}).click();
 await expect(page.getByText('$88.00',{exact:true})).toBeVisible();
 await expect(page.getByText('$369.40',{exact:true})).toBeVisible();
 await expect(page.getByText('$281.40',{exact:true})).toBeVisible();
 await page.getByLabel('Upload paystub for review').setInputFiles(path.join(process.cwd(),'public/sample-paystub.txt'));
 await expect(page.getByRole('heading',{name:'Review extracted facts before using them'})).toBeVisible();
 const confirm=page.getByRole('button',{name:'Confirm reviewed paystub',exact:true});
 await expect(confirm).toBeDisabled();
 const option=page.locator('.tax-correction-label option').filter({hasText:'Alex Morgan'}).first();
 const existing=await option.getAttribute('value');
 expect(existing).toBeTruthy();
 await page.locator('.tax-correction-label select').selectOption(existing!);
 const approval=page.getByRole('checkbox',{name:/I reviewed all fields/});
 await approval.check();
 await page.getByLabel('Gross pay current',{exact:true}).fill('4000.00');
 // The field is unchanged, so check a real edit and restore it; each edit needs new approval.
 await page.getByLabel('Gross pay current',{exact:true}).fill('4000.01');
 await expect(confirm).toBeDisabled();
 await page.getByLabel('Gross pay current',{exact:true}).fill('4000.00');
 await approval.check();
 await confirm.click();
 await expect(page.getByText(/Paystub facts confirmed/)).toBeVisible();
 await expect(page.getByText('$2,137.60',{exact:true})).toBeVisible();
 await page.getByText('Bracket calculation & official rule sources',{exact:true}).click();
 await expect(page.getByRole('link',{name:/IRS Revenue Procedure 2025-32/})).toBeVisible();
 await page.screenshot({path:'../artifacts/tax-planning-desktop.png',fullPage:true});
 await page.getByRole('navigation').getByRole('button',{name:'FinPilot Copilot',exact:true}).click();
 await page.getByRole('textbox',{name:'Ask FinPilot'}).fill('What if Alex increases traditional 401(k) by $250 per paycheck?');
 await page.getByRole('button',{name:'Send question'}).click();
 await expect(page.getByText('$220.00',{exact:true})).toBeVisible();
 await page.getByText('Agent & tool trace',{exact:false}).click();
 await expect(page.getByText('simulate_tax_strategy',{exact:true})).toBeVisible();
 expect(errors).toEqual([]);
});

test('Texas tax page stays usable on mobile',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/#Tax%20Planning');
 await expect(page.getByText('$2,137.60',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.screenshot({path:'../artifacts/tax-planning-mobile.png',fullPage:true});
});
