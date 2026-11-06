import {test,expect} from '@playwright/test';
import {mockPlanningService} from '../src/services/mock-planning-service';
import type {Group} from '../src/services/types';
const group:Group={id:'private-circle',name:'Our circle',theme:'Dinner',ownerId:'alex',archived:false,members:[{id:'alex',preferredName:'Alex',color:'#fff'},{id:'friend',preferredName:'Sunny',color:'#000',firstName:'Private',lastName:'Contact',email:'private@example.test'}]};
test('demo group plans copy aliases without private contacts and remain independent snapshots',()=>{
 const plan=mockPlanningService.create({title:'Supper',kind:'outing',start:'',end:'',participants:'Ignored'},group);
 expect(plan.members.map(m=>m.name)).toEqual(['Alex','Sunny']);
 expect(JSON.stringify(plan)).not.toContain('private@example.test');
 expect(JSON.stringify(plan)).not.toContain('Private');
 group.members[1].preferredName='Changed';group.name='Changed group';
 expect(plan.members[1].name).toBe('Sunny');
 expect(plan.groupId).toBe('private-circle');expect(plan.group?.name).toBe('Our circle');
});
import {GROUP_STORAGE_KEY,loadGroups,saveGroups,validateGroup} from '../src/services/group-service';
test('invalid stored groups are retained without overwriting contacts',()=>{
 const previous=Object.getOwnPropertyDescriptor(globalThis,'localStorage');const data=new Map([[GROUP_STORAGE_KEY,'not valid json']]);
 Object.defineProperty(globalThis,'localStorage',{configurable:true,value:{getItem:(key:string)=>data.get(key)??null,setItem:(key:string,value:string)=>data.set(key,value)}});
 try{const loaded=loadGroups();expect(loaded.groups).toEqual([]);expect(loaded.writable).toBe(false);expect(saveGroups([],loaded.writable)).toContain('only in memory');expect(data.get(GROUP_STORAGE_KEY)).toBe('not valid json');}finally{if(previous)Object.defineProperty(globalThis,'localStorage',previous);else Reflect.deleteProperty(globalThis,'localStorage');}
});
test('group contacts reject duplicate aliases and duplicate email addresses',()=>{
 const draft={name:'Friends',theme:'Dinner',members:[{id:'alex',preferredName:'Alex',color:'#fff'},{id:'a',preferredName:' Alex ',color:'#000'}]};
 expect(validateGroup(draft,[])).toContain('different preferred name');
 const contacts={...draft,members:[{id:'alex',preferredName:'Alex',color:'#fff',email:'same@example.test'},{id:'a',preferredName:'Sunny',color:'#000',email:'SAME@example.test'}]};
 expect(validateGroup(contacts,[])).toContain('only once');
});
