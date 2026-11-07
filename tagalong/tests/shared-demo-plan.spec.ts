import {test,expect} from '@playwright/test';

test('an account saves and reopens the four-friend fictional story with sources and itinerary',async({page})=>{
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-alice',refresh_token:'refresh-alice',token_type:'bearer',expires_in:3600,user:{id:'alice',email:'alice@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByLabel('Email address',{exact:true}).fill('alice@example.test');await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await page.goto('/');await page.getByRole('button',{name:'Add four-friends demo plan',exact:true}).click();await expect(page.getByRole('heading',{name:'DEMO · Four friends, one Austin weekend.',exact:true})).toBeVisible();
 const url=page.url(),base='/api/backend/v1/plans/'+new URL(url).pathname.split('/').pop();
 const plan=await(await page.request.get(base,{headers:{Authorization:'Bearer test-alice'}})).json();expect(plan.members).toHaveLength(1);expect(plan.itinerary).toHaveLength(7);
 expect(plan.messages.filter((message:{simulation?:boolean})=>message.simulation)).toHaveLength(40);
 await page.getByRole('tab',{name:'Chat',exact:true}).click();
 await expect(page.getByText('Four friends planning together',{exact:true})).toBeVisible();
 await expect(page.locator('.chat-messages').getByText('Fictional friend',{exact:true})).toHaveCount(plan.messages.filter((message:{simulation?:boolean;assistant?:boolean})=>message.simulation&&!message.assistant).length);
 for(const name of ['Alex','Maya','Sam','Jordan'])await expect(page.locator('.chat-messages .message-byline > strong').filter({hasText:name}).first()).toBeVisible();
 await page.getByRole('button',{name:'See their options and votes',exact:true}).click();
 const choices=page.getByRole('region',{name:'Four friends’ planning decisions'});await expect(choices.getByRole('article')).toHaveCount(5);await expect(choices.getByText('First responses · disagreement remains',{exact:true})).toHaveCount(5);await expect(choices.getByText('Final responses · fictional agreement',{exact:true})).toHaveCount(5);
 await page.screenshot({path:test.info().outputPath('friends-options-and-votes.png')});
 expect((await page.request.get(base+'/demo-story',{headers:{Authorization:'Bearer test-bob'}})).status()).toBe(404);
 await page.getByRole('button',{name:'View demo story',exact:true}).click();const dialog=page.getByRole('dialog');await expect(dialog.getByText(/Alex, Maya, Sam and Jordan are fictional adults/)).toBeVisible();await expect(dialog.locator('[aria-label="Fictional story cast"]').getByText('Fictional friend',{exact:true})).toHaveCount(4);
 for(let index=0;index<6;index++)await dialog.getByRole('button',{name:'Next step',exact:true}).click();await expect(dialog.getByText('Step 7 of 7',{exact:true})).toBeVisible();await expect(dialog.getByRole('region',{name:'Final fictional itinerary'}).getByRole('heading',{name:'The story’s final day-by-day itinerary',exact:true})).toBeVisible();
 await expect(dialog.locator('.demo-story-choices a[href="https://www.lonestarcourt.com/"]').filter({hasText:'Official reference website'})).toHaveText('Official reference website');
 await dialog.getByRole('button',{name:'Run live RAG and AI check',exact:true}).click();await expect(dialog.getByRole('heading',{name:'Latest live AI reply in this plan',exact:true})).toBeVisible();await expect(dialog.getByText(/Live citation:/).first()).toBeVisible();await expect(dialog.getByText('Step 7 of 7',{exact:true})).toBeVisible();
 await dialog.getByRole('button',{name:'Replay from start',exact:true}).click();await expect(dialog.getByText('Step 1 of 7',{exact:true})).toBeVisible();await dialog.getByRole('button',{name:'Close',exact:true}).click();await page.reload();await page.getByRole('button',{name:'View demo story',exact:true}).click();await expect(dialog.getByText('Step 1 of 7',{exact:true})).toBeVisible();
 await page.screenshot({path:test.info().outputPath('saved-four-friends-demo.png')});
});
