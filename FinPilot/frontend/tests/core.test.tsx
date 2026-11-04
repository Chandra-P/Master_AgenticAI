import React from 'react';
import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { currency, validateScenario } from '../lib/format';
import { ResourceState } from '../components/ui';

test('currency distinguishes missing evidence from zero',()=>{
 expect(currency(null)).toBe('Not available');
 expect(currency('0')).toBe('$0');
 expect(currency('60000')).toBe('$60,000');
});
test('scenario rejects negative and non-finite inputs',()=>{
 expect(validateScenario({monthly_payment:'-1'})).toBeTruthy();
 expect(validateScenario({income_reduction_pct:'101'})).toBeTruthy();
 expect(validateScenario({cash_purchase:'NaN'})).toBeTruthy();
 expect(validateScenario({monthly_payment:'600'})).toBeNull();
});
test('loading is announced to assistive technology',()=>{
 render(<ResourceState loading error={null}/>);
 expect(screen.getByRole('status')).toHaveTextContent('Loading');
});
test('errors include a retry action',()=>{
 render(<ResourceState loading={false} error="API unavailable" retry={()=>{}}/>);
 expect(screen.getByRole('alert')).toHaveTextContent('API unavailable');
 expect(screen.getByRole('button',{name:'Try again'})).toBeInTheDocument();
});

test('document dialog traps focus and restores its trigger',async()=>{
 const { vi }=await import('vitest');
 const { fireEvent, waitFor }=await import('@testing-library/react');
 const { Documents }=await import('../components/finance-pages');
 const doc={id:'loan',title:'Loan evidence',version:1,effective_date:'2026-10-01',superseded_by:null,metadata:{synthetic:true,quarantined_sections:0},chunks:[{page:1,section:'Offer',content:'SYNTHETIC APR: 6.49%'}]};
 vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.endsWith('/loan')?doc:{items:[doc]}),{status:200,headers:{'content-type':'application/json'}})));
 render(<Documents/>);
 const trigger=await screen.findByRole('button',{name:/Loan evidence/});
 trigger.focus();fireEvent.click(trigger);
 const dialog=await screen.findByRole('dialog');
 const close=screen.getByRole('button',{name:'Close'});
 expect(close).toHaveFocus();
 fireEvent.keyDown(dialog,{key:'Tab'});
 expect(close).toHaveFocus();
 fireEvent.keyDown(dialog,{key:'Escape'});
 await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
 expect(trigger).toHaveFocus();
 vi.unstubAllGlobals();
});
