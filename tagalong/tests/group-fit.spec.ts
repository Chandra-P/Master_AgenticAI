import {openTool} from './planning-tools';
import {test,expect,type Page} from '@playwright/test';

async function setup(page:Page,hold=false){
 const user={id:'fit-owner',email:'fit@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'};
 const plan={id:'fit-plan',title:'Dinner with friends',kind:'outing',location:'Austin',date:'May 14',start:'2027-05-14',end:'2027-05-14',budget:40,image:'/images/restaurant.jpg',members:[{name:'Owner',color:'#6366f1',user_id:user.id}],messages:[],preferences:[{label:'Vegetarian options',confirmed:true}],polls:[],itinerary:[],tasks:[],revision:3,owner_id:user.id,role:'owner'};
 let requests=0;let release:()=>void=()=>{};const gate=new Promise<void>(resolve=>{release=resolve;});
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','connected'));
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'https://tagalong-test.supabase.co',supabaseAnonKey:'test-key',connectedReady:true}}));
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-owner',refresh_token:'refresh',token_type:'bearer',expires_in:3600,user}}));
 await page.route('**/api/backend/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path.endsWith('/group-fit')){requests++;expect(route.request().postDataJSON().expected_revision).toBe(3);if(hold)await gate;await route.fulfill({json:{verdict:'conflicts',summary:'This dinner exceeds the working budget.',matches:[{text:'Vegetarian dishes are listed.',source_ids:['menu']}],conflicts:[{text:'The estimate is above the group budget.',source_ids:['plan-facts']}],unknowns:['Confirm current availability directly with the venue.'],sources:[{id:'menu',title:'Saved menu',text:'Vegetarian dinner costs $55 per person.',retrieval_origin:'pinecone'},{id:'plan-facts',title:'Current plan facts',text:'Budget per person: $40.',retrieval_origin:'postgres'}],retrieval_status:'available',context_truncated:true}}).catch(()=>{});return;}
  const json=path.endsWith('/me')?{id:user.id,email:user.email,name:'Owner',workspace_mode:'member'}:path.endsWith('/plans')?[plan]:path.endsWith('/coordination')?{plan_id:plan.id,plan_revision:3,status:'ACTIVE',health:30,next_step:'Review plan',reason:'Working plan.',target_tab:'Planning board',summary:'Working plan.',decisions_made:[],open_questions:[],provider_status:'unavailable'}:[];
  await route.fulfill({json});
 });
 await page.goto('/account');await page.getByLabel('Email address').fill(user.email);await page.getByLabel('Password',{exact:true}).fill('test-password-123');await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await page.goto('/plans/'+plan.id+'?tab=Group%20fit');
 return {release,requests:()=>requests};
}

test('group fit shows sourced conflicts and uncertainty without saving an activity',async({page})=>{
 const state=await setup(page);
 await page.getByLabel('Option name',{exact:true}).fill('Dinner option');await page.getByLabel('Option details or menu',{exact:true}).fill('Vegetarian dinner, $55 each.');await page.getByLabel('Estimated cost per person',{exact:true}).fill('55');
 await page.getByRole('button',{name:'Check group fit',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Conflicts with the group',exact:true})).toBeVisible();
 await page.getByText('Review findings · 3',{exact:true}).click();
 await expect(page.getByText('The estimate is above the group budget.',{exact:true})).toBeVisible();
  await expect(page.getByText('Pinecone RAG · 1 source',{exact:true})).toBeVisible();
  await expect(page.getByText('OpenAI group-fit check',{exact:true})).toBeVisible();
 await page.getByRole('link',{name:/Evidence 1:/}).click();
 await expect(page.getByText('Vegetarian dinner costs $55 per person.',{exact:true})).toBeVisible();
 await expect(page.getByText(/Only selected evidence excerpts/)).toBeVisible();
 await page.locator('.group-fit-panel').screenshot({path:'test-results/group-fit-'+test.info().project.name+'.png'});
 expect(state.requests()).toBe(1);
 await page.getByRole('tab',{name:'Itinerary',exact:true}).click();await expect(page.getByText('Dinner option',{exact:true})).toHaveCount(0);
});

test('editing a pending option prevents its old group-fit response from appearing',async({page})=>{
 const state=await setup(page,true);await page.getByLabel('Option name',{exact:true}).fill('Old option');await page.getByRole('button',{name:'Check group fit',exact:true}).click();await expect.poll(state.requests).toBe(1);
 await page.getByLabel('Option name',{exact:true}).fill('New option');state.release();
 await expect(page.getByText('This dinner exceeds the working budget.',{exact:true})).toHaveCount(0);
 await expect(page.getByLabel('Option name',{exact:true})).toHaveValue('New option');
});

test('demo group fit explains that shared sources require sign-in',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));await page.goto('/');await page.getByRole('link',{name:'Open Coastal weekend'}).click();await openTool(page,'Group fit');await expect(page.getByText('Sign in to a shared plan to check an option against your group’s sources. Open your account',{exact:true})).toBeVisible();await expect(page.locator('.group-fit-panel').getByRole('link',{name:'Open your account',exact:true})).toHaveAttribute('href','/account');await expect(page.getByRole('button',{name:'Check group fit',exact:true})).toHaveCount(0);
});

test('missing evidence remains an uncertain result rather than a recommendation',async({page})=>{
 await setup(page);await page.route('**/api/backend/v1/plans/fit-plan/group-fit',route=>route.fulfill({json:{verdict:'needs_info',summary:'There is not enough evidence to recommend this option.',matches:[],conflicts:[],unknowns:['Add a current menu and confirm member constraints.'],sources:[],retrieval_status:'unavailable',context_truncated:false}}));
 await page.getByLabel('Option name',{exact:true}).fill('An unverified option');await page.getByRole('button',{name:'Check group fit',exact:true}).click();
 await expect(page.getByRole('heading',{name:'More information needed',exact:true})).toBeVisible();await expect(page.getByText('No group evidence found. Add a Note or option details.',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:/Source:/})).toHaveCount(0);
});

test('a discovered place opens a prefilled group-fit check before any action is saved',async({page})=>{
 const state=await setup(page);await page.route('**/api/backend/v1/places/search',route=>route.fulfill({json:{provider:'Synthetic public fixture',notice:'Unverified source information.',results:[{id:'fit-place',kind:'place',title:'Fixture Cafe',url:'https://venue.example.test/menu',snippet:'Vegetarian dinner menu.',address:'10 Test Street',location:'Austin',category:'Food & drink',image:null,image_source_url:null,map_url:'https://www.google.com/maps/search/?api=1&query=Fixture+Cafe'}]}}));
 await openTool(page,'Discover');await page.getByLabel('Looking for').fill('Dinner');await page.getByRole('button',{name:'Update',exact:true}).click();await page.getByRole('button',{name:'Check group fit for Fixture Cafe',exact:true}).click();
 const dialog=page.getByRole('dialog');await expect(dialog.getByLabel('Option name',{exact:true})).toHaveValue('Fixture Cafe');await expect(dialog.getByLabel('Option details or menu',{exact:true})).toHaveValue('Vegetarian dinner menu.\n10 Test Street');await expect(dialog.getByLabel('Option website (optional)',{exact:true})).toHaveValue('https://venue.example.test/menu');expect(state.requests()).toBe(0);
});
