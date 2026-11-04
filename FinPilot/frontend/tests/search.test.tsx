import React from 'react';
import { expect, test, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { QuickSearch } from '../components/quick-search';

test('quick search opens by keyboard and navigates to a matching page',async()=>{
 const navigate=vi.fn();render(<QuickSearch navigate={navigate} ask={()=>{}}/>);
 fireEvent.keyDown(window,{key:'k',ctrlKey:true});
 const input=await screen.findByRole('combobox',{name:'Search FinPilot pages and questions'});
 expect(input).toHaveFocus();
 fireEvent.change(input,{target:{value:'Tax Planning'}});
 fireEvent.keyDown(input,{key:'Enter'});
 expect(navigate).toHaveBeenCalledWith('Tax Planning');
 expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});
test('quick search honestly reports no results and restores keyboard focus',async()=>{
 render(<QuickSearch navigate={()=>{}} ask={()=>{}}/>);
 const trigger=screen.getByRole('button',{name:'Search FinPilot'});
 trigger.focus();fireEvent.click(trigger);
 const input=await screen.findByRole('combobox');
 fireEvent.change(input,{target:{value:'zzzz-not-a-feature'}});
 expect(screen.getByText('No matching pages or questions')).toBeVisible();
 fireEvent.keyDown(window,{key:'Escape'});
 await waitFor(()=>expect(trigger).toHaveFocus());
});
test('question search opens the real Copilot flow and traps tab focus',async()=>{
 const ask=vi.fn();render(<QuickSearch navigate={()=>{}} ask={ask}/>);
 fireEvent.click(screen.getByRole('button',{name:'Search FinPilot'}));
 const input=await screen.findByRole('combobox');
 fireEvent.change(input,{target:{value:'withholding'}});
 fireEvent.keyDown(input,{key:'ArrowDown'});
 fireEvent.keyDown(input,{key:'ArrowUp'});
 const close=screen.getByRole('button',{name:'Close quick search'});
 close.focus();fireEvent.keyDown(close,{key:'Tab'});
 expect(input).toHaveFocus();
 fireEvent.keyDown(input,{key:'Enter'});
 expect(ask).toHaveBeenCalledWith('Am I withholding enough federal tax?');
});
