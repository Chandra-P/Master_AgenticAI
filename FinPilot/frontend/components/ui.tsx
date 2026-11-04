import { ArrowUpRight, Check, CircleAlert, LoaderCircle, Sparkles } from 'lucide-react';
import type { ReactNode } from 'react';
export function ResourceState({loading,error,retry}:{loading:boolean;error:string|null;retry?:()=>void}) {
 if(error) return <div className="error-state" role="alert"><CircleAlert size={22}/><p>{error}</p>{retry&&<button className="button secondary" onClick={retry}>Try again</button>}</div>;
 if(loading) return <div className="loading-state" role="status"><LoaderCircle className="spin" size={20}/><span>Loading your financial picture…</span><div className="skeleton"/><div className="skeleton short"/></div>;
 return null;
}
export function Panel({title,eyebrow,action,children,className=''}:{title?:string;eyebrow?:string;action?:ReactNode;children:ReactNode;className?:string}) {
 return <section className={`panel ${className}`}><div className="panel-head"><div>{eyebrow&&<div className="eyebrow">{eyebrow}</div>}{title&&<h2>{title}</h2>}</div>{action}</div>{children}</section>;
}
export function Badge({children,tone='neutral'}:{children:ReactNode;tone?:'neutral'|'green'|'amber'|'red'}) {return <span className={`badge ${tone}`}>{children}</span>;}
export function Kpi({label,value,detail,icon}:{label:string;value:string;detail:string;icon?:ReactNode}) {return <div className="kpi"><div className="kpi-label">{label}{icon}</div><div className="kpi-value">{value}</div><div className="kpi-detail">{detail}</div></div>;}
export function Empty({title,children}:{title:string;children?:ReactNode}) {return <div className="empty"><Sparkles size={28}/><h3>{title}</h3><p>{children}</p></div>;}
export function LinkButton({children,onClick}:{children:ReactNode;onClick:()=>void}) {return <button className="text-button" onClick={onClick}>{children}<ArrowUpRight size={15}/></button>;}
export function Status({passed,children}:{passed:boolean;children:ReactNode}) {return <span className={passed?'status good':'status bad'}>{passed?<Check size={15}/>:<CircleAlert size={15}/>} {children}</span>;}
