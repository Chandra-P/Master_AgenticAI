import { test, expect } from '@playwright/test';

test('financial intelligence demo',async({page})=>{
 await page.goto('/');
 await expect(page.getByText('$60,000',{exact:true})).toBeVisible();
 const nav=page.getByRole('navigation',{name:'Main navigation'});
 await nav.getByRole('button',{name:'FinPilot Copilot',exact:true}).click();
 await page.getByRole('button',{name:'How much did I spend last month?',exact:true}).click();
 await expect(page.getByText('$6,000.00',{exact:true})).toBeVisible();
 const input=page.getByRole('textbox',{name:'Ask FinPilot'});
 await input.fill('What APR is listed in my current auto-loan offer?');
 await page.getByRole('button',{name:'Send question'}).click();
 await expect(page.getByText('6.49%',{exact:true})).toBeVisible();
 await input.fill('Can I afford the $50,000 car in my current loan offer?');
 await page.getByRole('button',{name:'Send question'}).click();
 await expect(page.getByRole('heading',{name:'Higher down payment',exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Lower down payment',exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Postpone purchase',exact:true})).toBeVisible();
 await nav.getByRole('button',{name:'Scenarios',exact:true}).click();
 await page.getByRole('button',{name:'Run deterministic simulation'}).click();
 await expect(page.getByText('$3,400.00',{exact:true})).toBeVisible();
 await nav.getByRole('button',{name:'Evaluation Lab',exact:true}).click();
 await page.getByRole('button',{name:'Run evaluation suite'}).click();
 await expect(page.locator('.evaluation-case')).toHaveCount(59);
 await expect(page.locator('.evaluation-case .bad')).toHaveCount(0);
});

test('mobile navigation and constraint approval',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/');
 await page.getByRole('button',{name:'Open navigation'}).click();
 await page.getByRole('navigation').getByRole('button',{name:'Settings',exact:true}).click();
 await expect(page.getByRole('button',{name:'Confirm & save constraints'})).toBeDisabled();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
