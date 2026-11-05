import type {Plan} from './types';

const commonPlanning=[
 'We should meet at the entrance.', 'We could meet after lunch.',
 'We can decide together.', 'Can everyone confirm the time?',
 'What time works for everyone?', 'We should book a table.',
 'Let us check the weather.', 'We need to set a budget.',
 'How about dinner together?', 'I can help with transport.',
 'We should compare our options.', 'Where should we stay?',
];
const normalize=(word:string)=>word.toLocaleLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu,'');

/** Deliberately local: only this plan contributes history, and no draft is sent. */
export function suggestContinuation(text:string,plan:Plan):string {
 if(text.length<2||text.length>=2000||/\n/.test(text))return '';
 const phrases=["Let's plan ","What time works for everyone?",'Should we book a table?',
  'How about dinner together?',"I'm happy with that plan.",'Can everyone confirm their availability?',
  ...(plan.location?[`Let's explore ${plan.location}.`,`How about ${plan.location}?`]:[]),
  ...plan.members.map(member=>`Thanks ${member.name}!`),
  ...(plan.kind==='trip'?["Let's plan our trip.",'What should we pack?','Where should we stay?']:['Where should we meet?'])];
 const phrase=phrases.find(candidate=>candidate.toLocaleLowerCase().startsWith(text.toLocaleLowerCase())&&candidate.length>text.length);
 if(phrase)return phrase.slice(text.length,2000);

 // Match the last two completed words first, then one, including a partial
 // next word. Suggest a single observed token rather than generating facts.
 const parts=text.match(/^([\s\S]*?)(\S*)$/);
 if(!parts)return '';
 const completed=parts[1].trim().split(/\s+/).filter(Boolean).map(normalize);
 if(!completed.length)return '';
 const partial=parts[2].toLocaleLowerCase();
 const context=plan.location?[`Dinner at ${plan.location}.`,`Meet in ${plan.location}.`]:[];
 let remaining=10000;
 const corpus:string[][]=[];
 for(const line of [...commonPlanning,...context,...plan.messages.slice(-100).reverse().map(message=>message.text)]) {
  if(remaining<=0)break;
  const bounded=line.slice(0,remaining);remaining-=bounded.length;
  corpus.push(bounded.split(/\s+/).filter(Boolean));
 }
 for(const size of [2,1]) {
  if(completed.length<size)continue;
  const suffix=completed.slice(-size);
  for(const words of corpus) {
   for(let index=size;index<words.length;index++) {
    const candidate=words[index];
    if(candidate.length>48||!candidate.toLocaleLowerCase().startsWith(partial)||candidate.length<=partial.length)continue;
    if(suffix.every((word,offset)=>word===normalize(words[index-size+offset]))) {
     return (candidate.slice(partial.length)+' ').slice(0,2000-text.length);
    }
   }
  }
 }
 return '';
}
