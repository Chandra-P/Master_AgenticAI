import {test,expect} from '@playwright/test';
import {primaryTabs,planningTools,workspaceTab,primaryTabFor,isPlanningTool} from '../src/services/workspace-navigation';
import {initialPlans} from '../src/services/demo-data';
import {demoSnapshot} from '../src/services/demo-decisions';

test('legacy tools keep a primary parent and unknown links preserve Decisions default',()=>{
 expect(primaryTabs).toEqual(['Overview','Decisions','Chat','Itinerary']);
 expect(workspaceTab(null)).toBe('Decisions');
 expect(workspaceTab('unknown')).toBe('Decisions');
 for(const tool of planningTools){expect(workspaceTab(tool)).toBe(tool);expect(isPlanningTool(tool)).toBe(true);expect(primaryTabs).toContain(primaryTabFor(tool));}
 expect(primaryTabFor('Planning board')).toBe('Overview');
 expect(primaryTabFor('Demo bookings')).toBe('Itinerary');
});

test('four primary sections keep tools contextual and legacy links accessible',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.goto('/plans/coastal-weekend?tab=Discover');
 const sections=page.getByRole('tablist',{name:'Plan sections'});
 await expect(sections.getByRole('tab')).toHaveCount(4);
 await expect(sections.getByRole('tab',{name:'Decisions',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(page.getByRole('region',{name:'Discover planning tool'})).toBeVisible();
 await page.getByRole('button',{name:'Back to Decisions',exact:true}).click();
 await expect(page.getByRole('region',{name:'Discover planning tool'})).toHaveCount(0);
 await page.getByRole('tab',{name:'Overview',exact:true}).click();
 await page.getByRole('button',{name:'Notes and files',exact:true}).click();
 await expect(page.getByRole('region',{name:'Documents planning tool'})).toBeVisible();
 await expect(sections.getByRole('tab',{name:'Overview',exact:true})).toHaveAttribute('aria-selected','true');
 await page.getByText('More planning tools',{exact:true}).click();
 await page.getByRole('button',{name:'Polls',exact:true}).click();
 await expect(page.getByRole('region',{name:'Polls planning tool'})).toBeVisible();
});

test('itinerary carries confirmed option details without adding an activity or booking',async({page})=>{
 const plans=initialPlans();const plan=plans.find(p=>p.id==='coastal-weekend')!;
 const snapshot=demoSnapshot(plan);const decision=snapshot.decisions.find(d=>d.category==='lodging')!;
 decision.options=[{id:'synthetic-stay',label:'Synthetic harbor stay',sourceIds:[],url:'https://example.com/stay',estimatedCostPerPerson:120,notes:'Verify step-free access with the provider.'}];
 decision.selectedOptionId='synthetic-stay';decision.confirmation={by:decision.eligibleMemberIds[0],at:'2026-11-06T12:00:00Z',decisionVersion:decision.version};decision.status='confirmed';plan.decisionState=snapshot;
 await page.addInitScript(data=>{localStorage.setItem('tagalong-workspace-mode','demo');localStorage.setItem('tagalong-demo-v1',JSON.stringify(data));},plans);
 await page.goto('/plans/coastal-weekend?tab=Itinerary');
 const outcomes=page.getByRole('region',{name:'Confirmed decision outcomes'});
 await expect(outcomes.getByRole('heading',{name:'Synthetic harbor stay'})).toBeVisible();
 await expect(outcomes.getByRole('link',{name:'Option website'})).toHaveAttribute('href','https://example.com/stay');
 await expect(outcomes.getByText('Estimated USD 120 per person · unverified')).toBeVisible();
 await expect(outcomes.getByText('Verify step-free access with the provider.')).toBeVisible();
 await expect(outcomes.getByText('Not booked',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>JSON.parse(localStorage.getItem('tagalong-demo-v1')!).find((p:{id:string})=>p.id==='coastal-weekend').itinerary.length)).toBe(plan.itinerary.length);
 await page.getByRole('button',{name:'Preview demo booking workflow'}).click();
 await expect(page.getByRole('region',{name:'Demo bookings planning tool'})).toBeVisible();
});
