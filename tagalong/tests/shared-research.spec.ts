import {test,expect,type Page} from '@playwright/test';
import {openTool} from './planning-tools';

test('saved notes and real tool receipts lead to a sourced decision option without booking',async({page})=>{
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-alice',refresh_token:'refresh-alice',token_type:'bearer',expires_in:3600,user:{id:'alice',email:'alice@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByLabel('Email address',{exact:true}).fill('alice@example.test');await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await page.goto('/');await page.getByRole('button',{name:'Create a plan manually',exact:true}).click();
 const title='Sourced dinner '+crypto.randomUUID().slice(0,8);await page.getByLabel('Plan name').fill(title);await page.getByLabel('Start date').fill('2027-04-16');await page.getByRole('button',{name:'Create shared plan',exact:true}).click();await expect(page.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
 await openTool(page,'Documents');await page.getByLabel('Document title').fill('Our dinner needs');await page.getByLabel('Document text').fill('We prefer vegetarian food and quiet places where we can talk.');await page.getByRole('button',{name:'Save document'}).click();await expect(page.getByText('Our dinner needs',{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Decisions',exact:true}).click();
 const place=page.getByRole('article').filter({has:page.getByRole('heading',{name:'Place',exact:true})}).first();await place.getByRole('button',{name:'Find options',exact:true}).click();
 const dialog=page.getByRole('dialog');await dialog.getByLabel('What are you looking for?',{exact:true}).fill('Vegetarian dinner in April');await dialog.getByLabel('Search location',{exact:true}).fill('Austin');await dialog.getByRole('button',{name:'Search with group context',exact:true}).click();
 await expect(dialog.getByRole('heading',{name:'What Tagalong actually used',exact:true})).toBeVisible();
 const evidence=dialog.getByRole('region',{name:'Remembered group context'});await evidence.getByText('Our dinner needs',{exact:true}).click();await expect(evidence.getByText(/We prefer vegetarian food/)).toBeVisible();
 await expect(dialog.getByRole('link',{name:'Explore Synthetic vegetarian restaurant',exact:true})).toHaveAttribute('href','https://places.example.test/restaurant');
 await dialog.getByRole('button',{name:'Review and add option',exact:true}).click();await expect(dialog.getByLabel('Option name',{exact:true})).toHaveValue('Synthetic vegetarian restaurant');
 const base=new URL(page.url()).pathname.replace('/plans/','/api/backend/v1/plans/'),headers={Authorization:'Bearer test-alice'};
 const before=await(await page.request.get(base+'/decisions',{headers})).json();const decision=before.decisions.find((d:{title:string})=>d.title==='Place');
 expect((await page.request.post(base+'/decisions/'+decision.id+'/comments',{headers,data:{expected_revision:before.plan_revision,expected_version:decision.version,text:'Verify current availability before agreeing.'}})).ok()).toBeTruthy();
 await expect(dialog.getByText('The group plan changed after this search. Your selected option and original source are kept. Review the current group needs before adding it.',{exact:true})).toBeVisible({timeout:20000});
 await dialog.getByRole('button',{name:'Add to decision',exact:true}).click();await expect(dialog).not.toBeVisible();
 await expect(place.getByRole('link',{name:'Visit Synthetic vegetarian restaurant',exact:true})).toBeVisible();await page.reload();await expect(place.getByRole('link',{name:'Visit Synthetic vegetarian restaurant',exact:true})).toBeVisible();
 await place.getByText('Source evidence for Synthetic vegetarian restaurant',{exact:true}).click();await expect(place.getByText(/Unverified source retrieved/)).toBeVisible();await expect(place.locator('.decision-option-details details').getByText('Synthetic public source snippet for browser verification.',{exact:true})).toBeVisible();
 await place.getByRole('button',{name:'Save response',exact:true}).click();await place.getByRole('button',{name:'Confirm selected option',exact:true}).click();await expect(place.getByText('Confirmed',{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Itinerary',exact:true}).click();const outcomes=page.getByRole('region',{name:'Confirmed decision outcomes'});await expect(outcomes.getByRole('heading',{name:'Synthetic vegetarian restaurant',exact:true})).toBeVisible();await expect(outcomes.getByText('Not booked',{exact:true})).toBeVisible();
});

async function fixtureLogin(page:Page,name:'alice'|'bob'){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByLabel('Email address',{exact:true}).fill(name+'@example.test');await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}

test('a member can submit an option suggestion without changing the owner voting options',async({page})=>{
 await fixtureLogin(page,'bob');const owner={Authorization:'Bearer test-alice'};
 const response=await page.request.post('/api/backend/v1/plans',{headers:owner,data:{title:'Member alternatives '+crypto.randomUUID().slice(0,8),kind:'trip',start:'2027-04-16',end:'2027-04-18'}});expect(response.ok()).toBeTruthy();const plan=await response.json();
 expect((await page.request.post('/api/backend/v1/plans/'+plan.id+'/members',{headers:owner,data:{email:'bob@example.test'}})).ok()).toBeTruthy();
 await page.goto('/plans/'+plan.id);const lodging=page.getByRole('article').filter({has:page.getByRole('heading',{name:'Lodging',exact:true})}).first();await expect(lodging.getByRole('button',{name:'Add option',exact:true})).toHaveCount(0);await lodging.getByRole('button',{name:'Find options',exact:true}).click();
 const dialog=page.getByRole('dialog');await dialog.getByRole('button',{name:'Add your own',exact:true}).click();await dialog.getByLabel('Option name',{exact:true}).fill('Member suggested lodge');await dialog.getByLabel('Website link',{exact:true}).fill('https://example.com/member-lodge');await dialog.getByRole('button',{name:'Suggest in comments',exact:true}).click();await expect(dialog).not.toBeVisible();
 await lodging.getByRole('button',{name:/comments/}).click();await expect(lodging.locator('.decision-comments > div').filter({hasText:'Option suggestion: Member suggested lodge'})).toBeVisible();await expect(lodging.getByRole('radio')).toHaveCount(0);
});

test('changing between same-category decisions discards a late research response',async({page})=>{
 await fixtureLogin(page,'alice');const headers={Authorization:'Bearer test-alice'};
 const response=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Research targets '+crypto.randomUUID().slice(0,8),kind:'outing',start:'2027-04-16',end:'2027-04-16'}});const plan=await response.json();
 const snapshot=await(await page.request.get('/api/backend/v1/plans/'+plan.id+'/decisions',{headers})).json();const place=snapshot.decisions.find((d:{category:string})=>d.category==='place');
 const created=await page.request.post('/api/backend/v1/plans/'+plan.id+'/decisions',{headers,data:{expected_revision:snapshot.plan_revision,title:'Backup place',category:'place',required:false,options:[]}});expect(created.ok()).toBeTruthy();const updated=await created.json();const backup=updated.decisions.find((d:{title:string})=>d.title==='Backup place');
 await page.goto('/plans/'+plan.id);await page.getByRole('tab',{name:'Chat',exact:true}).click();await page.getByRole('button',{name:'Find options',exact:true}).click();const dialog=page.getByRole('dialog');await dialog.getByLabel('Decision',{exact:true}).selectOption(place.id);await dialog.getByLabel('What are you looking for?',{exact:true}).fill('Quiet dinner');await dialog.getByLabel('Search location',{exact:true}).fill('Austin');
 let release!:()=>void,received!:()=>void;const held=new Promise<void>(resolve=>{release=resolve;}),started=new Promise<void>(resolve=>{received=resolve;});
 await page.route('**/research',async route=>{received();await held;await route.fulfill({json:{plan_id:plan.id,plan_revision:updated.plan_revision,query:'Quiet dinner',sources:[],options:[{id:'late',name:'Old target venue',details:'Wrong target',url:'https://example.com/old',source_ids:[]}],steps:[],context_truncated:false}}).catch(()=>{});});
 await dialog.getByRole('button',{name:'Search with group context',exact:true}).click();await started;await dialog.getByLabel('Decision',{exact:true}).selectOption(backup.id);release();await expect(dialog.getByRole('button',{name:'Search with group context',exact:true})).toBeEnabled();await expect(dialog.getByText('Old target venue',{exact:true})).toHaveCount(0);
});
