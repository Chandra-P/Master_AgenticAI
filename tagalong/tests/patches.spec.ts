import {test,expect} from '@playwright/test';
import {createPlanPatches} from '../src/services/plan-patches';
import {initialPlans} from '../src/services/demo-data';

test('a small edit does not resend a large private conversation',()=>{
 const before=initialPlans()[0];before.messages=Array.from({length:600},(_,i)=>({id:String(i),author:'alice',text:'x'.repeat(1000),time:'now'}));
 const after={...before,budget:321};
 const patches=createPlanPatches(before,after);
 expect(patches).toEqual([{op:'replace',path:['budget'],value:321}]);
 expect(JSON.stringify(patches).length).toBeLessThan(100);
});

test('new chat and one changed vote use narrow patches',()=>{
 const before=initialPlans()[0];before.polls[0].votes={alice:0,bob:1};
 const message={id:'new-message',author:'alice',user_id:'alice',text:'Dinner?',time:'now'};
 const after={...before,messages:[...before.messages,message],polls:before.polls.map((p,i)=>i===0?{...p,votes:{...p.votes,alice:1}}:p)};
 const patches=createPlanPatches(before,after);
 expect(patches).toContainEqual({op:'add',path:['messages',before.messages.length],value:message});
 expect(patches).toContainEqual({op:'replace',path:['polls',0,'votes','alice'],value:1});
 expect(patches.some(p=>p.path.includes('bob'))).toBe(false);
});

test('array removals are ordered from the end so remaining positions stay valid',()=>{
 const before=initialPlans()[0];before.itinerary=[{id:'one',title:'One',time:'now',category:'Idea',location:'Here'},{id:'two',title:'Two',time:'now',category:'Idea',location:'Here'}];
 expect(createPlanPatches(before,{...before,itinerary:[]})).toEqual([{op:'remove',path:['itinerary',1]},{op:'remove',path:['itinerary',0]}]);
});
