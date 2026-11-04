import React from 'react';
import { afterEach, expect, test, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { TaxPlanning } from '../components/tax-planning';
import fixture from './fixtures/tax.json';

afterEach(()=>vi.unstubAllGlobals());
function backend(){
 vi.stubGlobal('fetch',vi.fn(async(path:string,init?:RequestInit)=>{
  const data=path.endsWith('/profile')?fixture.profile:path.endsWith('/projection')?fixture.projection:path.endsWith('/paystubs')?fixture.paystubs:path.endsWith('/strategy')&&init?.method==='POST'?fixture.strategy:{};
  return new Response(JSON.stringify(data),{status:200,headers:{'content-type':'application/json'}});
 }));
}
test('tax planning announces loading without fabricated figures',()=>{
 vi.stubGlobal('fetch',()=>new Promise(()=>{}));
 render(<TaxPlanning/>);
 expect(screen.getByRole('status')).toHaveTextContent('Loading');
 expect(screen.queryByText('$14,020.00')).not.toBeInTheDocument();
});
test('tax API failure is visible and retryable',async()=>{
 vi.stubGlobal('fetch',async()=>new Response(JSON.stringify({detail:'Tax service unavailable'}),{status:503}));
 render(<TaxPlanning/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('Tax service unavailable');
 expect(screen.getByRole('button',{name:'Try again'})).toBeInTheDocument();
});
test('tax planning displays scope, withholding distinction and exact figures',async()=>{
 backend();render(<TaxPlanning/>);
 expect(await screen.findByText('$2,137.60',{exact:true})).toBeVisible();
 expect(screen.getAllByText('$14,020.00',{exact:true})[0]).toBeVisible();
 expect(screen.getByText('Lower tax and different withholding are different decisions.')).toBeVisible();
 expect(screen.getByText(/Texas has no individual state income tax/)).toBeVisible();
 expect(screen.getByRole('link',{name:/Download synthetic sample paystub/})).toHaveAttribute('href','/sample-paystub.txt');
});
test('strategy result separates cash take-home reduction from tax savings',async()=>{
 backend();render(<TaxPlanning/>);
 const run=await screen.findByRole('button',{name:'Compare tax strategy'});
 fireEvent.click(run);
 expect(await screen.findByText('$220.00',{exact:true})).toBeVisible();
 expect(screen.getByText('$1,000.00',{exact:true})).toBeVisible();
 expect(screen.getByText('$780.00',{exact:true})).toBeVisible();
 expect(screen.getByText('Modeled take-home reduction')).toBeVisible();
 expect(screen.getByText(/does not subtract gross contributions again/)).toBeVisible();
});

test('editing payroll changes clears the old validated comparison',async()=>{
 backend();render(<TaxPlanning/>);
 fireEvent.click(await screen.findByRole('button',{name:'Compare tax strategy'}));
 expect(await screen.findByText('$220.00',{exact:true})).toBeVisible();
 fireEvent.change(screen.getByLabelText('Extra traditional 401(k) ($)'),{target:{value:'300'}});
 expect(screen.queryByText('$220.00',{exact:true})).not.toBeInTheDocument();
 expect(screen.queryByText('Deterministic checks passed',{exact:true})).not.toBeInTheDocument();
});
