import {test,expect,type Page,type Locator} from '@playwright/test';

async function login(page:Page,name:'alice'|'bob'|'carol'){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByRole('radio',{name:'Member',exact:true}).check();
 await page.getByLabel('Email address').fill(name+'@example.test');await page.getByLabel('Password',{exact:true}).fill('test-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}
const decision=(page:Page,title:string)=>page.getByRole('article').filter({has:page.getByRole('heading',{name:title,exact:true})}).first();
async function respond(card:Locator,title:string,response:'support'|'can_live_with'|'object'|'abstain'){
 await card.page().bringToFront();
 await card.getByLabel('Your response to '+title).selectOption(response);
 await card.getByRole('button',{name:'Save response',exact:true}).click();
 await expect(card.getByText('Your current response: '+response.replaceAll('_',' '),{exact:false})).toBeVisible({timeout:20000});
}

test('three people create join discuss resolve objections and finalize entirely through the UI',async({page:owner,browser,isMobile},info)=>{
 test.setTimeout(360000);
 const members=await Promise.all([browser.newContext({viewport:isMobile?{width:390,height:844}:{width:1280,height:900},isMobile}),browser.newContext({viewport:isMobile?{width:390,height:844}:{width:1280,height:900},isMobile})]);
 const [bob,carol]=await Promise.all(members.map(context=>context.newPage()));
 for(const page of [owner,bob,carol])page.setDefaultTimeout(15000);
 const title='Three-member dinner '+crypto.randomUUID().slice(0,8);
 try{
  await login(owner,'alice');await owner.goto('/');
  await owner.getByRole('button',{name:'Create a plan manually',exact:true}).click();
  await owner.getByLabel('Plan name').fill(title);await owner.getByLabel('Start date').fill('2027-05-14');
  await owner.getByRole('button',{name:'Create shared plan',exact:true}).click();
  await expect(owner.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();const planUrl=owner.url();
  console.log('Journey: plan created');
  await owner.getByRole('button',{name:'Add member',exact:true}).click();
  await owner.getByRole('button',{name:'Create invitation link',exact:true}).click();
  const link=await owner.getByLabel('Private join link',{exact:true}).inputValue();
  console.log('Journey: private invitation created');
  await owner.getByRole('button',{name:'Close',exact:true}).click();
  for(const [page,name] of [[bob,'bob'],[carol,'carol']] as const){
   await page.goto(link);await expect(page.getByRole('link',{name:'Sign in or create account',exact:true})).toBeVisible();
   console.log('Journey: '+name+' opened invitation');
   await expect(page.getByText(title,{exact:true})).toHaveCount(0);
   await page.getByRole('link',{name:'Sign in or create account',exact:true}).click();
   await login(page,name);await page.getByRole('link',{name:'Continue to invitation',exact:true}).click();
   console.log('Journey: '+name+' signed in');
   await expect(page.getByRole('heading',{name:'Join your people.',exact:true})).toBeVisible();
   await page.getByLabel('Preferred display name').fill(name==='bob'?'Bob Journey':'Carol Journey');
   await expect(page.getByLabel('Preferred display name')).toHaveValue(name==='bob'?'Bob Journey':'Carol Journey');
   await page.getByRole('button',{name:'Join plan',exact:true}).click();
   await expect(page.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
   console.log('Journey: '+name+' joined');
   await expect(page.getByRole('button',{name:'Add decision',exact:true})).toHaveCount(0);
  }
  const labels=['Place','Date and time','Budget','Activity or meal'];
  for(const label of labels){
   await owner.bringToFront();
   const card=decision(owner,label);
   await expect(card.getByText('0 of 3 responded',{exact:true})).toBeVisible({timeout:20000});
   await card.getByRole('button',{name:'Edit decision',exact:true}).click();
   const dialog=owner.getByRole('dialog');await dialog.getByLabel('Options, one per line').fill('Reviewed '+label);
   await dialog.getByRole('button',{name:'Save decision',exact:true}).click();await expect(dialog).not.toBeVisible();
   await respond(card,label,'support');
   await expect(card.getByRole('button',{name:'Confirm selected option',exact:true})).toBeDisabled();
   const bobCard=decision(bob,label),carolCard=decision(carol,label);
   await bob.bringToFront();
   await expect(bobCard.getByRole('radio',{name:new RegExp('Reviewed '+label)})).toBeVisible({timeout:20000});
   await respond(bobCard,label,label==='Place'?'object':'can_live_with');
   if(label==='Place'){
    await bobCard.getByRole('button',{name:/comments/}).click();
    await bobCard.getByLabel('Comment on Place').fill('Please verify accessible parking before we choose this place.');
   }
   await carol.bringToFront();await expect(carolCard.getByRole('radio',{name:new RegExp('Reviewed '+label)})).toBeVisible({timeout:20000});
   await respond(carolCard,label,label==='Budget'?'abstain':'support');
   if(label==='Place'){
    await bob.bringToFront();
    await expect(bobCard.getByText('3 of 3 responded',{exact:true})).toBeVisible({timeout:20000});
    await expect(bobCard.getByLabel('Comment on Place')).toHaveValue('Please verify accessible parking before we choose this place.');
    await bobCard.getByRole('button',{name:'Add comment',exact:true}).click();
    await expect(bobCard.locator('.decision-comments > div').filter({hasText:'Please verify accessible parking before we choose this place.'})).toBeVisible();
    await expect(card.getByText('Needs discussion',{exact:true})).toBeVisible({timeout:20000});
    await expect(card.getByRole('button',{name:'Confirm selected option',exact:true})).toBeDisabled();
    await respond(bobCard,label,'support');
   }
   await owner.bringToFront();await expect(card.getByRole('button',{name:'Confirm selected option',exact:true})).toBeEnabled({timeout:20000});
   await card.getByRole('button',{name:'Confirm selected option',exact:true}).click();
   await expect(card.getByText('Confirmed',{exact:true})).toBeVisible({timeout:20000});
  }
  await expect(owner.getByRole('progressbar',{name:'Group consensus'}).first()).toHaveAttribute('aria-valuenow','99');
  await bob.locator('#final-review').click();await expect(bob.getByRole('dialog').getByText('The plan owner must confirm and finalize this plan.',{exact:true})).toBeVisible();
  await expect(bob.getByRole('button',{name:'Finalize reviewed plan',exact:true})).toHaveCount(0);await bob.getByRole('button',{name:'Close',exact:true}).click();
  await owner.locator('#final-review').click();const review=owner.getByRole('dialog');
  await review.getByRole('checkbox').check();await review.getByRole('button',{name:'Finalize reviewed plan',exact:true}).click();
  await expect(review.getByRole('button',{name:'Reopen plan',exact:true})).toBeVisible({timeout:20000});await owner.getByRole('button',{name:'Close',exact:true}).click();
  for(const page of [owner,bob,carol]){
   await page.bringToFront();
   await expect(page.getByRole('progressbar',{name:'Group consensus'}).first()).toHaveAttribute('aria-valuenow','100',{timeout:20000});
   await page.reload();await expect(page.getByRole('progressbar',{name:'Group consensus'}).first()).toHaveAttribute('aria-valuenow','100');
  }
  await decision(carol,'Place').getByRole('button',{name:/comments/}).click();await expect(carol.getByText('Please verify accessible parking before we choose this place.',{exact:true})).toBeVisible();
  await owner.screenshot({path:info.outputPath('finalized-owner.png')});await carol.screenshot({path:info.outputPath('finalized-member.png')});
  await decision(owner,'Place').getByRole('button',{name:'Reopen decision',exact:true}).click();
  for(const page of [owner,bob,carol]){await page.bringToFront();await expect(page.getByRole('progressbar',{name:'Group consensus'}).first()).not.toHaveAttribute('aria-valuenow','100',{timeout:20000});}
  expect(owner.url().split('?')[0]).toBe(planUrl.split('?')[0]);
 }finally{await Promise.all(members.map(context=>context.close()));}
});
