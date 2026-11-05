import {test,expect} from '@playwright/test';
import {simulatedAssistant} from '../src/services/mock-planning-service';

test('demo budget attribution answers the question without inventing a person or preferences',()=>{
 const answer=simulatedAssistant.reply('@@Tagalong who set budgt');
 expect(answer.text).toContain('sample budgets automatically');
 expect(answer.text).toContain('does not record who last changed');
 expect(answer.text).toContain('shared workspace');
 expect(answer.preferences).toEqual([]);
});

test('unsupported demo questions explain the simulation instead of proposing unrelated preferences',()=>{
 const answer=simulatedAssistant.reply('@Tagalong who invited Jamie?');
 expect(answer.text).toContain('scripted demo');
 expect(answer.preferences).toEqual([]);
});
