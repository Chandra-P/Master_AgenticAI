import {test,expect} from '@playwright/test';

test.beforeEach(async({page})=>{await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));});

test('create a trip, chat with simulated AI, vote and review the live board',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Create a plan',exact:true}).first().click();
 await page.getByRole('button',{name:'Trip',exact:true}).click();
 await page.getByLabel('Plan name').fill('Autumn friends escape');
 await page.getByLabel('Start date').fill('2026-11-20');
 await page.getByLabel('End date').fill('2026-11-22');
 await page.getByLabel('Invite participants').fill('Maya, Sam');
 await page.getByRole('button',{name:'Create demo plan'}).click();
 await expect(page.getByRole('heading',{name:'Autumn friends escape',level:1})).toBeVisible();
 await page.getByLabel('Message your group').fill('@Tagalong suggest a relaxed weekend');
 await page.getByRole('button',{name:'Send message'}).click();
 await expect(page.getByText('Simulated assistant', {exact:true}).first()).toBeVisible();
 await page.getByRole('tab',{name:'Planning board'}).click();
 await expect(page.getByText('Relaxed pace', {exact:true}).first()).toBeVisible();
 await page.getByRole('tab',{name:'Polls'}).click();
 await page.getByRole('button',{name:/Nov 20/}).click();
 await expect(page.getByText('Your vote is saved. You can change it anytime.')).toBeVisible();
 await page.getByRole('tab',{name:'Planning board'}).click();
 await expect(page.getByText('Nov 20–22', {exact:true}).first()).toBeVisible();
 await page.reload();
 await expect(page.getByRole('heading',{name:'Autumn friends escape',level:1})).toBeVisible();
});

test('discover, add to itinerary, confirm preferences and navigate',async({page})=>{
 await page.goto('/');
 await page.getByRole('link',{name:'Open Coastal weekend'}).click();
 await page.getByRole('tab',{name:'Discover'}).click();
 await page.getByRole('button',{name:'Add Harbor & Pine to itinerary'}).click();
 await page.getByRole('tab',{name:'Itinerary'}).click();
 await expect(page.getByRole('heading',{name:'Harbor & Pine'})).toBeVisible();
 await expect(page.getByText('Not booked').first()).toBeVisible();
 await page.getByRole('tab',{name:'Planning board'}).click();
 await page.getByRole('button',{name:'Confirm Outdoor dining'}).click();
 await expect(page.getByText('Confirmed by you').first()).toBeVisible();
 if(!await page.getByRole('link',{name:'About Tagalong'}).isVisible()) await page.getByRole('button',{name:'Open menu'}).click();
 await page.getByRole('link',{name:'About Tagalong'}).click();
 await expect(page.getByRole('heading',{name:'Good plans. Great company.'})).toBeVisible();
});

test('reject empty plans and create a custom poll',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Create a plan',exact:true}).first().click();
 await page.getByRole('button',{name:'Create demo plan'}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.getByRole('button',{name:'Close'}).click();
 await page.getByRole('link',{name:'Open Coastal weekend'}).click();
 await page.getByRole('tab',{name:'Polls'}).click();
 await page.getByRole('button',{name:'Create poll',exact:true}).click();
 await page.getByLabel('Poll question').fill('Dinner time?');
 await page.getByLabel('Option 1').fill('6 pm');
 await page.getByLabel('Option 2').fill('7 pm');
 await page.getByRole('button',{name:'Publish demo poll'}).click();
 await expect(page.getByRole('heading',{name:'Dinner time?'})).toBeVisible();
 await page.getByRole('button',{name:/6 pm/}).click();
 await page.getByRole('button',{name:/7 pm/}).click();
 await expect(page.getByRole('button',{name:/7 pm/})).toContainText('1 vote');
 await expect(page.getByRole('button',{name:/6 pm/})).toContainText('0 votes');
});
