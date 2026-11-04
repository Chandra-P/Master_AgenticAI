import Link from 'next/link';
export function Brand({small=false}:{small?:boolean}){return <Link href="/" className={'brand '+(small?'brand-small':'')} aria-label="Tagalong home"><span className="brand-mark"><i/><i/><i/></span><span>tagalong<span className="brand-dot">.</span></span></Link>;}
