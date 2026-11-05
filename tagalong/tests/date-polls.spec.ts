import {test,expect} from '@playwright/test';
import {initialPlans} from '../src/services/demo-data';

for(const voted of [false,true])test('legacy trip date poll preserves vote meanings: '+(voted?'existing votes':'no votes'),async({page})=>{
 const plan=initialPlans()[0];plan.start='2027-05-14';plan.end='2027-05-16';plan.date='May 14–16';plan.polls=[{id:'old-dates',question:'Which date works best?',options:['May 14','May 16'],votes:voted?{Maya:1}:{},datePoll:true}];
 await page.addInitScript(p=>{localStorage.setItem('tagalong-workspace-mode','demo');localStorage.setItem('tagalong-demo-v1',JSON.stringify([p]));},plan);
 await page.goto('/plans/'+plan.id+'?tab=Polls');
 await expect(page.getByText('Working dates: May 14–16',{exact:true})).toBeVisible();
 if(!voted){
  await page.getByRole('button',{name:/May 14–16/}).click();
  await expect(page.getByRole('button',{name:/May 14–16/})).toHaveAttribute('aria-pressed','true');
  const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('tagalong-demo-v1')||'[]')[0]);
  expect(saved.polls[0].options).toEqual(['May 14–16','Suggest another date range']);expect(saved.polls[0].votes.Alex).toBe(0);
 }else{
  await expect(page.getByRole('note')).toContainText('Existing votes refer to the original options');
  await page.getByRole('button',{name:'Create a full-range poll',exact:true}).click();
  await expect(page.getByLabel('Option 1',{exact:true})).toHaveValue('May 14–16');
  await page.getByRole('button',{name:'Publish demo poll',exact:true}).click();
  await expect(page.locator('.poll-card')).toHaveCount(2);
  const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('tagalong-demo-v1')||'[]')[0]);
  expect(saved.polls[0].votes).toEqual({Maya:1});expect(saved.polls[1].options[0]).toBe('May 14–16');
 }
});
