import {test,expect} from '@playwright/test';

test('guest can replay the Austin group journey, evidence, votes and itinerary',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.route('**/api/backend/v1/public/demo-stories/austin-four-friends',route=>route.fulfill({json:{
  planId:'public-austin-demo',template:'austin-four-friends',scripted:true,title:'Four friends, one Austin weekend',disclosure:'Fictional walkthrough · scripted AI and votes · no bookings',referenceDate:'2026-11-06',
  cast:[{name:'Alex',color:'#ec8677'},{name:'Maya',color:'#7b9270'},{name:'Sam',color:'#8583b3'},{name:'Jordan',color:'#6b98b4'}],
  sources:[{id:'demo-constraints',title:'Fictional demo · four friends’ constraints',text:'Sam needs a $650 per-person ceiling. Maya prefers vegetarian food. Jordan prefers a relaxed pace.'}],
  messages:[
   {id:'start',author:'Alex',text:'Could we take a weekend trip to Austin?',time:'Scene 1 · Start the weekend plan',assistant:false,simulation:true},
   {id:'ai',author:'Tagalong',text:'I can compare choices against the saved group constraints.',time:'Scene 1 · Start the weekend plan',assistant:true,simulation:true,sources:[{id:'demo-constraints',title:'Fictional demo · four friends’ constraints',text:'Sam needs a $650 per-person ceiling. Maya prefers vegetarian food. Jordan prefers a relaxed pace.'}]},
   {id:'vote',author:'Sam',text:'I object to the higher-cost hotel. The revised allowance works for me.',time:'Scene 2 · Needs become shared evidence',assistant:false,simulation:true}
  ],
  choices:[{category:'Lodging',label:'Lone Star Court · proposed stay',url:'https://www.lonestarcourt.com/',estimate:300,image:null,alternatives:['Busy central hotel','Lone Star Court','Separate stays'],reason:'The modeled allowance fits the fictional group budget.',votes:{Alex:'can_live_with',Maya:'support',Sam:'support',Jordan:'support'},sourceIds:['demo-constraints'],rounds:[{title:'Initial proposal',option:'Busy central hotel',votes:{Alex:'support',Maya:'can_live_with',Sam:'object',Jordan:'object'}},{title:'Revised fictional responses',option:'Lone Star Court',votes:{Alex:'can_live_with',Maya:'support',Sam:'support',Jordan:'support'}}]}],
  milestones:[{id:'idea',title:'1. Start the weekend plan',text:'Four friends start with an Austin idea.',sourceIds:['demo-constraints']},{id:'preferences',title:'2. Needs become shared evidence',text:'Their needs are captured in a saved note.',sourceIds:['demo-constraints'],ai:true}],
  days:[{date:'2027-04-16',title:'Friday · arrive and reconnect',items:[{time:'6:30 PM',title:'Shared vegetarian dinner candidate',location:'Austin · verify details',image:'/images/restaurant.jpg'}]}]
 }}));
 await page.goto('/');
 await page.getByRole('button',{name:/See four friends plan an Austin weekend/}).click();
 const dialog=page.getByRole('dialog');
 await expect(dialog.getByText('Fictional demo:',{exact:false})).toBeVisible();
 await expect(dialog.getByText('Could we take a weekend trip to Austin?',{exact:true})).toBeVisible();
 await expect(dialog.getByText('Evidence shown in this scripted reply (1)',{exact:true})).toBeVisible();
 await dialog.getByRole('button',{name:'Next step',exact:true}).click();
 await expect(dialog.getByText('Needs become shared evidence',{exact:true})).toBeVisible();
 await expect(dialog.getByRole('heading',{name:'Options, objections, and votes',exact:true})).toBeVisible();
 const lodging=dialog.locator('.austin-demo-option');
 await lodging.getByText('Inspect options and votes',{exact:true}).click();
 await expect(lodging.getByText('Sam:',{exact:true}).first()).toBeVisible();
 await expect(dialog.getByRole('heading',{name:'Final three-day itinerary',exact:true})).toBeVisible();
 await expect(dialog.getByText(/6:30 PM · Shared vegetarian dinner candidate/)).toBeVisible();
 await expect(dialog.getByRole('link',{name:'Sign in to run the live check',exact:true})).toBeVisible();
});
