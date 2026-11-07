import {test,expect,type Page} from '@playwright/test';

async function login(page:Page,name:'alice'|'bob'='alice'){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');
 await page.getByRole('radio',{name:'Member',exact:true}).check();
 await page.getByLabel('Email address').fill(name+'@example.test');
 await page.getByLabel('Password',{exact:true}).fill('test-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}
async function makeGroup(page:Page){
 await page.goto('/groups');
 await page.getByRole('button',{name:'Create a group',exact:true}).first().click();
 const dialog=page.getByRole('dialog');
 const name='Shared circle '+crypto.randomUUID().slice(0,8);
 await dialog.getByLabel('Group name',{exact:true}).fill(name);
 await dialog.getByRole('button',{name:'Custom',exact:true}).click();
 await dialog.getByLabel('Custom theme',{exact:true}).fill('Tabletop evenings');
 await dialog.getByRole('button',{name:'Add adult',exact:true}).click();
 await dialog.getByLabel('Preferred name / alias',{exact:true}).fill('River');
 await dialog.getByLabel('Email (optional)',{exact:true}).fill('private-contact@example.test');
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 const card=page.getByRole('article',{name,exact:true});await expect(card).toBeVisible();
 return {name,card};
}

test('real-account groups persist across sessions and remain private without importing demo contacts',async({page,browser},testInfo)=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-groups-v1',JSON.stringify([{id:'demo-private',name:'Local sentinel',theme:'Sunday supper',ownerId:'alex',archived:false,members:[{id:'alex',preferredName:'Alex',color:'#fff'}]}])));
 await login(page);
 const {name,card}=await makeGroup(page);
 await expect(card).toContainText('alice owns this group');
 await expect(page.getByRole('heading',{name:'Local sentinel',exact:true})).toHaveCount(0);
 await page.screenshot({path:testInfo.outputPath('shared-groups.png'),fullPage:true});
 const saved=(await(await page.request.get('/api/backend/v1/groups',{headers:{Authorization:'Bearer test-alice'}})).json()).find((g:{name:string})=>g.name===name);
 expect(saved.ownerId).toBe('alice');expect(saved.members[1].email).toBe('private-contact@example.test');
 const otherContext=await browser.newContext({baseURL:'http://127.0.0.1:3200'});const other=await otherContext.newPage();
 try{
  await login(other);await other.goto('/groups');await expect(other.getByRole('heading',{name,exact:true})).toBeVisible();
 }finally{await otherContext.close();}
 expect((await page.request.get('/api/backend/v1/groups/'+saved.id,{headers:{Authorization:'Bearer test-bob'}})).status()).toBe(404);
 await page.reload();await expect(card).toBeVisible();
});

test('selected group survives manual creation, archive and removal without granting contact access',async({page})=>{
 await login(page);const {name,card}=await makeGroup(page);
 await card.getByRole('button',{name:'Plan with this group',exact:true}).click();
 await expect(page.getByLabel('Plan with a group',{exact:true})).not.toHaveValue('');
 await page.getByRole('button',{name:'Create a plan manually',exact:true}).click();
 await expect(page.getByLabel('Plan with a group',{exact:true})).not.toHaveValue('');
 const title='Roster supper '+crypto.randomUUID().slice(0,8);
 await page.getByLabel('Plan name',{exact:true}).fill(title);
 await page.getByLabel('Start date',{exact:true}).fill('2027-05-14');
 await page.getByRole('button',{name:'Create a new group',exact:true}).click();
 await page.getByRole('button',{name:'Cancel',exact:true}).click();
 await expect(page.getByLabel('Plan name',{exact:true})).toHaveValue(title);
 await expect(page.getByText(/Intended participants only/)).toBeVisible();
 await page.getByRole('button',{name:'Create shared plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
 await expect(page.getByText(/Intended roster: alice, River/)).toBeVisible();
 const headers={Authorization:'Bearer test-alice'};
 const plan=(await(await page.request.get('/api/backend/v1/plans',{headers})).json()).find((p:{title:string})=>p.title===title);
 expect(plan.members).toHaveLength(1);expect(JSON.stringify(plan)).not.toContain('private-contact@example.test');
 expect((await page.request.get('/api/backend/v1/plans/'+plan.id,{headers:{Authorization:'Bearer test-bob'}})).status()).toBe(404);
 await page.goto('/groups');await card.getByRole('button',{name:'Archive '+name,exact:true}).click();
 await expect(card).toHaveCount(0);await page.getByRole('button',{name:/^Archived/}).click();
 await card.getByRole('button',{name:'Restore '+name,exact:true}).click();await page.getByRole('button',{name:/^Active/}).click();
 await card.getByRole('button',{name:'Remove '+name,exact:true}).click();await page.getByRole('button',{name:'Remove group',exact:true}).click();
 await expect(card).toHaveCount(0);
 expect(await(await page.request.get('/api/backend/v1/plans/'+plan.id,{headers})).json()).toEqual(plan);
});

test('generated plan review retains group selection and excludes contact details from AI requests',async({page})=>{
 await login(page);const {name,card}=await makeGroup(page);
 await card.getByRole('button',{name:'Plan with this group',exact:true}).click();
 const requests:string[]=[];page.on('request',request=>{if(request.url().includes('/v1/plans/generate'))requests.push(request.postData()||'');});
 await page.getByLabel('Describe your plan',{exact:true}).fill('A relaxed tabletop evening in Austin');
 await page.getByRole('button',{name:'Generate Plan',exact:true}).click();
 await expect(page.getByRole('region',{name:'Review AI plan draft',exact:true})).toBeVisible();
 const title='Reviewed roster '+crypto.randomUUID().slice(0,8);
 await page.getByLabel('Generated plan name',{exact:true}).fill(title);
 await page.getByLabel('Confirmed start date',{exact:true}).fill('2027-05-14');
 await page.getByLabel('Confirmed end date',{exact:true}).fill('2027-05-16');
 await expect(page.getByText(/Intended participants only/).first()).toBeVisible();
 await page.getByRole('button',{name:'Create reviewed plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
 const plan=(await(await page.request.get('/api/backend/v1/plans',{headers:{Authorization:'Bearer test-alice'}})).json()).find((p:{title:string})=>p.title===title);
 expect(plan.group.name).toBe(name);expect(plan.group.participants).toEqual(['alice','River']);expect(plan.members).toHaveLength(1);
 expect(requests.join('')).not.toContain('private-contact@example.test');expect(JSON.stringify(plan)).not.toContain('private-contact@example.test');
});

test('late group responses cannot repopulate a signed-out workspace',async({page})=>{
 await login(page);await page.goto('/groups');await expect(page.getByRole('button',{name:'Create a group',exact:true}).first()).toBeEnabled();
 let release!:()=>void;const held=new Promise<void>(resolve=>{release=resolve;});
 let received!:()=>void;const started=new Promise<void>(resolve=>{received=resolve;});
 await page.route('**/api/backend/v1/groups',async route=>{
  if(route.request().method()!=='GET'){await route.continue();return;}
  received();await held;await route.fulfill({json:[{id:'late',name:'Private late roster',theme:'Dinner',ownerId:'alice',members:[{id:'alice',preferredName:'alice',color:'#fff'}],archived:false,revision:1}]}).catch(()=>{});
 });
 await page.goto('/groups');await started;await page.getByRole('link',{name:'Account',exact:true}).click();
 await page.getByRole('button',{name:'Sign out',exact:true}).click();
 await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
 const completed=page.waitForResponse(response=>response.url().endsWith('/api/backend/v1/groups'));release();await completed;
 await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
 await expect(page.getByText('Private late roster',{exact:true})).toHaveCount(0);
 await page.unroute('**/api/backend/v1/groups');await login(page,'bob');await page.goto('/groups');
 await expect(page.getByRole('button',{name:'Create a group',exact:true}).first()).toBeEnabled();
 await expect(page.getByText('Private late roster',{exact:true})).toHaveCount(0);
});
