import {test,expect,type Page} from '@playwright/test';

async function login(page:Page,name:'alice'|'bob'){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByRole('radio',{name:'Member',exact:true}).check();
 await page.getByLabel('Email address').fill(name+'@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}
async function group(page:Page){
 const name='Sharing circle '+crypto.randomUUID().slice(0,8);
 const response=await page.request.post('/api/backend/v1/groups',{headers:{Authorization:'Bearer test-alice'},data:{name,theme:'Weekend friends',members:[{id:'alice',preferredName:'alice',color:'#fff'},{id:'roster-bob',preferredName:'Bobby',color:'#ccc',email:'bob@example.test'},{id:'alias-only',preferredName:'River',color:'#ddd'}]}});
 expect(response.ok()).toBeTruthy();return response.json();
}
async function notification(page:Page,title:string){
 await page.getByRole('button',{name:/^Notifications,/}).click();
 const dialog=page.getByRole('dialog',{name:'Notifications',exact:true});
 const item=dialog.getByRole('listitem').filter({hasText:title});await expect(item).toBeVisible();return {dialog,item};
}

test('manual group plan requires approval then appears with one persistent in-app notification',async({page,browser},info)=>{
 await login(page,'alice');const g=await group(page);await page.goto('/groups');
 await page.getByRole('article',{name:g.name,exact:true}).getByRole('button',{name:'Plan with this group',exact:true}).click();
 await page.getByRole('button',{name:'Create a plan manually',exact:true}).click();
 const title='Approved manual '+crypto.randomUUID().slice(0,8);
 await page.getByLabel('Plan name',{exact:true}).fill(title);await page.getByLabel('Start date',{exact:true}).fill('2027-05-14');
 const approval=page.getByLabel('Share this plan with group members',{exact:true});await expect(approval).not.toBeChecked();
 await expect(page.getByText(/Cannot receive automatic access.*River/)).toBeVisible();
 await approval.check();await page.getByRole('button',{name:'Create shared plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
 const context=await browser.newContext({baseURL:'http://127.0.0.1:3200'});
 try{
  const member=await context.newPage();await login(member,'bob');
  let {dialog,item}=await notification(member,title);await expect(item.getByText('Unread',{exact:true})).toBeVisible();
  await member.screenshot({path:info.outputPath('plan-notifications.png'),fullPage:true});
  await item.getByRole('button',{name:'Mark as read',exact:true}).click();await expect(item.getByText('Read',{exact:true})).toBeVisible();
  await dialog.getByRole('button',{name:'Close',exact:true}).click();await member.reload();
  ({dialog,item}=await notification(member,title));await expect(item.getByText('Read',{exact:true})).toBeVisible();
  await item.getByRole('link',{name:'Open plan',exact:true}).click();
  await expect(member.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
  await expect(member.getByRole('button',{name:'Add decision',exact:true})).toHaveCount(0);
  const notices=await (await member.request.get('/api/backend/v1/notifications',{headers:{Authorization:'Bearer test-bob'}})).json();
  expect(notices.filter((n:{title:string})=>n.title===title)).toHaveLength(1);
 }finally{await context.close();}
});

test('reviewed AI draft shares only after the owner checks the recipient approval',async({page})=>{
 await login(page,'alice');const g=await group(page);await page.goto('/groups');
 await page.getByRole('article',{name:g.name,exact:true}).getByRole('button',{name:'Plan with this group',exact:true}).click();
 await page.getByLabel('Describe your plan',{exact:true}).fill('A relaxed weekend in Austin with our friends');
 await page.getByRole('button',{name:'Start Planning',exact:true}).click();
 const title='Approved draft '+crypto.randomUUID().slice(0,8);
 await page.getByText('Edit plan name and type',{exact:true}).click();await page.getByLabel('Generated plan name',{exact:true}).fill(title);
 await page.getByLabel('Working start date',{exact:true}).fill('2027-05-14');await page.getByLabel('Working end date',{exact:true}).fill('2027-05-16');
 await page.getByLabel('Share this plan with group members',{exact:true}).check();
 await page.getByRole('button',{name:'Create reviewed plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
 const notices=await (await page.request.get('/api/backend/v1/notifications',{headers:{Authorization:'Bearer test-bob'}})).json();
 expect(notices.some((n:{title:string})=>n.title===title)).toBeTruthy();
});

test('existing-plan sharing supports pending revocation and member removal without automatic rejoin',async({page})=>{
 await login(page,'alice');const g=await group(page);
 const title='Existing private '+crypto.randomUUID().slice(0,8),headers={Authorization:'Bearer test-alice'};
 const created=await page.request.post('/api/backend/v1/plans',{headers,data:{title,kind:'outing',start:'2027-05-14',end:'2027-05-14'}});const p=await created.json();
 expect((await page.request.get('/api/backend/v1/plans/'+p.id,{headers:{Authorization:'Bearer test-bob'}})).status()).toBe(404);
 await page.goto('/plans/'+p.id);await page.getByRole('button',{name:'Add member',exact:true}).click();
 await page.getByLabel('Group to share with',{exact:true}).selectOption(g.id);
 await page.getByLabel('Share this plan with group members',{exact:true}).check();
 await page.getByRole('button',{name:'Share plan with group',exact:true}).click();
 const pending=page.getByRole('button',{name:'Revoke pending access for Bobby',exact:true});await expect(pending).toBeVisible();
 await pending.click();await expect(page.getByText('Bobby · Access approval revoked',{exact:true})).toBeVisible();
 expect((await page.request.get('/api/backend/v1/plans/'+p.id,{headers:{Authorization:'Bearer test-bob'}})).status()).toBe(404);
 await page.getByLabel('Share this plan with group members',{exact:true}).check();await page.getByRole('button',{name:'Share plan with group',exact:true}).click();
 await expect(pending).toBeVisible();
 expect((await page.request.get('/api/backend/v1/plans/'+p.id,{headers:{Authorization:'Bearer test-bob'}})).ok()).toBeTruthy();
 await page.getByRole('button',{name:'Close',exact:true}).click();await page.reload();
 await page.getByRole('button',{name:'Add member',exact:true}).click();
 await page.getByRole('button',{name:'Remove member bob',exact:true}).click();
 await expect(page.getByRole('button',{name:'Remove member bob',exact:true})).toHaveCount(0);
 for(let i=0;i<2;i++)expect((await page.request.get('/api/backend/v1/plans/'+p.id,{headers:{Authorization:'Bearer test-bob'}})).status()).toBe(404);
 const notices=await(await page.request.get('/api/backend/v1/notifications',{headers:{Authorization:'Bearer test-bob'}})).json();
 expect(notices.some((n:{plan_id:string})=>n.plan_id===p.id)).toBeFalsy();
});

test('late notification reads cannot enter another signed-in account',async({page})=>{
 await login(page,'alice');let release!:()=>void,received!:()=>void;
 const held=new Promise<void>(resolve=>{release=resolve;});const started=new Promise<void>(resolve=>{received=resolve;});
 await page.route('**/api/backend/v1/notifications',async route=>{received();await held;await route.fulfill({json:[{id:'late',plan_id:'private',title:'Private delayed notification',created_at:'2026-01-01T00:00:00Z',read:false}]}).catch(()=>{});});
 await page.getByRole('button',{name:/^Notifications,/}).click();await started;
 await page.getByRole('dialog',{name:'Notifications',exact:true}).getByRole('button',{name:'Close',exact:true}).click();
 await page.getByRole('link',{name:'Account',exact:true}).click();
 const logout=page.waitForResponse(response=>response.url().includes('/auth/v1/logout'));
 await page.getByRole('button',{name:'Sign out',exact:true}).click();await logout;
 await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
 release();await page.unroute('**/api/backend/v1/notifications');await login(page,'bob');
 await page.getByRole('button',{name:/^Notifications,/}).click();await expect(page.getByRole('dialog')).not.toContainText('Private delayed notification');
});
