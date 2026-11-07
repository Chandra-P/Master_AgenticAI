import type {DecisionSnapshot} from './decisions';
export type PlanKind = 'outing' | 'trip';
export type Tab = 'Overview' | 'Decisions' | 'Chat' | 'Planning board' | 'Polls' | 'Discover' | 'Itinerary' | 'Documents' | 'Demo bookings' | 'Group fit';
export interface Member { name: string; color: string; user_id?:string }
export interface Message { id: string; author: string; text: string; time: string; assistant?: boolean; user_id?:string; sources?:{id:string;title:string;text:string}[] }
export interface Preference { label: string; confirmed: boolean }
export interface Poll { id: string; question: string; options: string[]; votes: Record<string,number>; datePoll?: boolean }
export interface Activity { id: string; title: string; time: string; category: string; location: string; image?: string;source_url?:string;map_url?:string;image_source_url?:string;day?:string }
export interface GroupMember { id:string; preferredName:string; color:string; firstName?:string; lastName?:string; email?:string }
export interface Group { id:string; name:string; theme:string; ownerId:string; members:GroupMember[]; archived:boolean; revision?:number }
export interface GroupSnapshot {id:string;name:string;theme:string;revision?:number;participants?:string[]}
export type GroupDraft = Pick<Group,'name'|'theme'|'members'>;
export interface Plan { demo_template?:'austin-four-friends'; decisionState?:DecisionSnapshot; groupId?:string; group?:GroupSnapshot; id: string; title: string; kind: PlanKind; location: string; date: string; start: string; end: string; budget: number; image: string; members: Member[]; messages: Message[]; preferences: Preference[]; polls: Poll[]; itinerary: Activity[]; tasks: {label:string;done:boolean}[]; revision?:number;owner_id?:string;role?:'owner'|'member' }
export interface CreatePlanInput { title:string; kind:PlanKind; start:string; end:string; participants:string; groupId?:string; expectedGroupRevision?:number }
export interface Suggestion { id:string; title:string; category:string; location:string; description:string; price:string; rating:string; image:string; tag:string }
export interface PlanningService { load():Promise<Plan[]>; save(plans:Plan[]):void; create(input:CreatePlanInput,group?:Group):Plan }
export interface AssistantService { reply(message:string):{text:string; preferences:Preference[]} }
