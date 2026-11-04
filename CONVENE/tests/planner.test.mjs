import test from 'node:test';
import assert from 'node:assert/strict';
import { budgetSummary, quoteRequest, filteredOptions, researchedOption, readAgentStream, reconcileAgentPrices } from '../web/planner.mjs';

const venue = {id:'v',name:'Hall',kind:'venue',price:235,price_type:'published_base',capacity:160,exclusions:['Security']};
const decor = {id:'d',name:'Balloons',kind:'decorator',price:375,price_type:'starting_at',exclusions:['Delivery']};
const party = {guests:120,budget:2000,reserve:1000,date:'2026-12-06',theme:'Stitch',city:'San Antonio, Texas'};

test('published lower bounds never become confirmed totals',()=>{
 const result=budgetSummary(party,[venue,decor],{});
 assert.equal(result.subtotal,610); assert.equal(result.headroom,390);
 assert.equal(result.complete,false); assert.equal(result.status,'quotes_needed');
});
test('confirmed entered quotes retain room for rest of the party',()=>{
 const result=budgetSummary(party,[venue,decor],{v:450,d:550});
 assert.equal(result.subtotal,1000); assert.equal(result.headroom,0);
 assert.equal(result.complete,true); assert.equal(result.status,'tight');
});
test('over budget and missing costs remain explicit',()=>{
 assert.equal(budgetSummary(party,[venue,decor],{v:1100,d:950}).status,'over_budget');
 assert.equal(budgetSummary(party,[{...decor,price:null}],{}).complete,false);
 assert.equal(budgetSummary(party,[],{}).status,'choose_options');
});
test('unknown prices are excluded from known-price filtering; capacity counts everyone',()=>{
 assert.deepEqual(filteredOptions([venue,{...venue,id:'small',capacity:100}],{guests:120,search:'',priced:false}),[venue]);
 assert.deepEqual(filteredOptions([{...decor,price:null}],{guests:120,search:'',priced:true}),[]);
});
test('quote draft contains full guest count and never asserts availability',()=>{
 const text=quoteRequest(party,[venue,decor]);
 assert.match(text,/120/); assert.match(text,/2026-12-06/); assert.match(text,/Stitch/);
 assert.match(text,/availability/i); assert.match(text,/Security/i);
});

test('edited date replaces catalog availability date in quote draft',()=>{
 const text=quoteRequest({...party,date:'2026-12-13'},[{...venue,confirm:['December 6 availability']}]);
 assert.match(text,/2026-12-13/);assert.doesNotMatch(text,/December 6/);
});

test('researched venue becomes selectable without inventing price or capacity',()=>{
 const result=researchedOption({source_url:'https://venue.example/',retrieved_at:'2026-10-31T12:00:00Z',
   details:{name:{value:'Real venue'},address:{value:'1 Main St, San Antonio, TX'},
   capacity:{value:'80 seated / 150 standing'},pricing:{value:'From $100 per hour'},amenities:[]}},1);
 assert.equal(result.kind,'venue');assert.equal(result.price,null);assert.equal(result.capacity,null);
 assert.equal(result.capacity_text,'80 seated / 150 standing');
 assert.equal(result.price_type,'quote_required');
 assert.equal(result.source_url,'https://venue.example/');
 assert.equal(budgetSummary(party,[result,decor],{}).complete,false);
});

test('agent activity decodes split NDJSON chunks and returns final recommendation',async()=>{
 const encoder=new TextEncoder();const events=[];
 const stream=new ReadableStream({start(controller){
   for(const text of ['{"type":"node","node":"Ven','dor"}\n{"type":"result","result":{"tool_count":2}}\n'])controller.enqueue(encoder.encode(text));
   controller.close();
 }});
 const result=await readAgentStream(stream,event=>events.push(event));
 assert.equal(events[0].node,'Vendor');assert.equal(result.tool_count,2);
});

test('agent stream failure is not treated as a completed plan',async()=>{
 const stream=new ReadableStream({start(controller){controller.enqueue(new TextEncoder().encode('{"type":"error","message":"Provider unavailable"}\n'));controller.close();}});
 await assert.rejects(()=>readAgentStream(stream,()=>{}),/Provider unavailable/);
});

test('applying agent combination cannot restore an invalidated source price',()=>{
 const options=reconcileAgentPrices([venue,decor],[{id:'v',price:null,price_type:'quote_required',price_note:'Updated quote required'}]);
 assert.equal(options[0].price,null);
 assert.equal(budgetSummary(party,options,{}).subtotal,375);
 assert.equal(budgetSummary(party,options,{}).complete,false);
});
