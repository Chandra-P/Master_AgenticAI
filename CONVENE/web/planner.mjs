export function budgetSummary(party, options, quotes = {}) {
  let subtotal = 0;
  let complete = options.length === 2;
  for (const option of options) {
    const entered = quotes[option.id];
    const confirmed = typeof entered === 'number' && Number.isFinite(entered) && entered >= 0;
    if (!confirmed) complete = false;
    subtotal += confirmed ? entered : (Number.isFinite(option.price) ? option.price : 0);
  }
  const reserve = Math.max(0, Number(party.reserve) || 0);
  const headroom = party.budget - subtotal - reserve;
  let status = options.length ? 'quotes_needed' : 'choose_options';
  if (subtotal > party.budget || headroom < 0) status = 'over_budget';
  else if (complete) status = headroom < 200 ? 'tight' : 'within_allowance';
  return {subtotal, reserve, headroom, complete, status, remaining: party.budget - subtotal};
}

export function filteredOptions(options, {guests, search = '', priced = false}) {
  const term = search.toLowerCase().trim();
  return options.filter(option =>
    (option.kind !== 'venue' || option.capacity == null || option.capacity >= guests) &&
    (!priced || Number.isFinite(option.price)) &&
    (!term || [option.name, option.area, option.description, ...(option.features || [])].join(' ').toLowerCase().includes(term)));
}

export function quoteRequest(party, options) {
  return `Hello, I'm planning a ${party.theme}-themed 10th birthday in ${party.city} on ${party.date} for ${party.guests} people (${party.children??30} children and ${party.family??90} family members).\n\nOur whole-party budget is $${party.budget}; venue and decorations must leave room for food, cake and games.\n\n${options.map(option => `${option.name}:\nPlease confirm ${option.confirm?.map(question=>/availability/i.test(question)?`Availability on ${party.date}`:question).join('; ') || 'availability and an all-in price'}.\nPlease include: ${option.exclusions?.join('; ') || 'all required fees'}.\nSource: ${option.source_url}`).join('\n\n')}\n\nPlease provide a written itemized quote, deposit/refund terms and any restrictions. Nothing has been reserved. Thank you!`;
}

export function researchedOption(venue, id) {
  return {id:`researched-${id}`,kind:'venue',name:venue.details.name.value,
    area:'San Antonio · researched',address:venue.details.address.value,
    description:'Source-backed venue details. Confirm a suitable layout and complete quote before choosing.',
    capacity:null, capacity_text:venue.details.capacity?.value || 'Unconfirmed',
    price:null,pricing_text:venue.details.pricing?.value || 'Quote required',
    price_type:'quote_required',price_note:'No comparable all-in price confirmed',
    image:null,image_credit:'Illustrative venue photo',badge:'Capacity & costs to confirm',
    features:(venue.details.amenities || []).slice(0,4).map(fact=>fact.value),
    exclusions:['All required venue, staffing, security and other fees'],
    confirm:['Date availability','Seated capacity and games layout','Outside cake and food','Decorator access','Complete all-in quote'],
    source_url:venue.source_url,checked_on:venue.retrieved_at.slice(0,10),facts:venue.details,
    availability:'unconfirmed',stitch_confirmed:false};
}

export async function readAgentStream(stream, onEvent) {
  const reader=stream.getReader(),decoder=new TextDecoder();
  let buffer='',result;
  const record=line=>{
    if(!line.trim())return;
    const event=JSON.parse(line);onEvent(event);
    if(event.type==='error')throw Error(event.message);
    if(event.type==='result')result=event.result;
  };
  try{
    while(true){const chunk=await reader.read();if(chunk.done)break;
      buffer+=decoder.decode(chunk.value,{stream:true});
      const lines=buffer.split('\n');buffer=lines.pop();for(const line of lines)record(line);
    }
    buffer+=decoder.decode();if(buffer.trim())record(buffer);
    if(!result)throw Error('The agent connection ended before a result was returned.');
    return result;
  }finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
}

export function reconcileAgentPrices(options, updates) {
  const byId=new Map(updates.map(update=>[update.id,update]));
  return options.map(option=>{
    const update=byId.get(option.id);
    if(!update||(update.price!==null&&(!Number.isFinite(update.price)||update.price<0)))return option;
    return {...option,price:update.price,price_type:update.price_type,price_note:update.price_note};
  });
}
