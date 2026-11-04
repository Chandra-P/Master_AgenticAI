import type { Plan, Suggestion } from './types';
export const members = [{name:'Alex',color:'#edc6b3'},{name:'Maya',color:'#c6d5c4'},{name:'Sam',color:'#c7c7e2'},{name:'Jordan',color:'#eccb8c'}];
export const suggestions: Suggestion[] = [
 {id:'harbor',title:'Harbor & Pine',category:'Food & drink',location:'Seabrook · Waterfront',description:'Long lunches, seasonal plates, and a table with an ocean view.',price:'$$ · $25–40 / person',rating:'4.8',image:'/images/restaurant.jpg',tag:'A table for everyone'},
 {id:'trail',title:'The coast, on foot',category:'Outdoors',location:'Seabrook · Coastal trail',description:'An easy cliffside walk with hidden coves and plenty of photo stops.',price:'Free · 2 hours',rating:'4.9',image:'/images/coast.jpg',tag:'A little fresh air'},
 {id:'forest',title:'Slow mornings in the pines',category:'Getaways',location:'Pine Valley · Forest cabins',description:'Cozy cabins, morning coffee, and absolutely no rush.',price:'From $120 / night',rating:'4.7',image:'/images/forest.jpg',tag:'Switch off together'}
];
const base: Plan = {
 id:'coastal-weekend',title:'Coastal weekend',kind:'trip',location:'Seabrook, California',date:'Nov 20–22',start:'2026-11-20',end:'2026-11-22',budget:350,image:'/images/coast.jpg',members,
 messages:[
 {id:'1',author:'Maya',text:'A weekend by the ocean? I’m picturing good food, a little exploring, and zero alarms. 🌊',time:'10:24 AM'},
 {id:'2',author:'Sam',text:'Very much in. Can we keep it around $350 each?',time:'10:26 AM'},
 {id:'3',author:'Alex',text:'@Tagalong help us get this weekend out of the group chat!',time:'10:28 AM'},
 {id:'4',author:'Tagalong',assistant:true,text:'A coastal escape sounds like your kind of weekend. I’ve proposed outdoor dining and a relaxed pace for the group to review. Next up: vote on dates, then let’s find a place everyone loves.',time:'10:28 AM'},
 {id:'5',author:'Jordan',text:'This is already more organized than our last trip 😂 I’ll take a look at places to stay.',time:'10:31 AM'}],
 preferences:[{label:'Outdoor dining',confirmed:false},{label:'Relaxed pace',confirmed:false},{label:'Vegetarian friendly',confirmed:true}],
 polls:[{id:'dates',question:'When are we getting away?',options:['Nov 20–22','Nov 27–29','Dec 4–6'],votes:{Maya:0,Sam:0,Jordan:1},datePoll:true}],
 itinerary:[{id:'arrival',title:'Hello, Seabrook',time:'3:00 PM',category:'Arrival',location:'Meet at the waterfront'},{id:'walk',title:'Golden hour coastal walk',time:'4:30 PM',category:'Outdoors',location:'Seabrook coastal trail',image:'/images/coast.jpg'}],
 tasks:[{label:'Vote on our dates',done:false},{label:'Find a cozy place to stay',done:false},{label:'Pick a dinner spot',done:false}]
};
export function initialPlans(): Plan[] { return [structuredClone(base),{...structuredClone(base),id:'sunday-supper',title:'Sunday supper club',kind:'outing',location:'Brookside, California',date:'Nov 15',start:'2026-11-15',end:'2026-11-15',budget:60,image:'/images/restaurant.jpg',members:members.slice(0,3),messages:[{id:'s1',author:'Maya',text:'Our next supper club deserves somewhere special. Any ideas?',time:'Yesterday'}],itinerary:[],preferences:[{label:'Vegetarian friendly',confirmed:false}]},{...structuredClone(base),id:'into-the-pines',title:'Into the pines',location:'Pine Valley, California',date:'Dec 11–13',start:'2026-12-11',end:'2026-12-13',image:'/images/forest.jpg',budget:400,members:members.slice(0,3),messages:[],itinerary:[]}]; }
