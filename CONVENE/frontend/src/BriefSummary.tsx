export type Brief = {version:number;occasion:string|null;services:string[];event_date:string|null;date_flexibility:string|null;time_window:string|null;children:number|null;family:number|null;guest_estimate:number|null;budget:string|null;age:number|null;interests:string|null;theme:string|null;priorities:string|null;dietary_needs:string|null;food_fulfilment:string|null;explicit_unknown:string[];tentative_fields:string[]};

export function BriefSummary({brief}:{brief:Brief|undefined}){
  const guests=brief?.children!=null&&brief.family!=null?brief.children+brief.family:brief?.guest_estimate;
  const fact=(label:string,value:unknown,key:string,statusKeys=[key])=><div className="fact" key={key}><dt>{label}</dt><dd>{value==null||value===''?'Not decided':String(value)}{statusKeys.some(field=>brief?.tentative_fields.includes(field))&&<span className="tag">Tentative</span>}</dd></div>;
  return <dl>
    {fact('Celebrating',brief?.occasion,'occasion')}
    {fact('Help with',brief?.services.length?brief.services.join(', '):null,'services')}
    {brief?.occasion?.toLowerCase().includes('birthday')&&fact('Birthday age',brief.age,'age')}
    {fact('All guests',guests,'guest_estimate',['guest_estimate','children','family'])}
    {brief?.children!=null&&fact('Children',brief.children,'children')}
    {brief?.family!=null&&fact('Accompanying adults / family',brief.family,'family')}
    {fact('When',brief?.event_date||brief?.date_flexibility,'event_date',['event_date','date_flexibility'])}
    {brief?.event_date&&brief.date_flexibility&&fact('Date flexibility',brief.date_flexibility,'date_flexibility')}
    {fact('Time',brief?.time_window,'time_window')}
    {fact('Total budget',brief?.budget?`$${Number(brief.budget).toLocaleString('en-US')}`:null,'budget')}
    {fact('What matters most',brief?.priorities,'priorities')}
    {brief?.interests&&fact('Interests / activities',brief.interests,'interests')}
    {brief?.services.includes('decoration')&&fact('Theme',brief.theme,'theme')}
    {brief?.services.includes('food')&&fact('Food preferences / allergies',brief.dietary_needs,'dietary_needs')}
    {brief?.services.includes('food')&&fact('Food pickup / delivery',brief.food_fulfilment,'food_fulfilment')}
  </dl>;
}
