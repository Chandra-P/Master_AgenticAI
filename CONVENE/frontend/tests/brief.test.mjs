import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

const compiled=await build({entryPoints:[fileURLToPath(new URL('../src/BriefSummary.tsx',import.meta.url))],bundle:true,write:false,platform:'node',format:'cjs',jsx:'automatic'});
const module={exports:{}};
new Function('module','exports','require',compiled.outputFiles[0].text)(module,module.exports,createRequire(import.meta.url));
const {BriefSummary}=module.exports;
const brief={occasion:'birthday',services:['venue','decoration'],age:8,children:20,family:20,
  event_date:'2026-12-06',date_flexibility:null,time_window:'Afternoon',budget:'800',
  priorities:'Keep everyone invited',theme:'dinosaur',tentative_fields:['family','event_date'],explicit_unknown:[]};

test('parent review exposes age, guest breakdown, priorities and aggregate uncertainty',()=>{
  const html=renderToStaticMarkup(React.createElement(BriefSummary,{brief}));
  assert.match(html,/<dt>Birthday age<\/dt><dd>8<\/dd>/);
  assert.match(html,/<dt>Children<\/dt><dd>20<\/dd>/);
  assert.match(html,/<dt>Accompanying adults \/ family<\/dt><dd>20<span class="tag">Tentative/);
  assert.match(html,/<dt>All guests<\/dt><dd>40<span class="tag">Tentative/);
  assert.match(html,/Keep everyone invited/);
  assert.match(html,/2026-12-06<span class="tag">Tentative/);
});

test('unknown budget is not zero and food-specific review follows chosen services',()=>{
  const html=renderToStaticMarkup(React.createElement(BriefSummary,{brief:{...brief,budget:null,services:['food'],dietary_needs:'Peanut allergy',food_fulfilment:'delivery'}}));
  assert.match(html,/<dt>Total budget<\/dt><dd>Not decided/);
  assert.match(html,/Peanut allergy/);
  assert.match(html,/delivery/);
  assert.doesNotMatch(html,/<dt>Theme/);
});
