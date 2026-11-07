import {test,expect} from '@playwright/test';
import {inspectVisual} from './ui-refresh.helpers';

test.beforeEach(async({page},info)=>{
 test.skip(info.project.name!=='desktop','The visual audit explicitly covers all three widths.');
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'',supabaseAnonKey:'',connectedReady:false}}));
});

test('every demo route, tool and responsive state has readable type and contrast',async({page},info)=>{
 test.setTimeout(180000);
 for(const width of [1440,1024,390]){
  await page.setViewportSize({width,height:1000});
  for(const route of ['/','/welcome','/discover','/itinerary','/groups','/account','/admin','/join','/plans/coastal-weekend','/plans/sunday-supper','/plans/into-the-pines','/plans/missing','/missing']){
   await page.goto(route);await expect(page.locator('.app-shell')).toBeVisible();
   await inspectVisual(page,info,`${width}-route-${route.replaceAll('/','-')}`);
  }
  await page.goto('/plans/coastal-weekend');
  for(const name of ['Decisions','Chat','Planning board','Polls','Discover','Itinerary','Documents','Demo bookings','Group fit']){
   await page.getByRole('tab',{name,exact:name!=='Polls'}).click();
   await inspectVisual(page,info,`${width}-tool-${name.replaceAll(' ','-')}`);
  }
  await page.goto('/discover');await page.getByLabel('Search ideas').fill('no matching idea');
  await expect(page.getByText('No ideas found just yet.')).toBeVisible();await inspectVisual(page,info,`${width}-empty-discovery`);
 }
});

test('dialogs, comments, forms and mobile navigation fit the visual system',async({page},info)=>{
 test.setTimeout(180000);
 for(const width of [1440,1024,390]){
  await page.setViewportSize({width,height:1000});await page.goto('/');
  const create=page.getByRole('button',{name:'Create a plan',exact:true}).filter({visible:true}).first();
  await create.focus();await expect(create).toBeFocused();await expect(create).toHaveCSS('outline-style','solid');
  await inspectVisual(page,info,`${width}-keyboard-focus`);
  await page.getByRole('button',{name:'Create a plan',exact:true}).filter({visible:true}).first().click();
  await inspectVisual(page,info,`${width}-create-outing`);await page.getByRole('button',{name:'Trip',exact:true}).click();
  await inspectVisual(page,info,`${width}-create-trip`);await page.keyboard.press('Escape');
  await page.goto('/groups');await page.getByRole('button',{name:'Create a group',exact:true}).first().click();
  await page.getByRole('button',{name:'Add adult',exact:true}).click();await page.getByText('More details (optional)',{exact:true}).click();
  await inspectVisual(page,info,`${width}-group-editor`);await page.keyboard.press('Escape');
  await page.getByRole('button',{name:/^Remove Sunday/}).click();await inspectVisual(page,info,`${width}-group-remove`);await page.keyboard.press('Escape');
  await page.getByRole('button',{name:/^Archived/}).click();await inspectVisual(page,info,`${width}-groups-empty`);
  await page.goto('/plans/coastal-weekend');
  const first=page.getByRole('article').filter({has:page.getByRole('heading',{name:'Destination',exact:true})}).first();
  await first.getByRole('button',{name:/comments/}).click();await inspectVisual(page,info,`${width}-comments`);
  await first.getByRole('button',{name:'Edit decision',exact:true}).click();await inspectVisual(page,info,`${width}-edit-decision`);await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Add decision',exact:true}).click();await inspectVisual(page,info,`${width}-add-decision`);await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Review final plan',exact:true}).last().click();await inspectVisual(page,info,`${width}-review-final`);await page.keyboard.press('Escape');
  if(width<=1300){await page.getByRole('button',{name:'Planning assistant',exact:true}).click();await inspectVisual(page,info,`${width}-planning-assistant`);await page.keyboard.press('Escape');}
  for(const [tab,button] of [['Planning board','Edit details'],['Polls','Create poll'],['Itinerary','Add activity']]){
   await page.getByRole('tab',{name:tab}).click();await page.getByRole('button',{name:button,exact:true}).click();await inspectVisual(page,info,`${width}-${button.replaceAll(' ','-')}`);await page.keyboard.press('Escape');
  }
  await page.getByRole('button',{name:'Invite',exact:true}).click();await inspectVisual(page,info,`${width}-participants`);await page.keyboard.press('Escape');
  if(width===390){await page.getByRole('button',{name:'Open menu',exact:true}).click();await inspectVisual(page,info,'390-navigation');await page.keyboard.press('Escape');}
 }
});

test('workspace loading, service errors and success notices remain clear',async({page},info)=>{
 test.setTimeout(60000);
 let release!:()=>void;const pending=new Promise<void>(resolve=>{release=resolve;});
 await page.route('**/api/config',async route=>{await pending;await route.fulfill({status:503,json:{detail:'Synthetic unavailable configuration'}});});
 await page.goto('/',{waitUntil:'domcontentloaded'});await expect(page.getByText('Getting your workspace ready…',{exact:true})).toBeVisible();
 for(const width of [1440,1024,390]){await page.setViewportSize({width,height:1000});await inspectVisual(page,info,`${width}-workspace-loading`);}
 release();await expect(page.getByText('Could not load app configuration. Please reload.',{exact:true})).toBeVisible();
 await inspectVisual(page,info,'390-service-error');
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'',supabaseAnonKey:'',connectedReady:false}}));
 await page.reload();await page.getByRole('button',{name:'Create a plan',exact:true}).filter({visible:true}).first().click();
 await page.getByLabel('Plan name',{exact:true}).fill('Visual success state');await page.getByRole('button',{name:'Create demo plan',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'Your demo plan is ready.'})).toBeVisible();await inspectVisual(page,info,'390-success-notice');
});
