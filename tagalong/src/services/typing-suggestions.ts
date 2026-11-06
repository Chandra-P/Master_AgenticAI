import type {Plan} from './types';

const commonPlanning=[
 'We should meet at the entrance.', 'We could meet after lunch.',
 'We can decide together.', 'Can everyone confirm the time?',
 'What time works for everyone?', 'We should book a table.',
 'Let us check the weather.', 'We need to set a budget.',
 'How about dinner together?', 'I can help with transport.',
 'We should compare our options.', 'Where should we stay?',
 'I want to plan our trip.', "Let's fly instead.",
 'Find restaurants nearby.', 'We can explore places together.',
 'I would like to visit the park.', 'Can we choose a restaurant?',
 'We need transport and accommodation.', 'What is our budget?',
];
const normalize=(word:string)=>word.toLocaleLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu,'');
const matchingWord=(word:string)=>normalize(word).replace(/[’']/g,'');
const isWord=(word:string)=>word.length<=48&&/^[\p{L}]+(?:[’'-][\p{L}]+)*[.,!?]?$/u.test(word);

function suggestionCorpus(plan:Plan):string[][] {
 const context=plan.location?[`Dinner at ${plan.location}.`,`Meet in ${plan.location}.`]:[];
 let remaining=10000;
 const corpus:string[][]=[];
 for(const line of [...commonPlanning,...context,...plan.messages.slice(-100).reverse().map(message=>message.text)]) {
  if(remaining<=0)break;
  const bounded=line.slice(0,remaining);remaining-=bounded.length;
  corpus.push(bounded.split(/\s+/).filter(Boolean));
 }
 return corpus;
}

/** Deliberately local: only this plan contributes history, and no draft is sent. */
export function suggestContinuation(text:string,plan:Plan):string {
 if(text.length<2||text.length>=2000||/\n/.test(text))return '';
 // A mention routes a message; it is not part of what the person is writing.
 // Match without it, but return only the suffix to append to the original draft.
 const draft=text.replace(/^\s*@tagalong\s+/i,'').trimStart();
 if(draft.length<2)return '';
 const phrases=["Let's plan ","What time works for everyone?",'Should we book a table?',
  'How about dinner together?',"I'm happy with that plan.",'Can everyone confirm their availability?',
  ...(plan.location?[`Let's explore ${plan.location}.`,`How about ${plan.location}?`]:[]),
  ...plan.members.map(member=>`Thanks ${member.name}!`),
  ...(plan.kind==='trip'?["Let's plan our trip.",'What should we pack?','Where should we stay?']:['Where should we meet?'])];
 const phrase=phrases.find(candidate=>candidate.toLocaleLowerCase().startsWith(draft.toLocaleLowerCase())&&candidate.length>draft.length);
 if(phrase)return phrase.slice(draft.length,draft.length+2000-text.length);

 // Match the last two completed words first, then one, including a partial
 // next word. Suggest a single observed token rather than generating facts.
 const parts=draft.match(/^([\s\S]*?)(\S*)$/);
 if(!parts)return '';
 const completed=parts[1].trim().split(/\s+/).filter(Boolean).map(matchingWord);
 const partial=parts[2].toLocaleLowerCase();
 const corpus=suggestionCorpus(plan);
 for(const size of [2,1]) {
  if(completed.length<size)continue;
  const suffix=completed.slice(-size);
  for(const words of corpus) {
   for(let index=size;index<words.length;index++) {
    const candidate=words[index];
    if(!isWord(candidate)||!candidate.toLocaleLowerCase().startsWith(partial)||candidate.length<=partial.length)continue;
    if(suffix.every((word,offset)=>word===matchingWord(words[index-size+offset]))) {
     return (candidate.slice(partial.length)+' ').slice(0,2000-text.length);
    }
   }
  }
 }
 // With a partial word, a local vocabulary completion is useful even when
 // the surrounding sentence is new. Never guess a next word for unknown text.
 if(partial.length>=2&&/^[\p{L}]+$/u.test(partial)) {
  for(const words of corpus)for(const candidate of words) {
   if(isWord(candidate)&&candidate.toLocaleLowerCase().startsWith(partial)&&candidate.length>partial.length)
    return (candidate.slice(partial.length)+' ').slice(0,2000-text.length);
  }
 }
 return '';
}
