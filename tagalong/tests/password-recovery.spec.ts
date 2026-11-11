import {test,expect} from '@playwright/test';

const config={supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true};
test('reset rate limits explain when to retry without revealing provider details',async({page})=>{
 await page.route('**/api/config',route=>route.fulfill({json:config}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/recover**',route=>route.fulfill({status:429,headers:{'X-Supabase-Api-Version':'2024-01-01','Access-Control-Expose-Headers':'X-Supabase-Api-Version'},json:{code:'over_email_send_rate_limit',msg:'sensitive provider diagnostic'}}));
 await page.goto('/account');await page.getByRole('button',{name:'Forgot password?',exact:true}).click();
 await page.getByLabel('Recovery email address').fill('person@example.test');await page.getByRole('button',{name:'Send reset email',exact:true}).click();
 await expect(page.getByRole('alert').filter({hasText:'The email limit has been reached.'})).toHaveText('The email limit has been reached. Use the most recent reset email if one arrived, or wait an hour before requesting another.');
 await expect(page.getByText('sensitive provider diagnostic')).toHaveCount(0);
});
test('forgot password does not display an unrelated shared workspace failure',async({page})=>{
 const user={id:'reset-test',email:'person@example.test',aud:'authenticated',role:'authenticated',app_metadata:{},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
 await page.route('**/api/config',route=>route.fulfill({json:config}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-reset',refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user}}));
 await page.route('**/api/backend/**',route=>route.fulfill({status:503,json:{detail:'Shared workspace is temporarily unavailable. Please wait a moment and try again.'}}));
 await page.goto('/account');await page.getByLabel('Email address').fill(user.email);await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('alert').filter({hasText:'Shared workspace is temporarily unavailable. Please wait a moment and try again.'})).toBeVisible();
 await page.getByRole('button',{name:'Forgot password?',exact:true}).click();
 await expect(page.getByRole('alert').filter({hasText:'Shared workspace is temporarily unavailable. Please wait a moment and try again.'})).toHaveCount(0);
});
test('forgot password sends a recovery request with the existing account redirect',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 await page.route('**/api/config',route=>route.fulfill({json:config}));
 let payload:Record<string,unknown>={};let recoveryUrl='';
 await page.route('https://tagalong-test.supabase.co/auth/v1/recover**',route=>{payload=route.request().postDataJSON();recoveryUrl=route.request().url();return route.fulfill({json:{}});});
 await page.goto('/account');await page.getByRole('button',{name:'Forgot password?',exact:true}).click();
 await page.getByLabel('Recovery email address').fill('person@example.test');await page.getByRole('button',{name:'Send reset email',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'If an account exists'})).toBeVisible();
 expect(payload.email).toBe('person@example.test');expect(new URL(recoveryUrl).searchParams.get('redirect_to')).toBe('http://127.0.0.1:3100/account');
});

test('recovery link changes the password without loading plans or restoring admin mode',async({page})=>{
 const user={id:'recovery-test',email:'person@example.test',aud:'authenticated',role:'authenticated',user_metadata:{},app_metadata:{provider:'email'},created_at:'2026-01-01T00:00:00Z'};
 const token=[{alg:'HS256',typ:'JWT'},{sub:user.id,exp:Math.floor(Date.now()/1000)+3600,iat:Math.floor(Date.now()/1000),role:'authenticated'}].map(x=>Buffer.from(JSON.stringify(x)).toString('base64url')).join('.')+'.'+Buffer.from('synthetic').toString('base64url');
 await page.addInitScript(()=>{localStorage.setItem('tagalong-workspace-mode','connected');sessionStorage.setItem('tagalong-access-mode',JSON.stringify({userId:'recovery-test',role:'admin'}));});
 await page.route('**/api/config',route=>route.fulfill({json:config}));
 let updates=0;let newPassword='';let privateReads=0;
 await page.route('**/api/backend/**',route=>{privateReads++;return route.fulfill({status:401,json:{detail:'No planning calls during recovery'}});});
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>{if(route.request().method()==='PUT'){updates++;newPassword=route.request().postDataJSON().password;}return route.fulfill({json:route.request().url().includes('/logout')?{}:user});});
 await page.goto('/account#access_token='+token+'&refresh_token=synthetic-refresh&expires_in=3600&token_type=bearer&type=recovery');
 await expect(page.getByRole('heading',{name:'Choose a new password',exact:true})).toBeVisible();
 await page.reload();await expect(page.getByLabel('New password',{exact:true})).toBeVisible();
 await page.getByLabel('New password',{exact:true}).fill('new-synthetic-password-123');await page.getByLabel('Confirm new password').fill('different-password-123');
 await expect(page.getByRole('button',{name:'Save new password',exact:true})).toBeDisabled();expect(updates).toBe(0);
 await page.getByLabel('Confirm new password').fill('new-synthetic-password-123');await page.getByRole('button',{name:'Save new password',exact:true}).click();
 await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
 expect(updates).toBe(1);expect(newPassword).toBe('new-synthetic-password-123');expect(privateReads).toBe(0);
 expect(await page.evaluate(()=>sessionStorage.getItem('tagalong-access-mode'))).toBeNull();
 expect(page.url()).not.toContain('access_token');
});

test('expired recovery links offer another reset email and never allow a password update',async({page})=>{
 await page.route('**/api/config',route=>route.fulfill({json:config}));
 await page.goto('/account#error=access_denied&error_code=otp_expired&error_description=Expired&type=recovery');
 await expect(page.getByText('This recovery link is invalid or expired. Request a new one.',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Save new password',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Request a new reset link',exact:true})).toBeVisible();
});

test('recovery with unavailable authentication shows an actionable error',async({page})=>{
 await page.route('**/api/config',route=>route.fulfill({json:{...config,connectedReady:false}}));
 await page.goto('/account#type=recovery');
 await expect(page.getByText('Password recovery is unavailable. Please reload or try again later.',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Save new password',exact:true})).toHaveCount(0);
});

