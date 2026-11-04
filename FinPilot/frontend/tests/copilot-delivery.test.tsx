import React from 'react';
import { expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { Copilot } from '../components/intelligence-pages';

test('the same suggested question can be delivered again after consumption',async()=>{
 Object.defineProperty(HTMLElement.prototype,'scrollIntoView',{configurable:true,value:()=>{}});
 let count=0;
 vi.stubGlobal('fetch',async()=>{
  count++;
  return new Response(JSON.stringify({id:`answer-${count}`,question:'How much did I spend last month?',summary:`Reviewed answer ${count}`,route:'sql',mode:'deterministic',completeness:'complete evidence',facts:[],sources:[],scenarios:[],events:[],tools:[],validation:{passed:true,checks:[],errors:[]},latency_ms:1,assumptions:[],limitations:[],tracing:'local only'}),{status:200});
 });
 const consumed=vi.fn();const question='How much did I spend last month?';
 const view=render(<Copilot initialQuestion={question} onConsumed={consumed}/>);
 expect(await screen.findByText('Reviewed answer 1')).toBeVisible();
 view.rerender(<Copilot initialQuestion="" onConsumed={consumed}/>);
 view.rerender(<Copilot initialQuestion={question} onConsumed={consumed}/>);
 expect(await screen.findByText('Reviewed answer 2')).toBeVisible();
 vi.unstubAllGlobals();
});
