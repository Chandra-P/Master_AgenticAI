import {test,expect,type Page} from '@playwright/test';

async function login(page:Page,name:'alice'|'bob'){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');
 await page.getByRole('radio',{name:'Member',exact:true}).check();
 await page.getByLabel('Email address').fill(name+'@example.test');
 await page.getByLabel('Password',{exact:true}).fill('synthetic-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}
async function createGroup(page:Page){
 const name='Weekend friends · Circle '+crypto.randomUUID().slice(0,8);
 const response=await page.request.post('/api/backend/v1/groups',{headers:{Authorization:'Bearer test-alice'},data:{name,theme:'Weekend friends',members:[{id:'alice',preferredName:'alice',color:'#edc6b3'},{id:'roster-bob',preferredName:'Bobby',color:'#c6d5c4',email:'bob@example.test',firstName:'PrivateFirst',lastName:'PrivateLast'},{id:'alias-only',preferredName:'River',color:'#ccc'}]}});
 expect(response.ok()).toBeTruthy();return response.json();
}

test('owner shares explicitly; member sees read-only details and no private contacts or plan access',async({page,browser},testInfo)=>{
 await login(page,'alice');const group=await createGroup(page);
 const headers={Authorization:'Bearer test-bob'};
 expect((await page.request.get('/api/backend/v1/groups/'+group.id,{headers})).status()).toBe(404);
 await page.goto('/groups');
 const card=page.getByRole('article',{name:group.name,exact:true});
 // The body of the card opens details, not the editor.
 await card.click({position:{x:30,y:100}});
 const details=page.getByRole('dialog',{name:'Group details',exact:true});
 await expect(details.getByRole('heading',{name:group.name,exact:true})).toBeVisible();
 await expect(details.getByText('bob@example.test',{exact:true})).toBeVisible();
 await details.getByRole('button',{name:'Share with members',exact:true}).click();
 await expect(details.getByRole('button',{name:'Stop sharing',exact:true})).toBeVisible();
 await details.getByRole('button',{name:'Close',exact:true}).click();
 const context=await browser.newContext({baseURL:'http://127.0.0.1:3200'});
 try{
  const member=await context.newPage();await login(member,'bob');await member.goto('/groups');
  const memberCard=member.getByRole('article',{name:group.name,exact:true});
  await expect(memberCard).toContainText('Shared with you');await expect(memberCard).toContainText('alice owns this group');
  await expect(memberCard.getByRole('button',{name:/^(Edit |Archive |Remove |Plan with)/})).toHaveCount(0);
  const open=memberCard.getByRole('button',{name:'View group '+group.name,exact:true});
  await open.focus();await open.press('Enter');
  const view=member.getByRole('dialog',{name:'Group details',exact:true});
  await expect(view.getByText('Bobby',{exact:true})).toBeVisible();
  await expect(view.getByText('River',{exact:true})).toBeVisible();
  await expect(view).toContainText('View only');
  await expect(view).not.toContainText('bob@example.test');await expect(view).not.toContainText('PrivateFirst');
  await expect(view.getByRole('button',{name:/^(Edit group|Share with members|Stop sharing)$/})).toHaveCount(0);
  await member.screenshot({path:testInfo.outputPath('shared-group-details.png'),fullPage:true});
  await view.getByRole('button',{name:'Close',exact:true}).click();await expect(open).toBeFocused();
  await member.goto('/');
  await expect(member.getByLabel('Plan with a group',{exact:true}).getByRole('option',{name:group.name,exact:true})).toHaveCount(0);
  await card.getByRole('button',{name:'View group '+group.name,exact:true}).click();
  await details.getByRole('button',{name:'Stop sharing',exact:true}).click();
  await expect(details.getByRole('button',{name:'Share with members',exact:true})).toBeVisible();
  expect((await member.request.get('/api/backend/v1/groups/'+group.id,{headers})).status()).toBe(404);
  await member.goto('/groups');await expect(memberCard).toHaveCount(0);
 }finally{await context.close();}
});

test('edit stays independent from details and stale sharing approval is rejected',async({page})=>{
 await login(page,'alice');const group=await createGroup(page);await page.goto('/groups');
 const card=page.getByRole('article',{name:group.name,exact:true});
 await card.getByRole('button',{name:'Edit '+group.name,exact:true}).click();
 await expect(page.getByLabel('Group name',{exact:true})).toHaveValue(group.name);
 await expect(page.getByRole('dialog',{name:'Group details',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Cancel',exact:true}).click();
 await card.getByRole('button',{name:'View group '+group.name,exact:true}).press('Space');
 const details=page.getByRole('dialog',{name:'Group details',exact:true});
 await expect(details.getByRole('button',{name:'Share with members',exact:true})).toBeVisible();
 const changed=await page.request.post('/api/backend/v1/groups/'+group.id+'/sharing',{headers:{Authorization:'Bearer test-alice'},data:{shared:true,expected_revision:1}});
 expect(changed.ok()).toBeTruthy();
 await details.getByRole('button',{name:'Share with members',exact:true}).click();
 await expect(details.getByRole('alert')).toContainText('This group changed');
 await details.getByRole('button',{name:'Close',exact:true}).click();
 await card.getByRole('button',{name:'View group '+group.name,exact:true}).click();
 await expect(details.getByRole('button',{name:'Stop sharing',exact:true})).toBeVisible();
});

test('revoking group sharing clears an open member dialog on refresh',async({page})=>{
 await login(page,'bob');const group=await createGroup(page);
 await page.request.post('/api/backend/v1/groups/'+group.id+'/sharing',{headers:{Authorization:'Bearer test-alice'},data:{shared:true,expected_revision:1}});
 await page.goto('/groups');await page.getByRole('article',{name:group.name,exact:true}).getByRole('button',{name:'View group '+group.name,exact:true}).click();
 const details=page.getByRole('dialog',{name:'Group details',exact:true});
 await expect(details.getByText('Bobby',{exact:true})).toBeVisible();
 await page.request.post('/api/backend/v1/groups/'+group.id+'/sharing',{headers:{Authorization:'Bearer test-alice'},data:{shared:false,expected_revision:2}});
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await expect(details.getByRole('alert')).toContainText('Group not found');
 await expect(details.getByText('Bobby',{exact:true})).toHaveCount(0);
});

test('late detail responses cannot survive sign-out or enter another account',async({page})=>{
 await login(page,'alice');const group=await createGroup(page);await page.goto('/groups');
 let release!:()=>void,started!:()=>void;
 const held=new Promise<void>(resolve=>{release=resolve;});
 const received=new Promise<void>(resolve=>{started=resolve;});
 await page.route('**/api/backend/v1/groups/'+group.id,async route=>{
  started();await held;await route.fulfill({json:{...group,name:'Private delayed detail',ownerName:'alice',role:'owner'}}).catch(()=>{});
 });
 await page.getByRole('article',{name:group.name,exact:true}).getByRole('button',{name:'View group '+group.name,exact:true}).click();
 await received;
 await page.getByRole('dialog',{name:'Group details',exact:true}).getByRole('button',{name:'Close',exact:true}).click();
 await page.getByRole('link',{name:'Account',exact:true}).click();
 await page.getByRole('button',{name:'Sign out',exact:true}).click();
 await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
 const completed=page.waitForResponse(response=>response.url().endsWith('/v1/groups/'+group.id));
 release();await completed;
 await page.unroute('**/api/backend/v1/groups/'+group.id);
 await page.unroute('https://tagalong-test.supabase.co/auth/v1/**');
 await login(page,'bob');await page.goto('/groups');
 await expect(page.getByRole('button',{name:'Create a group',exact:true}).first()).toBeEnabled();
 await expect(page.getByText('Private delayed detail',{exact:true})).toHaveCount(0);
 await expect(page.getByRole('article',{name:group.name,exact:true})).toHaveCount(0);
});
