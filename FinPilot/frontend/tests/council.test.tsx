import React from 'react';
import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { CouncilView } from '../components/council';
import type { Council } from '../lib/types';

const council:Council={mode:'demo',status:'held',disagreement:true,latency_ms:12,reconciliation:'Recommendation held for review.',reviews:[{role:'Evidence reviewer',model:'simulated policy',simulated:true,verdict:'approve',concerns:[],evidence_refs:['validation'],error:null},{role:'Constraint reviewer',model:'simulated policy',simulated:true,verdict:'caution',concerns:['constraints'],evidence_refs:['scenario:0'],error:null},{role:'Assumption reviewer',model:'simulated policy',simulated:true,verdict:'unavailable',concerns:[],evidence_refs:[],error:'Review unavailable (TimeoutError); no simulated replacement.'}]};

test('council shows simulation, disagreement, objections and unavailable member honestly',()=>{
 render(<CouncilView council={council}/>);
 expect(screen.getByRole('heading',{name:'Model council'})).toBeVisible();
 expect(screen.getByText(/Simulated reviews · no model calls/)).toBeVisible();
 expect(screen.getByText('Reviewers disagree')).toBeVisible();
 expect(screen.getByText('Recommendation held for review.')).toBeVisible();
 expect(screen.getByText('Constraint warnings')).toBeVisible();
 expect(screen.getByText(/Review unavailable \(TimeoutError\)/)).toBeVisible();
 expect(screen.getByText(/Agreement is not a confidence score/)).toBeVisible();
});

test('disabled council adds no review panel',()=>{
 const {container}=render(<CouncilView council={{...council,status:'off'}}/>);
 expect(container).toBeEmptyDOMElement();
});
