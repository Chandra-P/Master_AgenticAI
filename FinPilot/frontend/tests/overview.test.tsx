import React from 'react';
import { afterEach, expect, test, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { Overview } from '../components/overview';
import original from './fixtures/dashboard.json';

afterEach(()=>{vi.unstubAllGlobals();vi.restoreAllMocks();});
function data(){
 const d=structuredClone(original);d.user='Pat Morgan';d.cash.value='72000.00';d.memory.emergency_fund_minimum='31000.00';d.goals.items[0].current_amount='27500.00';d.goals.items[0].target_amount='65000.00';d.baseline_projection.baseline.unallocated_cash='13500.00';d.baseline_projection.goal_impact.projected_months=10;
 vi.stubGlobal('fetch',async()=>new Response(JSON.stringify(d),{status:200}));
 vi.stubGlobal('ResizeObserver',class {observe(){} unobserve(){} disconnect(){}});
 vi.spyOn(HTMLElement.prototype,'getBoundingClientRect').mockReturnValue({x:0,y:0,top:0,left:0,right:900,bottom:260,width:900,height:260,toJSON(){return {};}});
 return d;
}
test('modern dashboard uses actual cash, constraints and goal values',async()=>{
 data();render(<Overview navigate={()=>{}} ask={()=>{}}/>);
 expect(await screen.findByText('$72,000',{exact:true})).toBeVisible();
 expect(screen.getByText('$31,000',{exact:true})).toBeVisible();
 expect(screen.getByText('$13,500',{exact:true})).toBeVisible();
 expect(screen.getByText(/Welcome back, Pat/)).toBeVisible();
 expect(screen.getByRole('progressbar',{name:'House down-payment progress'})).toHaveAttribute('aria-valuenow','42');
 expect(screen.queryByText('$50,000',{exact:true})).not.toBeInTheDocument();
});
test('decision and tax shortcuts invoke existing application flows',async()=>{
 data();const ask=vi.fn(),navigate=vi.fn();render(<Overview navigate={navigate} ask={ask}/>);
 fireEvent.click(await screen.findByRole('button',{name:'Explore the car decision'}));
 expect(ask).toHaveBeenCalledWith(expect.stringContaining('current loan offer'));
 fireEvent.click(screen.getByRole('button',{name:'Open Tax Planning'}));
 expect(navigate).toHaveBeenCalledWith('Tax Planning');
});

test('missing goals and projection preserve available financial cards',async()=>{
 const d=data();d.goals.items=[];
 vi.stubGlobal('fetch',async()=>new Response(JSON.stringify({...d,baseline_projection:null,projection_unavailable_reason:'Missing goal data'}),{status:200}));
 render(<Overview navigate={()=>{}} ask={()=>{}}/>);
 expect(await screen.findByText('A direction worth defining')).toBeVisible();
 expect(screen.getByText('$72,000',{exact:true})).toBeVisible();
 expect(screen.getAllByText('Not available')).toHaveLength(2);
});
