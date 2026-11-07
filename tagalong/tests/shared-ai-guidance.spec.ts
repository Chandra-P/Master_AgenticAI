import {test,expect} from '@playwright/test';

test('AI explains its draft, proposes interests and guides the next step without casting votes',async({page})=>{
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-alice',refresh_token:'refresh-alice',token_type:'bearer',expires_in:3600,user:{id:'alice',email:'alice@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByLabel('Email address',{exact:true}).fill('alice@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await page.route('**/api/backend/v1/plans/generate',async route=>{const response=await route.fetch();const result=await response.json();result.draft.suggested_interests=['Food','Music'];result.draft.interest_reason='A starting mix for your food and music weekend; your group can change it.';await route.fulfill({response,json:result});});
 await page.goto('/');const prompt=page.getByLabel('Describe your plan');await prompt.fill('Food and music weekend in Austin with four friends');
 const promptBox=await prompt.boundingBox(),groupBox=await page.getByLabel('Plan with a group',{exact:true}).boundingBox();expect(promptBox!.y).toBeLessThan(groupBox!.y);
 await page.getByRole('button',{name:'Start Planning',exact:true}).click();const draft=page.getByRole('region',{name:'Review AI plan draft'});
 await expect(draft.getByRole('complementary',{name:'What AI prepared'})).toBeVisible();await expect(draft.getByText('Next, what dates should I search?',{exact:true})).toBeVisible();
 await expect(draft.getByRole('button',{name:'Food',exact:true})).toHaveAttribute('aria-pressed','true');await expect(draft.getByRole('button',{name:'Music',exact:true})).toHaveAttribute('aria-pressed','true');
 await draft.getByLabel('Working start date',{exact:true}).fill('2027-05-14');await draft.getByLabel('Working end date',{exact:true}).fill('2027-05-16');await draft.getByRole('button',{name:'Suggest things to do',exact:true}).click();await expect(draft.getByRole('article',{name:'Synthetic Music Night suggestion'})).toBeVisible();
 await draft.getByRole('button',{name:'Create reviewed plan',exact:true}).click();const guide=page.getByRole('region',{name:'AI planning guide'});await expect(guide).toBeVisible();
 await guide.getByRole('button',{name:'Ask AI for the next step',exact:true}).click();await expect(page.getByRole('tab',{name:'Chat',exact:true})).toHaveAttribute('aria-selected','true');await expect(page.locator('.assistant-message .message-bubble').last()).toContainText('Evidence considered');
 const cityGuide=page.getByRole('complementary',{name:'AI city planning guide'});await cityGuide.getByRole('button',{name:'Find ideas for me',exact:true}).click();await expect(cityGuide.getByRole('article',{name:'Synthetic vegetarian restaurant suggestion'})).toBeVisible();
 const id=new URL(page.url()).pathname.split('/').pop();const snapshot=await(await page.request.get('/api/backend/v1/plans/'+id+'/decisions',{headers:{Authorization:'Bearer test-alice'}})).json();expect(snapshot.decisions.every((decision:{ballots:unknown[];confirmation:unknown})=>!decision.ballots.length&&!decision.confirmation)).toBeTruthy();
 await page.screenshot({path:test.info().outputPath('guided-ai-next-step.png')});
});
