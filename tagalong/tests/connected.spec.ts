import {test, expect} from '@playwright/test';

test('home greeting uses preferred display name instead of internal identity',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 const user={id:'greeting-test',email:'person@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{display_name:'Chandra'},created_at:'2026-01-01T00:00:00Z'};
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true}}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-greeting',refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user}}));
 await page.route('**/api/backend/v1/me',route=>route.fulfill({json:{id:user.id,email:user.email,name:'internal-identity-123',display_name:'Chandra',workspace_mode:'member'}}));
 await page.route('**/api/backend/v1/plans',route=>route.fulfill({json:[{id:'greeting-plan',title:'Personal plan',kind:'outing',location:'To decide',date:'Dec 12',start:'2026-12-12',end:'2026-12-12',budget:0,image:'/images/restaurant.jpg',members:[{name:'Chandra',color:'#6366f1',user_id:user.id}],messages:[],preferences:[],polls:[],itinerary:[],tasks:[],revision:1,owner_id:user.id,role:'owner'}]}));
 await page.goto('/account');await page.getByLabel('Email address').fill(user.email);await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();await page.goto('/');
 await expect(page.getByRole('heading',{name:/Hey Chandra, let/})).toBeVisible();
 await expect(page.getByRole('heading',{name:/internal-identity/})).toHaveCount(0);
});

test('sign out wins over a delayed admin-mode switch',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 const user={id:'role-test',email:'role@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true}}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-role',refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user}}));
 const me={id:user.id,email:user.email,name:'role',app_admin:true,workspace_mode:'member'};
 await page.route('**/api/backend/v1/me',route=>route.fulfill({json:me}));
 await page.route('**/api/backend/v1/plans',route=>route.fulfill({json:[]}));
 await page.goto('/account');await page.getByLabel('Email address').fill(user.email);await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('button',{name:'Switch to Admin',exact:true})).toBeVisible();
 let release:()=>void=()=>{};let started:()=>void=()=>{};
 const blocked=new Promise<void>(resolve=>{release=resolve;});const waiting=new Promise<void>(resolve=>{started=resolve;});
 await page.route('**/api/backend/v1/me',async route=>{started();await blocked;await route.fulfill({json:me});});
 await page.getByRole('button',{name:'Switch to Admin',exact:true}).click();await waiting;
 await page.getByRole('button',{name:'Sign out',exact:true}).click();release();
 await page.waitForLoadState('networkidle');
 await expect(page.getByLabel('Email address')).toBeVisible();
 expect(await page.evaluate(()=>sessionStorage.getItem('tagalong-access-mode'))).toBeNull();
});

test('suspension clears an already loaded account when refresh denies access',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 const user={id:'suspended-test',email:'account@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true}}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-suspension',refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user}}));
 let suspended=false;
 await page.route('**/api/backend/v1/me',route=>suspended?route.fulfill({status:403,json:{detail:'Account suspended. Contact the app administrator.'}}):route.fulfill({json:{id:user.id,email:user.email,name:'account'}}));
 await page.route('**/api/backend/v1/plans',route=>route.fulfill({json:[]}));
 await page.goto('/account');await page.getByLabel('Email address').fill(user.email);await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 suspended=true;await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await expect(page.getByLabel('Email address')).toBeVisible();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toHaveCount(0);
});

test('signup asks for a preferred display name and sends it as profile metadata',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true}}));
 let submitted:Record<string,unknown>={};
 await page.route('https://tagalong-test.supabase.co/auth/v1/signup',route=>{submitted=route.request().postDataJSON();return route.fulfill({json:{user:{id:'signup-user',email:'new@example.test',user_metadata:{display_name:'Sunny'}},session:null}});});
 await page.goto('/account');
 await page.getByRole('button',{name:'New here? Create an account'}).click();
 await page.getByLabel('Preferred display name').fill('Sunny');
 await page.getByLabel('Email address').fill('new@example.test');
 await page.getByLabel('Password',{exact:true}).fill('test-password-123');
 await page.getByRole('button',{name:'Create account',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'Check your email'})).toBeVisible();
 expect(submitted.data).toEqual({display_name:'Sunny'});
});

test('configuration fetch failure never substitutes demo data for a shared workspace',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 await page.route('**/api/config',route=>route.fulfill({status:503,json:{detail:'Unavailable'}}));
 await page.goto('/');
 await expect(page.getByText('Could not load app configuration. Please reload.',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Open Coastal weekend'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Explore the demo'})).toHaveCount(0);
});

test('connected mode explains missing setup and never shows demo plans as shared data', async ({page}) => {
  await page.route('**/api/config', route => route.fulfill({json:{supabaseUrl:'',supabaseAnonKey:'',connectedReady:false}}));
  await page.goto('/account');
  await page.getByRole('button', {name:'Use shared workspace'}).click();
  await expect(page.getByText('Shared workspace needs Supabase and the API configuration.')).toBeVisible();
  await expect(page.getByRole('link',{name:'Open Coastal weekend'})).toHaveCount(0);
  await page.reload();
  await expect(page.getByText('Shared workspace needs Supabase and the API configuration.')).toBeVisible();
  await page.getByRole('button',{name:'Explore the demo'}).click();
  await page.goto('/');
  await expect(page.getByRole('link',{name:'Open Coastal weekend'})).toBeVisible();
});

test('sign in loads shared plans and service errors remain visible', async ({page}) => {
  await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
  const id='00000000-0000-4000-8000-000000000001';
  const user={id,email:'alex@example.com',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
  await page.route('**/api/config', route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true}}));
  await page.route('https://tagalong-test.supabase.co/auth/v1/**', route=>route.fulfill({json:{access_token:'test-token',refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user}}));
  await page.route('**/api/backend/v1/me', route=>route.fulfill({json:{id,email:user.email,name:'alex-00000000'}}));
  await page.route('**/api/backend/v1/plans', route=>route.fulfill({status:503,json:{detail:'Shared plans are temporarily unavailable.'}}));
  await page.goto('/account');
  await page.getByRole('button',{name:'Use shared workspace'}).click();
  await page.getByLabel('Email address').fill(user.email);
  await page.getByLabel('Password', {exact:true}).fill('a-test-password-123');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByText('Shared plans are temporarily unavailable.',{exact:true}).first()).toBeVisible();
  await expect(page.getByRole('link',{name:'Open Coastal weekend'})).toHaveCount(0);
});
