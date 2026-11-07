import {test,expect,type Page} from '@playwright/test';

async function signIn(page:Page){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-alice',refresh_token:'refresh-alice',token_type:'bearer',expires_in:3600,user:{id:'alice',email:'alice@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByLabel('Email address',{exact:true}).fill('alice@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}
test('a newer authoritative decision snapshot stays usable while the plan list catches up',async({page})=>{
 await signIn(page);
 const headers={Authorization:'Bearer test-alice'};
 const created=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Snapshot catch-up '+crypto.randomUUID().slice(0,8),kind:'trip',start:'2027-05-14',end:'2027-05-16'}});expect(created.ok()).toBeTruthy();const plan=await created.json();
 const base='/api/backend/v1/plans/'+plan.id;const snapshot=await(await page.request.get(base+'/decisions',{headers})).json();const decision=snapshot.decisions.find((item:{options:unknown[]})=>item.options.length>0);expect(decision).toBeTruthy();
 const comment=await page.request.post(base+'/decisions/'+decision.id+'/comments',{headers,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,text:'Newer decision evidence while the plan list refresh is delayed.'}});expect(comment.ok()).toBeTruthy();
 await page.route('**/api/backend/v1/plans',async route=>{if(route.request().method()!=='GET'){await route.continue();return;}const response=await route.fetch();const plans=await response.json();await route.fulfill({response,json:plans.map((item:{id:string})=>item.id===plan.id?plan:item)});});
 await page.goto('/plans/'+plan.id);const card=page.getByRole('article').filter({has:page.getByRole('heading',{name:decision.title,exact:true})}).first();
 await expect(card.getByRole('button',{name:'Save response',exact:true})).toBeEnabled();await card.getByRole('button',{name:'Save response',exact:true}).click();await expect(card.getByText(/Your current response: support/)).toBeVisible();
});

test('final review waits for matching plan context even when decisions are up to date',async({page})=>{
 await signIn(page);const headers={Authorization:'Bearer test-alice'};
 const result=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Fresh final review '+crypto.randomUUID().slice(0,8),kind:'trip',start:'2027-05-14',end:'2027-05-16'}});expect(result.ok()).toBeTruthy();const initial=await result.json(),base='/api/backend/v1/plans/'+initial.id;
 let snapshot=await(await page.request.get(base+'/decisions',{headers})).json();
 for(const original of snapshot.decisions.filter((item:{required:boolean})=>item.required)){
  let decision=snapshot.decisions.find((item:{id:string})=>item.id===original.id);
  if(!decision.options.length){const edit=await page.request.patch(base+'/decisions/'+decision.id,{headers,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,options:['Reviewed '+decision.title]}});expect(edit.ok()).toBeTruthy();snapshot=await edit.json();decision=snapshot.decisions.find((item:{id:string})=>item.id===original.id);}
  const data={expected_revision:snapshot.plan_revision,expected_version:decision.version,option_id:decision.options[0].id};const response=await page.request.put(base+'/decisions/'+decision.id+'/response',{headers,data:{...data,response:'support'}});expect(response.ok()).toBeTruthy();snapshot=await response.json();const confirmed=await page.request.post(base+'/decisions/'+decision.id+'/confirm',{headers,data:{...data,expected_revision:snapshot.plan_revision}});expect(confirmed.ok()).toBeTruthy();snapshot=await confirmed.json();
 }
 const oldPlan=await(await page.request.get(base,{headers})).json();
 const currentDecision=snapshot.decisions[0];const changed=await page.request.post(base+'/decisions/'+currentDecision.id+'/comments',{headers,data:{expected_revision:snapshot.plan_revision,expected_version:currentDecision.version,text:'New discussion to review before the final owner check.'}});expect(changed.ok()).toBeTruthy();
 let stale=true;await page.route('**/api/backend/v1/plans',async route=>{const response=await route.fetch();const plans=await response.json();await route.fulfill({response,json:plans.map((item:{id:string})=>stale&&item.id===initial.id?oldPlan:item)});});
 await page.goto('/plans/'+initial.id);await page.locator('#final-review').click();let dialog=page.getByRole('dialog');await expect(dialog.getByRole('checkbox')).toBeDisabled();await expect(dialog.getByRole('button',{name:'Finalize reviewed plan',exact:true})).toBeDisabled();
 stale=false;await page.reload();await page.locator('#final-review').click();dialog=page.getByRole('dialog');await dialog.getByRole('checkbox').check();await dialog.getByRole('button',{name:'Finalize reviewed plan',exact:true}).click();await expect(dialog.getByRole('button',{name:'Reopen plan',exact:true})).toBeVisible();
});
