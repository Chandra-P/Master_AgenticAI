import {test,expect} from '@playwright/test';
import {initialPlans} from '../src/services/demo-data';
import {demoSnapshot,applyDemoDecision,demoMemberId} from '../src/services/demo-decisions';
import {validateDecisionSnapshot} from '../src/services/decisions';

test('malformed decision responses become a recoverable error rather than a page crash',()=>{
 expect(()=>validateDecisionSnapshot([], 'plan')).toThrow('unexpected response');
 expect(()=>validateDecisionSnapshot({plan_id:'another'},'plan')).toThrow('unexpected response');
});

test('working details are proposals and missing responses cannot finalize',()=>{
 const plan=structuredClone(initialPlans()[0]);const snapshot=demoSnapshot(plan);
 expect(snapshot.score).toBe(0);expect(snapshot.finalized).toBe(false);
 expect(snapshot.decisions).toHaveLength(5);
 expect(()=>applyDemoDecision(plan,snapshot,{kind:'finalize',reviewed:true,idempotencyKey:'one'},demoMemberId(plan,0))).toThrow();
});

test('consent, comments, finalization and option edits preserve honest state',()=>{
 const plan=structuredClone(initialPlans()[0]);plan.members=plan.members.slice(0,1);
 let snapshot=demoSnapshot(plan);const member=demoMemberId(plan,0);
 const run=(command:Parameters<typeof applyDemoDecision>[2])=>{snapshot=applyDemoDecision(plan,snapshot,command,member);};
 for(const original of snapshot.decisions){
  if(!original.options.length)run({kind:'edit',decisionId:original.id,options:['Reviewed choice']});
  const decision=snapshot.decisions.find(d=>d.id===original.id)!;
  run({kind:'respond',decisionId:decision.id,optionId:decision.options[0].id,response:'support'});
  run({kind:'confirm',decisionId:decision.id,optionId:decision.options[0].id});
 }
 expect(snapshot.score).toBe(99);
 run({kind:'comment',decisionId:snapshot.decisions[0].id,text:'Keep parking in mind.'});
 expect(snapshot.comments).toHaveLength(1);
 run({kind:'finalize',reviewed:true,idempotencyKey:'one'});expect(snapshot.score).toBe(100);
 run({kind:'edit',decisionId:snapshot.decisions[0].id,options:['New choice']});
 expect(snapshot.finalized).toBe(false);expect(snapshot.decisions[0].ballots).toHaveLength(0);
 expect(snapshot.comments).toHaveLength(1);
});

test('objections, all-abstain and membership changes cannot preserve confirmation',()=>{
 const plan=structuredClone(initialPlans()[0]);plan.members=plan.members.slice(0,2);
 let snapshot=demoSnapshot(plan);const decision=snapshot.decisions.find(d=>d.options.length)!;
 snapshot=applyDemoDecision(plan,snapshot,{kind:'respond',decisionId:decision.id,optionId:decision.options[0].id,response:'support'},demoMemberId(plan,0));
 snapshot=applyDemoDecision(plan,snapshot,{kind:'respond',decisionId:decision.id,optionId:decision.options[0].id,response:'object'},demoMemberId(plan,1));
 expect(()=>applyDemoDecision(plan,snapshot,{kind:'confirm',decisionId:decision.id,optionId:decision.options[0].id},demoMemberId(plan,0))).toThrow();
 for(let i=0;i<2;i++)snapshot=applyDemoDecision(plan,snapshot,{kind:'respond',decisionId:decision.id,optionId:null,response:'abstain'},demoMemberId(plan,i));
 expect(()=>applyDemoDecision(plan,snapshot,{kind:'confirm',decisionId:decision.id,optionId:decision.options[0].id},demoMemberId(plan,0))).toThrow();
 plan.decisionState=snapshot;plan.members.push({name:'New member',color:'#abc'});
 expect(demoSnapshot(plan).decisions[0].ballots).toHaveLength(0);
});
