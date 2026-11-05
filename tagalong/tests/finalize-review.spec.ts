import {test,expect} from '@playwright/test';

test('ready next step opens an honest review and navigates to the itinerary without saving',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 const user={id:'reviewer',email:'reviewer@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
 const plan={id:'review-plan',title:'Ready weekend',kind:'trip',location:'Austin',date:'May 14',start:'2027-05-14',end:'2027-05-16',budget:350,image:'/images/coast.jpg',members:[{name:'Reviewer',color:'#6366f1',user_id:user.id}],messages:[],preferences:[],polls:[{id:'poll',question:'Dinner choice?',options:['Tacos','Pizza'],votes:{Reviewer:0}}],itinerary:[{id:'dinner',title:'Taco dinner',day:'2027-05-15',time:'19:00',category:'Food',location:'Austin'}],tasks:[{label:'Check opening hours',done:true}],revision:1,owner_id:user.id,role:'member'};
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-publishable-key',connectedReady:true}}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-review',refresh_token:'test-refresh',token_type:'bearer',expires_in:3600,user}}));
 await page.route('**/api/backend/v1/**',route=>{
  const path=new URL(route.request().url()).pathname;
  const json=path.endsWith('/me')?{id:user.id,email:user.email,name:'Reviewer',workspace_mode:'member'}:path.endsWith('/coordination')?{plan_id:plan.id,plan_revision:1,status:'READY_TO_FINALIZE',health:100,next_step:'Review your plan',reason:'All working details are filled.',target_tab:'Planning board',summary:'Ready for review.',decisions_made:[],open_questions:[],provider_status:'unavailable'}:path.endsWith('/plans')?[plan]:[];
  return route.fulfill({json});
 });
 await page.goto('/account');await page.getByLabel('Email address').fill(user.email);await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await page.goto('/plans/'+plan.id+'?tab=Planning%20board');
 const mutations:string[]=[];page.on('request',request=>{if(request.url().includes('/api/backend/')&&request.method()!=='GET')mutations.push(request.method()+' '+request.url());});
 await page.getByRole('button',{name:'View final itinerary',exact:false}).click();
 const review=page.getByRole('dialog',{name:'Here is your final itinerary'});
 await expect(review).toBeVisible();
 await review.screenshot({path:'test-results/final-itinerary-'+test.info().project.name+'.png'});
 await expect(review).toContainText('2027-05-14 – 2027-05-16');
 await expect(review).toContainText('Austin');await expect(review).toContainText('$350 per person');
 await expect(review).toContainText('19:00 · Taco dinner');await expect(review.getByRole('region',{name:'Itinerary for 2027-05-15'})).toBeVisible();await expect(review).toContainText('Check opening hours');
 await expect(review.getByRole('heading',{name:'What to do next',exact:true})).toBeVisible();
 await expect(review).toContainText('Confirm any reservations directly with the venue');
 await expect(review).toContainText('Arrange transport between activities');
 await expect(review).toContainText('Tacos: 1 vote');await expect(review).toContainText('Ready for review. Nothing is booked.');
 await review.getByRole('button',{name:'View full itinerary',exact:true}).click();
 await expect(review).toHaveCount(0);await expect(page.getByRole('tab',{name:'Itinerary',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(page.getByRole('heading',{name:'Taco dinner',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'View final itinerary',exact:false}).click();
 await page.getByRole('dialog').getByRole('button',{name:'Finish review',exact:true}).click();
 await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.getByRole('status').filter({hasText:'Review finished'})).toBeVisible();
 expect(mutations).toEqual([]);
});

