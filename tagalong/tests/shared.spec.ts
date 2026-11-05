import {test,expect,type Page,type BrowserContext} from '@playwright/test';

async function login(page:Page,name:'alice'|'bob',role:'member'|'admin'='member'){
 const config=await (await page.request.get('/api/config')).json();
 expect(config.supabaseUrl).toBe('https://tagalong-test.supabase.co');
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');
 await page.getByRole('radio',{name:role==='admin'?'Admin':'Member',exact:true}).check();
 await page.getByLabel('Email address').fill(name+'@example.test');
 await page.getByLabel('Password',{exact:true}).fill('test-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await expect(page.getByText('Current role: '+(role==='admin'?'Admin':'Member'),{exact:true})).toBeVisible();
}

test('natural-language generation creates a reviewed plan and proactively summarizes it',async({page})=>{
 const title='Reviewed proactive weekend '+crypto.randomUUID().slice(0,8);
 await login(page,'alice');await page.goto('/');
 await expect(page.getByRole('heading',{name:'Good company starts here.',exact:true})).toBeVisible();
 await page.getByLabel('Describe your plan').fill('Weekend trip for four friends near Austin under $350 per person');
 await page.getByRole('button',{name:'Generate Plan',exact:true}).click();
 const review=page.getByRole('region',{name:'Review AI plan draft'});
 await expect(review).toBeVisible();
 await expect(review.getByLabel('Confirmed start date')).toHaveValue('');
 await review.getByLabel('Generated plan name').fill(title);
 await review.getByLabel('Confirmed start date').fill('2027-05-14');await review.getByLabel('Confirmed end date').fill('2027-05-16');
 await review.getByRole('button',{name:'Create reviewed plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:title+'.',exact:true,level:1})).toBeVisible();
 const coordination=page.getByRole('region',{name:'Plan coordination'});
 await expect(coordination.getByText('Waiting for votes',{exact:true})).toBeVisible();
 await expect(coordination).toContainText('The group is planning '+title+'.',{timeout:20000});
 await expect(page.getByText('Planning idea: Weekend trip for four friends near Austin under $350 per person',{exact:true})).toBeVisible();
 await page.goto('/');await expect(page.getByRole('heading',{name:'Continue Planning',exact:true})).toBeVisible();
 await expect(page.locator('.continue-card').filter({hasText:title})).toBeVisible();
});

test('live discovery shows a clickable external source link',async({page})=>{
 await login(page,'alice');
 await page.context().route('https://places.example.test/restaurant',route=>route.fulfill({contentType:'text/html',body:'<h1>Synthetic restaurant source</h1>'}));
 await page.goto('/discover');await page.getByLabel('Destination',{exact:true}).fill('San Francisco');await page.getByLabel('What are you looking for?').fill('vegetarian dinner');
 await page.getByRole('button',{name:'Search places',exact:true}).click();
 const link=page.getByRole('link',{name:'Explore Synthetic vegetarian restaurant',exact:true});
 await expect(link).toHaveAttribute('href','https://places.example.test/restaurant');
 await expect(link).toHaveAttribute('rel','noopener noreferrer');
 const opened=page.waitForEvent('popup');await link.click();const source=await opened;
 await expect(source.getByRole('heading',{name:'Synthetic restaurant source'})).toBeVisible();await source.close();
});

test('owner can transfer a shared plan and the new owner can delete it after confirmation',async({page:alice,browser})=>{
 await login(alice,'alice');
 const context=await browser.newContext();const bob=await context.newPage();
 try{
 await login(bob,'bob');
 const title='Lifecycle review '+crypto.randomUUID().slice(0,8);
 const plan=await alice.evaluate(async title=>{const r=await fetch('/api/backend/v1/plans',{method:'POST',headers:{Authorization:'Bearer test-alice','Content-Type':'application/json'},body:JSON.stringify({title,kind:'outing',start:'2026-12-12',end:'2026-12-12'})});return r.json();},title);
 await alice.goto('/plans/'+plan.id);await alice.getByRole('button',{name:'Add member',exact:true}).click();await alice.getByLabel('Member email').fill('bob@example.test');await alice.getByRole('button',{name:'Add member',exact:true}).last().click();
  await bob.goto('/plans/'+plan.id);
  await expect(bob.getByRole('button',{name:'Delete plan',exact:true})).toHaveCount(0);
  await alice.getByRole('button',{name:'Transfer ownership',exact:true}).click();await alice.getByLabel('New plan owner').selectOption('bob');await alice.getByRole('button',{name:'Confirm transfer ownership',exact:true}).click();
  await expect(alice.getByRole('button',{name:'Delete plan',exact:true})).toHaveCount(0);
  await bob.reload();await bob.getByRole('button',{name:'Delete plan',exact:true}).click();
  await expect(bob.getByRole('button',{name:'Confirm delete plan',exact:true})).toBeDisabled();
  await bob.getByLabel('Plan name confirmation').fill(title);await bob.getByRole('button',{name:'Cancel',exact:true}).click();
  await expect(bob.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
  await bob.getByRole('button',{name:'Delete plan',exact:true}).click();await bob.getByLabel('Plan name confirmation').fill(title);await bob.getByRole('button',{name:'Confirm delete plan',exact:true}).click();
  await expect(bob).toHaveURL('/');await expect(bob.getByRole('link',{name:'Open '+title,exact:true})).toHaveCount(0);
  await alice.reload();await expect(alice.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
 }finally{await context.close();}
});

test('private link returns through sign-in and joins only after confirmation',async({page:alice,browser})=>{
 await login(alice,'alice');
 const plan=await alice.evaluate(async()=>{const r=await fetch('/api/backend/v1/plans',{method:'POST',headers:{Authorization:'Bearer test-alice','Content-Type':'application/json'},body:JSON.stringify({title:'Invitation-only weekend',kind:'trip',start:'2026-11-05',end:'2026-11-07',participants:''})});return r.json();});
 await alice.goto('/plans/'+plan.id);
 await alice.getByRole('button',{name:'Add member',exact:true}).click();
 await alice.getByRole('button',{name:'Create invitation link'}).click();
 const link=await alice.getByLabel('Private join link',{exact:true}).inputValue();
 expect(link).toContain('/join#');
 const context=await browser.newContext();const bob=await context.newPage();
 try{
  await bob.goto(link);
  await expect(bob.getByRole('link',{name:'Sign in or create account'})).toBeVisible();
  await expect(bob.getByText('Invitation-only weekend',{exact:true})).toHaveCount(0);
  await bob.getByRole('link',{name:'Sign in or create account'}).click();
  await login(bob,'bob');
  await expect(bob.getByRole('link',{name:'Continue to invitation'})).toBeVisible();
  await bob.getByRole('link',{name:'Continue to invitation'}).click();
  await expect(bob.getByRole('button',{name:'Join plan',exact:true})).toBeVisible();
  const before=await bob.evaluate(async()=>{const r=await fetch('/api/backend/v1/plans',{headers:{Authorization:'Bearer test-bob'}});return r.json();});
  expect(before.some((p:{id:string})=>p.id===plan.id)).toBe(false);
  await bob.getByLabel('Preferred display name').fill('Bobby');
  await bob.getByRole('button',{name:'Join plan',exact:true}).click();
  await expect(bob.getByRole('heading',{name:'Invitation-only weekend.'})).toBeVisible();
  expect(await bob.evaluate(()=>sessionStorage.getItem('tagalong-pending-invitation'))).toBeNull();
  await alice.getByRole('button',{name:'Disable invitation link'}).click();
  await bob.goto(link);
  await bob.getByLabel('Preferred display name').fill('Bobby');
  await bob.getByRole('button',{name:'Join plan',exact:true}).click();
  await expect(bob.getByRole('alert').filter({hasText:'unavailable or expired'})).toBeVisible();
 }finally{await context.close();}
});

test('two members share a plan, chat, vote, confirm an AI proposal and preserve it on refresh',async({page:alice,browser,isMobile})=>{
 const bobContext:BrowserContext=await browser.newContext({viewport:isMobile?{width:390,height:844}:{width:1280,height:720},isMobile});
 const bob=await bobContext.newPage();
 try{
  await login(alice,'alice');await login(bob,'bob');
  await alice.goto('/');
  await alice.getByRole('button',{name:'Create a plan',exact:true}).first().click();
  await alice.getByRole('button',{name:'Create a plan manually',exact:true}).click();
  await alice.getByRole('button',{name:'Trip',exact:true}).click();
  await alice.getByLabel('Plan name').fill('Shared coast '+crypto.randomUUID().slice(0,8));
  await alice.getByLabel('Start date').fill('2026-12-04');await alice.getByLabel('End date').fill('2026-12-06');
  await alice.getByRole('button',{name:'Create shared plan'}).click();
  await expect(alice).toHaveURL(/\/plans\//);
  const url=alice.url();
  await bob.goto(url);await expect(bob.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
  await alice.getByRole('button',{name:'Add member',exact:true}).click();
  await alice.getByLabel('Member email').fill('bob@example.test');
  await alice.getByRole('dialog').getByRole('button',{name:'Add member'}).click();
  await expect(alice.getByRole('dialog')).not.toBeVisible();
  await bob.reload();await expect(bob.getByRole('heading',{name:/Shared coast/})).toBeVisible();
  await alice.getByRole('tab',{name:'Documents'}).click();
  await alice.getByLabel('Document title').fill('Group food notes');
  await alice.getByLabel('Document text').fill('We prefer vegetarian meals for this trip.');
  await alice.getByRole('button',{name:'Save document'}).click();
  await expect(alice.getByText('Group food notes',{exact:true})).toBeVisible();
  await alice.getByRole('tab',{name:'Chat'}).click();
  await alice.getByLabel('Message your group').fill('@Tagalong remember our food preferences');
  await alice.getByRole('button',{name:'Send message'}).click();
  await expect(alice.locator('.message-bubble').filter({hasText:'Evidence considered'})).toBeVisible();
  await alice.getByText(/Sources \(/).click();
  await expect(alice.locator('blockquote').filter({hasText:'Group food notes'})).toBeVisible();
  await expect(alice.getByText('@Tagalong remember our food preferences',{exact:true})).toHaveCount(1);
  await alice.getByRole('tab',{name:'Planning board'}).click();
  await expect(alice.getByRole('button',{name:'Confirm Vegetarian'})).toBeVisible();
  await alice.getByRole('button',{name:'Confirm Vegetarian'}).click();
  await expect(alice.getByText('Confirmed by you',{exact:true})).toBeVisible();
  await alice.getByRole('tab',{name:'Polls'}).click();
  await alice.getByRole('button',{name:'Create poll',exact:true}).click();
  await alice.getByLabel('Poll question').fill('Dinner time?');await alice.getByLabel('Option 1').fill('6 pm');await alice.getByLabel('Option 2').fill('7 pm');
  await alice.getByRole('button',{name:'Publish poll',exact:true}).click();
  await bob.reload();await bob.getByRole('tab',{name:'Polls'}).click();
  await bob.getByRole('button',{name:/6 pm/}).click();await expect(bob.getByRole('button',{name:/6 pm/})).toContainText('1 vote');
  await bob.getByRole('button',{name:/7 pm/}).click();await expect(bob.getByRole('button',{name:/7 pm/})).toContainText('1 vote');
  await expect(bob.getByRole('button',{name:/6 pm/})).toContainText('0 votes');
  await alice.reload();await alice.getByRole('tab',{name:'Polls'}).click();await expect(alice.getByRole('button',{name:/7 pm/})).toContainText('1 vote');
  await alice.getByRole('button',{name:'Add member',exact:true}).click();
  await alice.getByRole('button',{name:'Remove member bob'}).click();
  await expect(alice.getByRole('button',{name:'Remove member bob'})).toHaveCount(0);
  await bob.reload();await expect(bob.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
 }finally{await bobContext.close();}
});

test('sign out ignores a delayed private response and keeps demo storage isolated',async({page})=>{
 await login(page,'alice');
 let release:()=>void=()=>{};let markStarted:()=>void=()=>{};
 const started=new Promise<void>(resolve=>{markStarted=resolve;});
 const wait=new Promise<void>(resolve=>{release=resolve;});
 await page.route('**/api/backend/v1/plans',async route=>{markStarted();await wait;await route.fulfill({json:[{id:'private',title:'Private delayed plan',kind:'trip',location:'Private',date:'',start:'',end:'',budget:0,image:'/images/coast.jpg',members:[],messages:[],preferences:[],polls:[],itinerary:[],tasks:[],revision:1,owner_id:'alice',role:'owner'}]});});
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));await started;
 await page.getByRole('button',{name:'Sign out',exact:true}).click();
 release();await expect(page.getByLabel('Email address')).toBeVisible();
 await page.getByRole('button',{name:'Explore the demo'}).click();await page.goto('/');
 await expect(page.getByRole('link',{name:'Open Private delayed plan'})).toHaveCount(0);
 expect(await page.evaluate(()=>localStorage.getItem('tagalong-demo-v1'))).not.toContain('Private delayed plan');
});

test('app admin reviews saved QA plans and audits private access while normal members are denied',async({page:alice,browser})=>{
 await login(alice,'alice','admin');await alice.goto('/admin');
 await expect(alice.getByRole('heading',{name:'Admin dashboard'})).toBeVisible();
 await alice.getByRole('button',{name:'Create QA review plans'}).click();
 await expect(alice.getByRole('heading',{name:'[QA Review] Chicago dinner',exact:true})).toBeVisible();
 await alice.getByRole('button',{name:'Create QA review plans'}).click();
 await expect(alice.getByRole('heading',{name:'[QA Review] Chicago dinner',exact:true})).toHaveCount(1);
 const review=alice.getByRole('button',{name:'Review private plan: [QA Review] Chicago dinner',exact:true});
 await expect(review).toBeDisabled();
 await alice.getByLabel('Reason for admin action').fill('Review synthetic dinner scenario');
 await review.click();
 await expect(alice.getByRole('region',{name:'Private plan review'})).toContainText('Budget: $65');
  await expect(alice.getByText('inspect_plan',{exact:true}).first()).toBeVisible();
 await alice.getByRole('button',{name:'Close private review'}).click();
 const context=await browser.newContext();const bob=await context.newPage();
 try{
  await login(bob,'bob');await bob.goto('/admin');
  await expect(bob.getByRole('heading',{name:'Admin access required'})).toBeVisible();
  await expect(bob.getByRole('link',{name:'Admin',exact:true})).toHaveCount(0);
  const status=await bob.evaluate(async()=>{const r=await fetch('/api/backend/v1/admin/overview',{headers:{Authorization:'Bearer test-bob'}});return r.status;});
  expect(status).toBe(403);
  await alice.reload();
  await alice.getByLabel('Reason for admin action').fill('QA suspension and restoration');
  await alice.getByRole('button',{name:'Suspend bob',exact:true}).click();
  await expect(alice.getByRole('button',{name:'Restore bob',exact:true})).toBeVisible();
  const denied=await bob.evaluate(async()=>{const r=await fetch('/api/backend/v1/me',{headers:{Authorization:'Bearer test-bob'}});return r.status;});
  expect(denied).toBe(403);
  await bob.evaluate(()=>window.dispatchEvent(new Event('focus')));
  await expect(bob.getByLabel('Email address')).toBeVisible();
  await expect(bob.getByRole('heading',{name:'Admin access required'})).toHaveCount(0);
  await alice.getByRole('button',{name:'Restore bob',exact:true}).click();
  await expect(alice.getByRole('button',{name:'Suspend bob',exact:true})).toBeVisible();
 }finally{await alice.evaluate(async()=>{await fetch('/api/backend/v1/admin/accounts/bob/suspension',{method:'POST',headers:{Authorization:'Bearer test-alice','X-Workspace-Mode':'admin','Content-Type':'application/json'},body:JSON.stringify({suspended:false,reason:'QA cleanup restore test member'})});});await context.close();}
});

test('admin can replay all demo stories then switch to member with no scenarios or dashboard access',async({page})=>{
 await login(page,'alice','admin');await page.goto('/admin');
 const titles=['Christmas weekend in San Francisco','Three days in Yosemite','A San Francisco date night'];
 for(const title of titles){
  await page.getByRole('button',{name:'Open story: '+title,exact:true}).click();
  const replay=page.getByRole('region',{name:'Demo story replay'});
  await expect(replay).toContainText('Fictional people and conversation');
  await expect(replay.getByRole('heading',{name:'Planning in progress'})).toBeVisible();
  await replay.getByRole('button',{name:'Show complete conversation'}).click();
  await expect(replay.getByRole('heading',{name:'Agreed planning outline'})).toBeVisible();
  await expect(replay).toContainText('No bookings have been made.');
  await replay.getByRole('button',{name:'Replay from start'}).click();
  await expect(replay).toContainText('Step 1 of');
 }
 const qa=await page.evaluate(async()=>{const response=await fetch('/api/backend/v1/admin/qa-plans',{method:'POST',headers:{Authorization:'Bearer test-alice','X-Workspace-Mode':'admin','Content-Type':'application/json'},body:'{}'});return response.json();});
 await page.goto('/account');await page.getByRole('button',{name:'Switch to Member',exact:true}).click();
 await expect(page.getByText('Current role: Member',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Admin',exact:true})).toHaveCount(0);
 await page.goto('/');await expect(page.getByRole('link',{name:/Open \[QA Review\]/})).toHaveCount(0);
 await page.goto('/plans/'+qa.plan_ids[0]);await expect(page.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
 await page.goto('/admin');await expect(page.getByRole('heading',{name:'Admin access required'})).toBeVisible();
 const status=await page.evaluate(async()=>{const response=await fetch('/api/backend/v1/admin/demo-stories',{headers:{Authorization:'Bearer test-alice'}});return response.status;});
 expect(status).toBe(403);
});
