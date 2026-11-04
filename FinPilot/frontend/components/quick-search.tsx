'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Command, CornerDownLeft, Search, Sparkles, X } from 'lucide-react';
import { navigation, searchQuestions } from '../lib/navigation';

export function QuickSearch({navigate,ask}:{navigate:(page:string)=>void;ask:(question:string)=>void}) {
 const [open,setOpen]=useState(false);
 const [query,setQuery]=useState('');
 const [active,setActive]=useState(0);
 const input=useRef<HTMLInputElement>(null);
 const closeButton=useRef<HTMLButtonElement>(null);
 const previousFocus=useRef<HTMLElement|null>(null);
 const show=useCallback(()=>{previousFocus.current=document.activeElement as HTMLElement;setQuery('');setActive(0);setOpen(true);},[]);
 const close=useCallback(()=>{setOpen(false);if(previousFocus.current?.isConnected)previousFocus.current.focus();},[]);
 useEffect(()=>{
  function keys(event:KeyboardEvent){
   if((event.ctrlKey||event.metaKey)&&!event.altKey&&event.key.toLowerCase()==='k'){
    event.preventDefault();if(!event.repeat){if(open)close();else show();}
   }else if(open&&event.key==='Escape'){event.preventDefault();close();}
  }
  window.addEventListener('keydown',keys);return()=>window.removeEventListener('keydown',keys);
 },[open,show,close]);
 useEffect(()=>{if(!open)return;input.current?.focus();const before=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{document.body.style.overflow=before;};},[open]);
 const search=query.trim().toLowerCase();
 const pages=navigation.filter(page=>`${page.name} ${page.description}`.toLowerCase().includes(search));
 const questions=searchQuestions.filter(item=>`${item.question} ${item.keywords}`.toLowerCase().includes(search));
 const options=[...pages.map(page=>({label:page.name,description:page.description,icon:page.icon,kind:'page' as const})),...questions.map(item=>({label:item.question,description:'Ask FinPilot Copilot',icon:Sparkles,kind:'question' as const}))];
 const selected=Math.min(active,Math.max(0,options.length-1));
 useEffect(()=>{if(open)document.getElementById(`command-option-${selected}`)?.scrollIntoView?.({block:'nearest'});},[open,selected,query]);
 function choose(index:number){const option=options[index];if(!option)return;close();if(option.kind==='page')navigate(option.label);else ask(option.label);}
 return <><button className="quick-search-trigger" onClick={show} aria-label="Search FinPilot"><Search size={16}/><span>Search workspace</span><kbd><Command size={10}/> K</kbd></button>{open&&<div className="command-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)close();}}><section className="command-dialog" data-command-palette role="dialog" aria-modal="true" aria-labelledby="command-title" onKeyDown={event=>{
  if(event.key==='Tab'){
   if(event.shiftKey&&document.activeElement===input.current){event.preventDefault();closeButton.current?.focus();}
   else if(!event.shiftKey&&document.activeElement===closeButton.current){event.preventDefault();input.current?.focus();}
  }
 }}><h2 id="command-title" className="sr-only">Quick search</h2><div className="command-input-row"><Search size={21}/><input ref={input} role="combobox" aria-label="Search FinPilot pages and questions" aria-controls="command-results" aria-expanded="true" aria-autocomplete="list" aria-activedescendant={options.length?`command-option-${selected}`:undefined} placeholder="Find a page or suggested question…" value={query} maxLength={100} onChange={event=>{setQuery(event.target.value);setActive(0);}} onKeyDown={event=>{
  if(event.key==='ArrowDown'){event.preventDefault();setActive(options.length?(selected+1)%options.length:0);}
  if(event.key==='ArrowUp'){event.preventDefault();setActive(options.length?(selected-1+options.length)%options.length:0);}
  if(event.key==='Enter'){event.preventDefault();choose(selected);}
 }}/><button ref={closeButton} className="icon-button" onClick={close} aria-label="Close quick search"><X size={18}/></button></div><div className="command-caption">{search?'MATCHING PAGES & QUESTIONS':'YOUR WORKSPACE AT A GLANCE'}</div><div id="command-results" className="command-results" role="listbox" aria-label="Search results">{options.map((option,index)=><button id={`command-option-${index}`} role="option" aria-selected={index===selected} tabIndex={-1} className={`command-option ${index===selected?'active':''}`} key={option.label} onMouseEnter={()=>setActive(index)} onClick={()=>choose(index)}><span className="command-option-icon"><option.icon size={18}/></span><span><strong>{option.label}</strong><small>{option.description}</small></span>{option.kind==='question'?<ArrowUpRight size={15}/>:<CornerDownLeft size={14}/>}</button>)}{!options.length&&<div className="command-empty" role="status"><Search size={24}/><h3>No matching pages or questions</h3><p>Try “tax”, “documents”, or “goals”.</p></div>}</div><div className="command-footer"><span><kbd>↑</kbd><kbd>↓</kbd> to move <kbd>↵</kbd> to open</span><span><kbd>esc</kbd> to close</span></div></section></div>}</>;
}
