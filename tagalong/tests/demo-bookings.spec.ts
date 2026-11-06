import {test,expect} from '@playwright/test';
test('chat makes the honest reservation demo discoverable without sending the draft',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.goto('/');await page.getByRole('link',{name:'Open Coastal weekend'}).click();
 await page.getByLabel('Message your group').fill('private unsent draft');
 await page.getByRole('button',{name:'Try demo restaurant booking'}).click();
 await expect(page.getByRole('tab',{name:'Demo bookings'})).toHaveAttribute('aria-selected','true');
 await expect(page.getByText('Demo reservation—no real booking or charge',{exact:true})).toBeVisible();
 await expect(page.getByText('Sign in to a shared plan to run the restaurant MCP demo.')).toBeVisible();
 await expect(page.getByRole('button',{name:'Confirm demo reservation',exact:true})).toHaveCount(0);
});
