import type {OptionProvenance} from './decisions';
import {ConnectedService,type RequestScope} from './connected';
import {publicWebUrl,safeActivityImage} from './place-links';

export const ideaInterests=['Food','Outdoors','Music','Arts','Nightlife','Relaxed'] as const;
export function hasIdeaCity(city:string){return !!city.trim()&&!/^(?:location to decide|somewhere(?: together)?|to decide|tbd|unknown)$/i.test(city.trim());}
export interface CityIdea {provenance?:OptionProvenance;id:string;name:string;details:string;url:string;image?:string;source_ids:string[]}
export interface CityIdeasResult {
 places:CityIdea[];events:(CityIdea&{date:string})[];
 sources:{id:string;title:string;text:string;url?:string}[];
 steps:{id:string;label:string;status:string;detail:string}[];question?:string;
}
export interface IdeaSuggestion extends CityIdea {category:'Place idea'|'Event idea';day?:string}
export interface ReviewedSuggestion {title:string;url:string;image?:string;day?:string;provenance?:OptionProvenance;category:'Place idea'|'Event idea'}
export function cityIdeaSuggestions(result:CityIdeasResult):IdeaSuggestion[]{
 return [...result.places.map(idea=>({...idea,id:'place:'+idea.url,category:'Place idea' as const})),...result.events.map(idea=>({...idea,id:'event:'+idea.url+'|'+idea.date,category:'Event idea' as const,day:idea.date}))];
}
export function addDraftIdea(selected:IdeaSuggestion[],idea:IdeaSuggestion){
 if(selected.some(item=>item.id===idea.id)||selected.length>=8)return selected;
 return [...selected,idea];
}
export function reviewedSuggestion(idea:IdeaSuggestion):ReviewedSuggestion|null {
 const url=publicWebUrl(idea.url);if(!url)return null;
 const image=safeActivityImage(idea.image);
 return {title:idea.name,url,category:idea.category,...(image?{image}:{}),...(idea.day?{day:idea.day}:{}),...(idea.provenance?{provenance:idea.provenance}:{})};
}
export class IdeaDiscoveryService {
 constructor(private api:ConnectedService){}
 discover(input:{city:string;start:string;end:string;interests:string[];query?:string},scope:RequestScope,signal:AbortSignal){
  return this.api.request<CityIdeasResult>('/v1/city-ideas',{method:'POST',body:JSON.stringify(input),signal},scope);
 }
}
