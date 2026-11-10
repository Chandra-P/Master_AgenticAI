import {test,expect} from '@playwright/test';
import {homePlanModel} from '../src/features/planning/decisions/home-plan-model';
import type {Plan} from '../src/services/types';
import type {DecisionSnapshot} from '../src/services/decisions';

test('home participation excludes stale ballots and chat activity',()=>{
 const plan={id:'synthetic',members:[{name:'Alex',color:'blue'},{name:'Sam',color:'mint'}]} as Plan;
 const snapshot:DecisionSnapshot={plan_id:'synthetic',plan_revision:2,score:0,finalized:false,finalization:null,last_activity_at:null,comments:[],decisions:[{id:'place',planId:'synthetic',title:'Place',category:'place',required:true,status:'awaiting_responses',version:2,eligibleMemberIds:['demo-member-0','demo-member-1'],options:[{id:'a',label:'Option A',sourceIds:[]}],ballots:[{memberId:'demo-member-0',optionId:'a',response:'support',decisionVersion:1,updatedAt:'2026-11-01T12:00:00Z'}],selectedOptionId:null,confirmation:null}]};
 const model=homePlanModel(plan,snapshot,'demo-member-0');
 expect(model.status).toBe('Your response needed');
 expect(model.participation).toBe('0 of 2 responded');
 expect(model.waitingOn).toEqual(['Alex','Sam']);
 expect(model.activity).toBe('Activity not available');
 expect(model.href).toBe('/plans/synthetic?tab=Decisions#decision-place');
});

test.describe('homepage browser',()=>{
test.beforeEach(async({page})=>{await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));});

test('idea chips preserve a reviewed demo creation path',async({page})=>{
 await page.goto('/');
 await expect(page.getByText('Turn group chats into plans.',{exact:true})).toBeVisible();
 const agentFlow=page.getByRole('region',{name:'AI planning flow'});
 await expect(agentFlow).toBeVisible();
 await expect(agentFlow.getByText('Search tool',{exact:true})).toBeVisible();
 await expect(agentFlow.getByText('Pinecone RAG',{exact:true})).toBeVisible();
 await expect(agentFlow.getByText('Group decides',{exact:true})).toBeVisible();
 const idea=page.getByRole('textbox',{name:'Describe your plan'});
 await expect(idea).toHaveAttribute('placeholder','Weekend trip to Austin with 6 friends');
 await page.getByRole('button',{name:'Dinner Friday night for 8 people',exact:true}).click();
 await expect(idea).toHaveValue('Dinner Friday night for 8 people');
 await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.getByRole('button',{name:'Start Planning',exact:true}).click();
 await expect(page.getByLabel('Plan name',{exact:true})).toHaveValue('Dinner Friday night for 8 people');
 await expect(page.getByRole('button',{name:'Create demo plan',exact:true})).toBeVisible();
});

test('next steps precede decision-based history without invented activity',async({page})=>{
 await page.goto('/');
 const next=page.getByRole('heading',{name:'Your next steps',exact:true});
 const history=page.getByRole('heading',{name:'Continue planning',exact:true});
 await expect(next).toBeVisible();
 await expect(history).toBeVisible();
 expect(await next.evaluate((element)=>element.getBoundingClientRect().top)).toBeLessThan(await history.evaluate((element)=>element.getBoundingClientRect().top));
 await expect(page.getByRole('link',{name:'Open Coastal weekend',exact:true})).toBeVisible();
 await expect(page.getByText('Activity not available').first()).toBeVisible();
 await expect(page.getByText('planning progress',{exact:false})).toHaveCount(0);
});

});
