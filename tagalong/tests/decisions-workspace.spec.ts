import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));});
test('decisions are the default and contextual comments persist',async({page})=>{
 await page.goto('/plans/coastal-weekend');
 await expect(page.getByRole('tab',{name:'Decisions',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(page.getByRole('heading',{name:'Plan summary',exact:true})).toBeVisible();
 const first=page.getByRole('article').filter({has:page.getByRole('heading',{name:'Destination',exact:true})}).first();
 await first.getByRole('button',{name:/comments/}).click();
 await first.getByLabel('Comment on Destination').fill('Please consider accessible parking.');
 await first.getByRole('button',{name:'Add comment',exact:true}).click();
 await expect(first.getByText('Please consider accessible parking.',{exact:true})).toBeVisible();
 await page.reload();
 await first.getByRole('button',{name:/comments/}).click();
 await expect(first.getByText('Please consider accessible parking.',{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Chat',exact:true}).click();
 await expect(page.getByLabel('Message your group')).toBeVisible();
});

test('a response is separate from a comment and option edits require a new response',async({page})=>{
 await page.goto('/plans/coastal-weekend');
 const card=page.getByRole('article').filter({has:page.getByRole('heading',{name:'Destination',exact:true})}).first();
 await card.getByLabel('Your response to Destination').selectOption('support');
 await card.getByRole('button',{name:'Save response',exact:true}).click();
 await expect(card.getByText(/Your current response: support/)).toBeVisible();
 await expect(card.getByRole('button',{name:'Confirm selected option'})).toBeDisabled();
 await card.getByRole('button',{name:'Edit decision'}).click();
 const dialog=page.getByRole('dialog');
 await dialog.getByLabel('Options, one per line').fill('A different coast');
 await dialog.getByRole('button',{name:'Save decision',exact:true}).click();
 await expect(dialog).not.toBeVisible();
 await expect(card.getByText(/Your current response:/)).toHaveCount(0);
 await expect(card.getByText('0 of 4 responded')).toBeVisible();
 await page.reload();
 await expect(card.getByRole('radio',{name:/A different coast/})).toBeVisible();
});
test('final review is an explicit owner action and mobile assistant remains accessible',async({page})=>{
 await page.goto('/plans/coastal-weekend?tab=Decisions#final-review');
 const review=page.getByRole('dialog');
 await expect(review.getByRole('heading',{name:'Review final plan'})).toBeVisible();
 await expect(review.getByRole('button',{name:'Finalize reviewed plan'})).toBeDisabled();
 await review.getByRole('button',{name:'Close',exact:true}).click();
 if(page.viewportSize()!.width<1100){
  await page.getByRole('button',{name:'Planning assistant',exact:true}).click();
  await expect(page.getByRole('dialog').getByRole('heading',{name:'Group momentum'})).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button',{name:'Planning assistant',exact:true})).toBeFocused();
 }
 await expect(page.getByRole('progressbar',{name:'Group consensus'}).first()).toHaveAttribute('aria-valuenow','0');
});


test('loaded older comments remain visible after a decision snapshot refresh',async({page})=>{
 await page.goto('/plans/coastal-weekend');
 const card=page.getByRole('article').filter({has:page.getByRole('heading',{name:'Destination',exact:true})}).first();
 await card.getByRole('button',{name:/comments/}).click();
 await card.getByLabel('Comment on Destination').fill('Initialize synthetic comment history');
 await card.getByRole('button',{name:'Add comment',exact:true}).click();
 await expect(card.getByText('Initialize synthetic comment history',{exact:true})).toBeVisible();
 await page.evaluate(()=>{
  const plans=JSON.parse(localStorage.getItem('tagalong-demo-v1')!);
  const plan=plans.find((p:{id:string})=>p.id==='coastal-weekend');
  const snapshot=plan.decisionState;
  const decision=snapshot.decisions.find((d:{category:string})=>d.category==='destination');
  snapshot.comments=Array.from({length:75},(_,i)=>({id:'history-'+i,planId:plan.id,decisionId:decision.id,authorId:decision.eligibleMemberIds[0],decisionVersion:decision.version,text:'Synthetic history comment '+i,createdAt:new Date(Date.UTC(2026,10,1,0,i)).toISOString()}));
  delete snapshot.comment_counts;
  localStorage.setItem('tagalong-demo-v1',JSON.stringify(plans));
 });
 await page.reload();
 await card.getByRole('button',{name:/comments/}).click();
 for(let i=0;i<5;i++)await card.getByRole('button',{name:'Show more comments'}).click();
 await expect(card.getByText('Synthetic history comment 55',{exact:true})).toBeVisible();
 await card.getByLabel('Comment on Destination').fill('New comment triggers a snapshot refresh');
 await card.getByRole('button',{name:'Add comment',exact:true}).click();
 await expect(card.getByRole('button',{name:'76 comments',exact:true})).toBeVisible();
 await expect(card.getByText('Synthetic history comment 55',{exact:true})).toBeVisible();
});
