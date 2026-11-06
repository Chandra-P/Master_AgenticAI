import {test,expect} from '@playwright/test';
test('chat makes the honest reservation demo discoverable without sending the draft',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.goto('/');await page.getByRole('link',{name:'Open Coastal weekend'}).click();
 await page.getByLabel('Message your group').fill('private unsent draft');
 await page.getByRole('button',{name:'Try demo restaurant booking'}).click();
 await expect(page.getByRole('tab',{name:'Demo bookings'})).toHaveAttribute('aria-selected','true');
 await expect(page.getByText('Demo reservation—no real booking or charge',{exact:true})).toBeVisible();
 await expect(page.getByText('Sign in to a shared plan to run the restaurant MCP demo.')).toBeVisible();
 await expect(page.getByRole('button',{name:'Confirm demo reservation',exact:true})).toHaveCount(0);
});

test('members can explore while booking waits for agreement and owner review',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 const user={id:'owner',email:'owner@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
 const plan={id:'booking-flow',title:'Dinner together',kind:'outing',location:'Austin',date:'May 14',start:'2027-05-14',end:'2027-05-14',budget:100,image:'/images/restaurant.jpg',members:[{name:'Owner',color:'#6366f1',user_id:user.id}],messages:[],preferences:[],polls:[],itinerary:[],tasks:[],revision:1,owner_id:user.id,role:'owner'};
 let resolved=false,approved=false,confirmCalls=0,firstList=true;
 let releaseList:()=>void=()=>{};const listGate=new Promise<void>(resolve=>{releaseList=resolve;});
 const readiness=()=>({ready:resolved&&approved,approved,can_approve:resolved&&!approved,decisions:[{question:'Dinner choice?',option:'Fictional Lantern'}],blockers:resolved?[]:[{label:'Complete the date poll',tab:'Polls'}]});
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true}}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-owner',refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user}}));
 await page.route('**/api/backend/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/demo-bookings')&&firstList){firstList=false;await listGate;}
  if(path.endsWith('/demo-bookings/confirm'))confirmCalls++;
  if(path.endsWith('/demo-bookings/approve')){expect(route.request().postDataJSON()).toEqual({confirmed:true,expected_revision:1});approved=true;}
  const json=path.endsWith('/me')?{id:user.id,email:user.email,name:'Owner',workspace_mode:'member'}:path.endsWith('/coordination')?{plan_id:plan.id,plan_revision:1,status:'WAITING_FOR_VOTES',health:40,next_step:'Resolve votes',reason:'Waiting for votes.',target_tab:'Polls',summary:'Working plan.',decisions_made:[],open_questions:[],provider_status:'unavailable'}:path.endsWith('/plans')?[plan]:path.endsWith('/demo-bookings')?{simulation:true,bookings:[],readiness:readiness()}:path.endsWith('/approve')?{simulation:true,readiness:readiness()}:path.endsWith('/search')?{simulation:true,restaurants:[{id:'demo-lantern',name:'Fictional Lantern',city:'Austin',description:'Demo',times:['19:00']}],trace:[]}:path.endsWith('/quote')?{simulation:true,quote:{id:'quote',restaurant_name:'Fictional Lantern',city:'Austin',date:plan.start,time:'19:00',party_size:1,expires_at:'2099-01-01T00:00:00Z',estimated_total:35,currency:'USD'},trace:[]}:[];
  return route.fulfill({json});
 });
 await page.goto('/account');await page.getByLabel('Email address').fill(user.email);await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await page.goto('/plans/'+plan.id+'?tab=Demo%20bookings');
 await expect(page.getByRole('heading',{name:'Before you reserve',exact:true})).toBeVisible();
 await page.getByLabel('Demo city',{exact:true}).fill('Austin downtown');releaseList();
 await expect(page.getByRole('link',{name:'Complete the date poll'})).toHaveAttribute('href','/plans/booking-flow?tab=Polls');
 await page.getByRole('complementary',{name:'Reservation progress'}).screenshot({path:'test-results/flow-agreement-'+test.info().project.name+'.png'});
 await page.getByRole('link',{name:'Complete the date poll'}).click();
 await expect(page.getByRole('tab',{name:'Polls 0',exact:true})).toHaveAttribute('aria-selected','true');
 await page.getByRole('link',{name:'Review group decisions',exact:true}).click();
 await expect(page.getByRole('tab',{name:'Demo bookings',exact:true})).toHaveAttribute('aria-selected','true');
 await page.getByRole('button',{name:'Search fictional restaurants',exact:true}).click();await page.getByRole('combobox',{name:'Restaurant',exact:true}).selectOption('demo-lantern');await page.getByRole('button',{name:'Review demo reservation',exact:true}).click();
 await expect(page.getByRole('button',{name:'Confirm demo reservation',exact:true})).toBeDisabled();
 expect(confirmCalls).toBe(0);
 resolved=true;await page.reload();
 await expect(page.getByRole('listitem').filter({hasText:'Dinner choice?'})).toContainText('Fictional Lantern');
 await page.getByRole('button',{name:'Approve group decisions',exact:true}).click();
 await expect(page.getByText('Group decisions approved. You can confirm a reservation.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Search fictional restaurants',exact:true}).click();await page.getByRole('combobox',{name:'Restaurant',exact:true}).selectOption('demo-lantern');await page.getByRole('button',{name:'Review demo reservation',exact:true}).click();
 await expect(page.getByRole('button',{name:'Confirm demo reservation',exact:true})).toBeEnabled();
});
