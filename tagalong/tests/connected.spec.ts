import {test, expect} from '@playwright/test';

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
