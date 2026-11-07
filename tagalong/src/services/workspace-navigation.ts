import type {Tab} from './types';

export const primaryTabs=['Overview','Decisions','Chat','Itinerary'] as const;
export type PrimaryTab=typeof primaryTabs[number];
export const planningTools=['Discover','Documents','Polls','Group fit','Demo bookings'] as const;
export function workspaceTab(value:string|null):Tab {
 return [...primaryTabs,...planningTools,'Planning board'].includes(value||'')?value as Tab:'Decisions';
}
export function primaryTabFor(tab:Tab):PrimaryTab {
 switch(tab){
  case 'Planning board':case 'Documents':case 'Group fit':return 'Overview';
  case 'Discover':case 'Polls':return 'Decisions';
  case 'Demo bookings':return 'Itinerary';
  default:return tab;
 }
}
export const isPlanningTool=(tab:Tab)=>!primaryTabs.some(primary=>primary===tab);
