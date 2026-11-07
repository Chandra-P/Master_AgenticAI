import {test,expect,type Page} from '@playwright/test';
import {inspectVisual} from './ui-refresh.helpers';

async function login(page:Page,admin=false){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-alice',refresh_token:'refresh-alice',token_type:'bearer',expires_in:3600,user:{id:'alice',email:'alice@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByRole('radio',{name:admin?'Admin':'Member',exact:true}).check();
 await page.getByLabel('Email address').fill('alice@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}

test('account and recovery screens follow the visual system at all widths',async({page},info)=>{
 test.skip(info.project.name!=='desktop');test.setTimeout(120000);
 for(const width of [1440,1024,390]){
  await page.setViewportSize({width,height:1000});await page.goto('/account');await expect(page.getByLabel('Email address')).toBeVisible();
  await inspectVisual(page,info,`${width}-sign-in`);
  await page.getByRole('radio',{name:'Admin',exact:true}).check();await inspectVisual(page,info,`${width}-admin-sign-in`);
  await page.getByRole('button',{name:'New here? Create an account',exact:true}).click();await inspectVisual(page,info,`${width}-sign-up`);
  await page.getByRole('button',{name:'Already have an account? Sign in',exact:true}).click();
  await page.getByRole('button',{name:'Forgot password?',exact:true}).click();await inspectVisual(page,info,`${width}-reset-request`);
  await page.getByRole('button',{name:'Back to sign in',exact:true}).click();
 }
 await page.goto('/account#error=access_denied&error_code=otp_expired&error_description=Expired&type=recovery');await page.reload();
 await expect(page.getByText('This recovery link is invalid or expired. Request a new one.',{exact:true})).toBeVisible();
 await inspectVisual(page,info,'390-expired-recovery');
});

test('connected tools, expanded evidence and owner dialogs adapt across screen sizes',async({page},info)=>{
 test.skip(info.project.name!=='desktop');test.setTimeout(180000);await login(page);
 await page.route('https://places.example.test/**',route=>route.fulfill({status:404,body:''}));
 const headers={Authorization:'Bearer test-alice'};
 const result=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Visual review weekend',kind:'trip',start:'2027-05-14',end:'2027-05-16'}});expect(result.ok()).toBeTruthy();const plan=await result.json();
 expect((await page.request.patch('/api/backend/v1/plans/'+plan.id,{headers,data:{expected_revision:plan.revision,patches:[{op:'replace',path:['location'],value:'Austin'}]}})).ok()).toBeTruthy();
 for(const width of [1440,1024,390]){
  await page.setViewportSize({width,height:1000});
  for(const path of ['/','/groups','/itinerary','/join','/account']){await page.goto(path);await expect(page.locator('.app-shell')).toBeVisible();await inspectVisual(page,info,`${width}-connected-${path.replaceAll('/','-')}`);}
  await page.goto('/');await page.getByLabel('Describe your plan',{exact:true}).fill('A relaxed Austin weekend with four friends');
  await page.getByRole('button',{name:'Start Planning',exact:true}).click();await expect(page.getByRole('region',{name:'Review AI plan draft',exact:true})).toBeVisible();await page.getByRole('region',{name:'Review AI plan draft',exact:true}).scrollIntoViewIfNeeded();
  await inspectVisual(page,info,`${width}-generated-review`);
  await page.goto('/plans/'+plan.id);
  for(const name of ['Decisions','Chat','Planning board','Polls','Discover','Itinerary','Documents','Demo bookings','Group fit']){
   await page.getByRole('tab',{name,exact:name!=='Polls'}).click();
   if(name==='Discover')await expect(page.getByRole('heading',{name:'Synthetic vegetarian restaurant',exact:true})).toBeVisible();
   await inspectVisual(page,info,`${width}-connected-${name.replaceAll(' ','-')}`);
  }
  await page.getByRole('tab',{name:'Discover',exact:true}).click();await page.getByRole('button',{name:'Add Synthetic vegetarian restaurant to plan',exact:true}).click();
  await inspectVisual(page,info,`${width}-place-dialog`);await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Check group fit for Synthetic vegetarian restaurant',exact:true}).click();await inspectVisual(page,info,`${width}-venue-fit-dialog`);await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Add member',exact:true}).click();await inspectVisual(page,info,`${width}-member-dialog`);await page.keyboard.press('Escape');
  for(const name of ['Transfer ownership','Delete plan']){await page.getByRole('button',{name,exact:true}).click();await inspectVisual(page,info,`${width}-${name.replaceAll(' ','-')}`);await page.keyboard.press('Escape');}
 }
 await page.getByRole('tab',{name:'Documents',exact:true}).click();await page.getByLabel('Document title',{exact:true}).fill('Synthetic venue note');
 await page.getByLabel('Document text',{exact:true}).fill('Synthetic adult group prefers a relaxed vegetarian dinner.');await page.getByRole('button',{name:'Save document',exact:true}).click();
 await page.getByText('Synthetic venue note',{exact:true}).click();await inspectVisual(page,info,'390-expanded-note');
 await page.getByRole('tab',{name:'Group fit',exact:true}).click();await page.getByLabel('Option name',{exact:true}).fill('Synthetic dinner');
 await page.getByLabel('Option details or menu',{exact:true}).fill('A synthetic vegetarian menu.');await page.getByRole('button',{name:'Check group fit',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Sources used',exact:true})).toBeVisible();await inspectVisual(page,info,'390-fit-result');
 await page.getByRole('button',{name:/^Source:/}).first().click();await inspectVisual(page,info,'390-fit-source');
});

test('admin overview, private review and story replay stay readable',async({page},info)=>{
 test.skip(info.project.name!=='desktop');test.setTimeout(120000);await login(page,true);
 for(const width of [1440,1024,390]){
  await page.setViewportSize({width,height:1000});await page.goto('/admin');await expect(page.getByRole('heading',{name:'Review overview',exact:true})).toBeVisible();
  await inspectVisual(page,info,`${width}-admin`);
  await page.getByRole('button',{name:'Create QA review plans',exact:true}).click();
  await page.getByLabel('Reason for admin action',{exact:true}).fill('Synthetic visual review');
  await page.getByRole('button',{name:/^Review private plan:/}).first().click();
  await expect(page.getByRole('region',{name:'Private plan review',exact:true})).toBeVisible();await page.getByRole('region',{name:'Private plan review',exact:true}).scrollIntoViewIfNeeded();
  await inspectVisual(page,info,`${width}-private-admin-review`);
  await page.getByRole('button',{name:'Close private review',exact:true}).click();
  await page.getByRole('button',{name:/^Open story:/}).first().click();await expect(page.getByRole('region',{name:'Demo story replay',exact:true})).toBeVisible();await page.getByRole('region',{name:'Demo story replay',exact:true}).scrollIntoViewIfNeeded();await inspectVisual(page,info,`${width}-story`);
  await page.getByRole('button',{name:'Show complete conversation',exact:true}).click();await inspectVisual(page,info,`${width}-full-story`);
 }
});

test('verified password recovery form is readable without loading private plans',async({page},info)=>{
 test.skip(info.project.name!=='desktop');
 const user={id:'visual-recovery',email:'person@example.test',aud:'authenticated',role:'authenticated',user_metadata:{},app_metadata:{provider:'email'},created_at:'2026-01-01T00:00:00Z'};
 const token=[{alg:'HS256',typ:'JWT'},{sub:user.id,exp:Math.floor(Date.now()/1000)+3600,iat:Math.floor(Date.now()/1000),role:'authenticated'}].map(value=>Buffer.from(JSON.stringify(value)).toString('base64url')).join('.')+'.'+Buffer.from('synthetic').toString('base64url');
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:user}));
 let reads=0;await page.route('**/api/backend/**',route=>{reads++;return route.fulfill({status:401,json:{detail:'No planning access during recovery'}});});
 await page.goto('/account#access_token='+token+'&refresh_token=synthetic&expires_in=3600&token_type=bearer&type=recovery');
 await expect(page.getByLabel('New password',{exact:true})).toBeVisible();
 for(const width of [1440,1024,390]){await page.setViewportSize({width,height:1000});await inspectVisual(page,info,`${width}-verified-recovery`);}
 expect(reads).toBe(0);
});
