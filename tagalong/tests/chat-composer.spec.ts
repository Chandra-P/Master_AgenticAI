import {test,expect,type Page} from '@playwright/test';

test('typing help explains local suggestions and hides completions while editing mid-draft',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.goto('/');
 await page.getByRole('link',{name:'Open Coastal weekend'}).click();
 const draft=page.getByLabel('Message your group');
 await expect(page.getByText('Try “Let” or a planning word. Suggestions stay on this device.',{exact:true})).toBeVisible();
 await draft.fill('Let');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toBeVisible();
 await draft.press('ArrowLeft');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toHaveCount(0);
 await draft.press('End');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toBeVisible();
 await page.getByRole('button',{name:/Accept suggestion/}).click();
 await expect(draft).toHaveValue("Let's plan ");
 await expect(draft).toBeFocused();
});

async function connectedChat(page:Page,onSuggestion:(draft:string,revision:number)=>Promise<string>){
 const user={id:'typing-owner',email:'typing@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
 const plan={id:'typing-plan',title:'Typing model plan',kind:'outing',location:'Austin',date:'May 14',start:'2027-05-14',end:'2027-05-14',budget:100,image:'/images/restaurant.jpg',members:[{name:'Owner',color:'#6366f1',user_id:user.id}],messages:[],preferences:[],polls:[],itinerary:[],tasks:[],revision:7,owner_id:user.id,role:'owner'};
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-key',connectedReady:true}}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-owner',refresh_token:'refresh',token_type:'bearer',expires_in:3600,user}}));
 await page.route('**/api/backend/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/typing-suggestion')){
   const body=route.request().postDataJSON();
   const suggestion=await onSuggestion(body.draft,body.expected_revision);
   await route.fulfill({json:{suggestion,source:'model'}}).catch(()=>{});
   return;
  }
  const json=path.endsWith('/me')?{id:user.id,email:user.email,name:'Owner',workspace_mode:'member'}:path.endsWith('/plans')?[plan]:path.endsWith('/coordination')?{plan_id:plan.id,plan_revision:7,status:'ACTIVE',health:30,next_step:'Review plan',reason:'Working plan.',target_tab:'Planning board',summary:'Working plan.',decisions_made:[],open_questions:[],provider_status:'unavailable'}:[];
  await route.fulfill({json});
 });
 await page.goto('/account');
 await page.getByLabel('Email address').fill(user.email);
 await page.getByLabel('Password',{exact:true}).fill('test-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await page.goto('/plans/'+plan.id);
 return page.getByLabel('Message your group');
}

test('connected suggestions debounce, accept without sending, and stop when disabled or composing',async({page})=>{
 const requests:{draft:string;revision:number}[]=[];
 const draft=await connectedChat(page,async(text,revision)=>{requests.push({draft:text,revision});return ' together.';});
 await expect(page.getByText(/Uses OpenAI after a pause/)).toBeVisible();
 await draft.fill('I want to explore');
 await page.waitForTimeout(200);
 expect(requests).toHaveLength(0);
 await draft.fill('I want to explore more');
 await expect(page.getByRole('button',{name:'Accept suggestion: together.',exact:true})).toBeVisible();
 await page.locator('.chat-composer-wrap').screenshot({path:'test-results/typing-model-'+test.info().project.name+'.png'});
 await page.getByRole('button',{name:'Accept suggestion: together.',exact:true}).click();
 await expect(draft).toHaveValue('I want to explore more together.');
 await expect(page.locator('.chat-message')).toHaveCount(0);
 expect(requests).toEqual([{draft:'I want to explore more',revision:7}]);
 await page.getByLabel('Typing suggestions').uncheck();
 await draft.fill('Another draft while disabled');
 await page.waitForTimeout(850);
 expect(requests).toHaveLength(1);
 await page.getByLabel('Typing suggestions').check();
 await draft.dispatchEvent('compositionstart');
 await page.waitForTimeout(850);
 expect(requests).toHaveLength(1);
 await draft.dispatchEvent('compositionend');
 await expect(page.getByRole('button',{name:'Accept suggestion: together.',exact:true})).toBeVisible();
 expect(requests).toHaveLength(2);
});

test('late model completion cannot replace an edited draft or survive leaving the chat',async({page})=>{
 let release:()=>void=()=>{};
 const gate=new Promise<void>(resolve=>{release=resolve;});
 let firstRequested=false;
 const draft=await connectedChat(page,async text=>{
  if(text==='Original model draft'){firstRequested=true;await gate;return ' stale.';}
  return ' fresh.';
 });
 await draft.fill('Original model draft');
 await expect.poll(()=>firstRequested).toBe(true);
 await draft.fill('Changed model draft');
 await expect(page.getByRole('button',{name:'Accept suggestion: fresh.',exact:true})).toBeVisible();
 release();
 await expect(page.getByRole('button',{name:'Accept suggestion: stale.',exact:true})).toHaveCount(0);
 await expect(draft).toHaveValue('Changed model draft');
 await page.getByRole('link',{name:'All plans',exact:true}).click();
 await page.getByRole('link',{name:'Open Typing model plan',exact:true}).click();
 await expect(draft).toHaveValue('');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toHaveCount(0);
});
