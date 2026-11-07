import {test,expect} from '@playwright/test';
import {addDraftIdea,cityIdeaSuggestions,reviewedSuggestion,hasIdeaCity,type IdeaSuggestion} from '../src/services/idea-discovery';

const idea=(id:string):IdeaSuggestion=>({id,name:'Reviewed idea '+id,details:'Verify with the provider.',url:'https://example.com/'+id,source_ids:['source-'+id],category:'Place idea'});

test('the guided summary and discovery agree on missing city placeholders',()=>{
 for(const city of ['', 'to decide','Somewhere together','Location to decide','TBD','unknown'])expect(hasIdeaCity(city)).toBe(false);
 expect(hasIdeaCity(' San Francisco ')).toBe(true);
});

test('reviewed idea selection deduplicates and stays within the eight-idea draft limit',()=>{
 let selected:IdeaSuggestion[]=[];
 for(let index=0;index<12;index++)selected=addDraftIdea(selected,idea(String(index)));
 expect(selected).toHaveLength(8);
 expect(addDraftIdea(selected,selected[0])).toBe(selected);
 expect(selected.map(item=>item.id)).toEqual(['0','1','2','3','4','5','6','7']);
});

test('event search dates survive review while private URLs and images cannot enter a draft',()=>{
 const suggestions=cityIdeaSuggestions({places:[idea('place')],events:[{...idea('event'),date:'2027-04-17'}],sources:[],steps:[]});
 expect(suggestions[1].category).toBe('Event idea');
 expect(reviewedSuggestion(suggestions[1])).toEqual({title:'Reviewed idea event',url:'https://example.com/event',category:'Event idea',day:'2027-04-17'});
 expect(reviewedSuggestion({...idea('private'),url:'http://localhost/internal'})).toBeNull();
 expect(reviewedSuggestion({...idea('image'),image:'http://127.0.0.1/private'})).not.toHaveProperty('image');
});

test('different searches cannot confuse response-relative IDs or lose evidence on review',()=>{
 const first=cityIdeaSuggestions({places:[idea('external:1')],events:[],sources:[],steps:[]})[0];
 const provenance={url:'https://example.com/other',retrievedAt:'2027-04-01T10:00:00Z',excerpt:'Official page excerpt'};
 const second=cityIdeaSuggestions({places:[{...idea('external:1'),url:provenance.url,provenance}],events:[],sources:[],steps:[]})[0];
 expect(addDraftIdea([first],second)).toHaveLength(2);
 expect(reviewedSuggestion(second)?.provenance).toEqual(provenance);
});
