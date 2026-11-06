import type {Tab} from './types';
﻿import {ConnectedService,getAuth,type PublicConfig} from './connected';
export interface DemoTrace {tool?:string;event?:string;status:string;protocol?:string;transport?:string}
export interface BookingReadiness {ready:boolean;approved:boolean;can_approve:boolean;blockers:{label:string;tab:Tab}[];decisions:{question:string;option:string}[]}
export interface DemoRestaurant {id:string;name:string;city:string;description:string;times?:string[]}
export interface DemoQuote {id:string;restaurant_name:string;city:string;date:string;time:string;party_size:number;expires_at:string;estimated_total:number;currency:string}
export interface DemoBooking extends Omit<DemoQuote,'expires_at'|'estimated_total'|'currency'> {reference:string;status:'confirmed'|'cancelled';created_by:string}
export interface DemoSearch {date:string;party_size:number;city:string}
export interface DemoQuoteInput extends DemoSearch {restaurant_id:string;time:string}
export class DemoBookingsService {
 private api:ConnectedService;
 constructor(config:PublicConfig){this.api=new ConnectedService(getAuth(config));}
 private path(planId:string){return '/v1/plans/'+encodeURIComponent(planId)+'/demo-bookings';}
 list(planId:string){return this.api.request<{simulation:true;bookings:DemoBooking[];readiness:BookingReadiness}>(this.path(planId));}
 approve(planId:string,revision:number){return this.api.request<{simulation:true;readiness:BookingReadiness}>(this.path(planId)+'/approve',{method:'POST',body:JSON.stringify({confirmed:true,expected_revision:revision})});}
 search(planId:string,input:DemoSearch){return this.api.request<{simulation:true;restaurants:DemoRestaurant[];trace:DemoTrace[]}>(this.path(planId)+'/search',{method:'POST',body:JSON.stringify(input)});}
 quote(planId:string,input:DemoQuoteInput){return this.api.request<{simulation:true;quote:DemoQuote;trace:DemoTrace[]}>(this.path(planId)+'/quote',{method:'POST',body:JSON.stringify(input)});}
 confirm(planId:string,quoteId:string){return this.api.request<{simulation:true;booking:DemoBooking;trace:DemoTrace[]}>(this.path(planId)+'/confirm',{method:'POST',body:JSON.stringify({quote_id:quoteId,confirmed:true})});}
 cancel(planId:string,id:string){return this.api.request<{simulation:true;booking:DemoBooking;trace:DemoTrace[]}>(this.path(planId)+'/'+encodeURIComponent(id)+'/cancel',{method:'POST',body:JSON.stringify({confirmed:true})});}
}
