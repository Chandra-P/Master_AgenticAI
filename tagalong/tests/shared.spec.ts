import {test,expect,type Page,type BrowserContext} from '@playwright/test';

async function login(page:Page,name:'alice'|'bob'){
 const config=await (await page.request.get('/api/config')).json();
 expect(config.supabaseUrl).toBe('https://tagalong-test.supabase.co');
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');
 await page.getByLabel('Email address').fill(name+'@example.test');
 await page.getByLabel('Password',{exact:true}).fill('test-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}

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
