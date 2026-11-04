import {useState} from 'react';
import './vendors.css';

type Contact={organization:string;role:string;phone_display:string;phone_e164:string;email:string|null;office_hours:string;contact_url:string;source_url:string;verified_on:string};
type Vendor={id:string;name:string;kind:string;address?:string;capacity:number|null;price:number|null;price_type:string;checked_on:string;source_url:string;contact?:Contact;directory_version:number;approval:{status:string;approved_by:string;approved_on:string}};
type Directory={vendors:Vendor[];food:Vendor[];note:string};

export function ApprovedVendors({ready,load}:{ready:boolean;load:()=>Promise<Directory>}){
  const [open,setOpen]=useState(false),[directory,setDirectory]=useState<Directory|null>(null);
  const [category,setCategory]=useState('venue'),[busy,setBusy]=useState(false),[error,setError]=useState('');
  async function toggle(){
    setOpen(!open);
    if(!open){setDirectory(null);setBusy(true);setError('');try{setDirectory(await load());}
      catch{setError('The approved directory could not load. Close and reopen to retry.');}finally{setBusy(false);}}
  }
  const vendors=category==='food'?directory?.food:directory?.vendors.filter(v=>v.kind===category);
  return <section className="approved-directory" aria-label="Approved vendor directory">
    <div className="directory-heading"><div><p className="eyebrow">PEOPLE TO HELP YOU CELEBRATE</p><h2>Your approved local directory</h2><p>Previously curated and approved for CONVENE. Final prices and availability still need confirmation.</p></div><button className="directory-toggle" disabled={!ready||busy} onClick={()=>void toggle()} aria-expanded={open} aria-controls="vendor-list">{open?'Close directory':'View approved vendors'} {open?'−':'+'}</button></div>
    {open&&<div id="vendor-list"><div className="directory-controls"><label htmlFor="vendor-category">Show</label><select id="vendor-category" value={category} onChange={e=>setCategory(e.target.value)}><option value="venue">Venues</option><option value="decorator">Professional decorators</option><option value="food">Food providers</option></select><span>Existing list · no web search</span></div>{busy&&<p role="status">Loading approved vendors…</p>}{error&&<p role="alert">{error}</p>}
      <div className="vendor-grid">{vendors?.map(v=><article className="vendor-card" key={v.id}><span className="vendor-status">Approved for consideration</span><h3>{v.name}</h3>{v.address&&<p>{v.address}</p>}<div className="vendor-facts">{v.capacity!=null&&<span>Published maximum: {v.capacity} guests</span>}<span>{v.price!=null?`$${v.price.toLocaleString()} ${v.price_type==='published_base'?'published base':'starting/minimum'}`:'Quote required'}</span><small>Price snapshot: {v.checked_on} · required extras may apply</small></div>
        {v.contact?<div className="vendor-contact"><h4>Contact the reservations office</h4><p>{v.contact.organization}</p><small>{v.contact.role}</small><a className="vendor-phone" href={`tel:${v.contact.phone_e164}`}>{v.contact.phone_display}</a><p className="office-hours">{v.contact.office_hours} · Central time</p>{v.contact.email?<p>Email: {v.contact.email}</p>:<p className="contact-unknown">Direct email not verified. Use the official contact page.</p>}<a href={v.contact.contact_url} target="_blank" rel="noopener noreferrer">Official contact page ↗</a><small>Contact checked {v.contact.verified_on} · <a href={v.contact.source_url} target="_blank" rel="noopener noreferrer">source</a></small></div>:<div className="vendor-contact"><p>Contact details need verification.</p><a href={v.source_url} target="_blank" rel="noopener noreferrer">Visit the official provider website ↗</a></div>}
        <p className="vendor-warning">Date availability, complete quote and securing conditions: needs confirmation.</p><small>Directory v{v.directory_version} · approved {v.approval.approved_on}<br/>{v.approval.approved_by}</small><a href={v.source_url} target="_blank" rel="noopener noreferrer">Venue / provider details ↗</a>
      </article>)}</div>{directory&&!busy&&!vendors?.length&&<p className="directory-empty">No approved {category==='food'?'food providers':'vendors'} configured yet. We’ll show that gap rather than suggest unapproved businesses.</p>}
    </div>}
  </section>;
}
