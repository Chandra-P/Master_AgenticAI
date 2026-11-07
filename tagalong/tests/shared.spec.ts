import {openTool} from './planning-tools';
import {test,expect,type Page,type BrowserContext} from '@playwright/test';

async function login(page:Page,name:'alice'|'bob',role:'member'|'admin'='member'){
 const config=await (await page.request.get('/api/config')).json();
 expect(config.supabaseUrl).toBe('https://tagalong-test.supabase.co');
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-'+name,refresh_token:'refresh-'+name,token_type:'bearer',expires_in:3600,user:{id:name,email:name+'@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');
 await page.getByRole('radio',{name:role==='admin'?'Admin':'Member',exact:true}).check();
 await page.getByLabel('Email address').fill(name+'@example.test');
 await page.getByLabel('Password',{exact:true}).fill('test-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
 await expect(page.getByText('Current role: '+(role==='admin'?'Admin':'Member'),{exact:true})).toBeVisible();
}

test('decision consent and contextual comments persist across members and finalization is durable',async({page})=>{
 test.setTimeout(120000);await login(page,'alice');
 const alice={Authorization:'Bearer test-alice'},bob={Authorization:'Bearer test-bob'};
 await page.request.get('/api/backend/v1/me',{headers:bob});
 const created=await page.request.post('/api/backend/v1/plans',{headers:alice,data:{title:'Decision dinner '+crypto.randomUUID().slice(0,8),kind:'outing',start:'2027-05-14',end:'2027-05-14'}});
 expect(created.ok()).toBeTruthy();const plan=await created.json();const base='/api/backend/v1/plans/'+plan.id;
 expect((await page.request.get(base+'/decisions',{headers:bob})).status()).toBe(404);
 expect((await page.request.post(base+'/members',{headers:alice,data:{email:'bob@example.test'}})).ok()).toBeTruthy();
 let snapshot=await(await page.request.get(base+'/decisions',{headers:alice})).json();
 expect(snapshot.score).toBe(0);expect(snapshot.finalized).toBe(false);
 for(const initial of snapshot.decisions){
  let decision=snapshot.decisions.find((d:{id:string})=>d.id===initial.id);
  const edited=await page.request.patch(base+'/decisions/'+decision.id,{headers:alice,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,options:['Reviewed '+decision.title]}});expect(edited.ok()).toBeTruthy();snapshot=await edited.json();decision=snapshot.decisions.find((d:{id:string})=>d.id===initial.id);
  const option=decision.options[0].id;
  const response=await page.request.put(base+'/decisions/'+decision.id+'/response',{headers:alice,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,option_id:option,response:'support'}});expect(response.ok()).toBeTruthy();snapshot=await response.json();
  const premature=await page.request.post(base+'/decisions/'+decision.id+'/confirm',{headers:alice,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,option_id:option}});expect(premature.status()).toBe(409);
  const second=await page.request.put(base+'/decisions/'+decision.id+'/response',{headers:bob,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,option_id:option,response:'can_live_with'}});expect(second.ok()).toBeTruthy();snapshot=await second.json();
  const confirmed=await page.request.post(base+'/decisions/'+decision.id+'/confirm',{headers:alice,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,option_id:option}});expect(confirmed.ok()).toBeTruthy();snapshot=await confirmed.json();
 }
 expect(snapshot.score).toBe(99);
 const decision=snapshot.decisions[0];const text='Parking seems difficult downtown.';
 const commented=await page.request.post(base+'/decisions/'+decision.id+'/comments',{headers:bob,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version,text}});expect(commented.ok()).toBeTruthy();snapshot=await commented.json();
 expect(snapshot.comments[0].authorId).toBe('bob');
 const payload={expected_revision:snapshot.plan_revision,reviewed:true,idempotency_key:crypto.randomUUID()};
 expect((await page.request.post(base+'/finalize',{headers:bob,data:payload})).status()).toBe(403);
 const finalized=await page.request.post(base+'/finalize',{headers:alice,data:payload});expect(finalized.ok()).toBeTruthy();snapshot=await finalized.json();expect(snapshot.score).toBe(100);
 expect((await(await page.request.post(base+'/finalize',{headers:alice,data:payload})).json()).finalization).toEqual(snapshot.finalization);
 await page.goto('/plans/'+plan.id);await expect(page.getByRole('tab',{name:'Decisions',exact:true})).toHaveAttribute('aria-selected','true');
 const card=page.getByRole('article').filter({has:page.getByRole('heading',{name:decision.title,exact:true})}).first();
 await card.getByRole('button',{name:'Summarize decision',exact:true}).click();
 await expect(card.getByRole('heading',{name:'AI decision summary',exact:true})).toBeVisible();
 await card.getByText(/Evidence used/).click();
 await expect(card.getByText('Decision: '+decision.title,{exact:true})).toBeVisible();
 await page.reload();await expect(page.getByRole('progressbar',{name:'Group consensus'}).first()).toHaveAttribute('aria-valuenow','100');
 const persisted=await(await page.request.get(base+'/decisions',{headers:bob})).json();expect(persisted.comments[0].text).toBe(text);
 const reopened=await page.request.post(base+'/decisions/'+decision.id+'/reopen',{headers:alice,data:{expected_revision:snapshot.plan_revision,expected_version:decision.version}});expect(reopened.ok()).toBeTruthy();const next=await reopened.json();expect(next.finalized).toBe(false);expect(next.score).toBeLessThan(100);
});

test('real MCP demo books once, persists to the shared itinerary, and cancels without real reservations',async({page})=>{
 test.setTimeout(120000);
 await login(page,'alice');
 const a={Authorization:'Bearer test-alice'},b={Authorization:'Bearer test-bob'};
 const created=await page.request.post('/api/backend/v1/plans',{headers:a,data:{title:'MCP restaurant demo '+crypto.randomUUID().slice(0,8),kind:'trip',start:'2027-05-14',end:'2027-05-16'}});expect(created.ok()).toBeTruthy();const plan=await created.json();
 expect((await page.request.get('/api/backend/v1/me',{headers:b})).ok()).toBeTruthy();
 expect((await page.request.post('/api/backend/v1/plans/'+plan.id+'/members',{headers:a,data:{email:'bob@example.test'}})).ok()).toBeTruthy();
 await page.goto('/plans/'+plan.id+'?tab=Demo%20bookings');
 await expect(page.getByText('Demo reservation—no real booking or charge',{exact:true})).toBeVisible();
 await expect(page.getByText('Complete group agreement before confirming a reservation.',{exact:true})).toBeVisible();
 const planPath='/api/backend/v1/plans/'+plan.id;
 async function change(headers:Record<string,string>,patches:unknown[]){const current=await(await page.request.get(planPath,{headers})).json();const response=await page.request.patch(planPath,{headers,data:{expected_revision:current.revision,patches}});expect(response.ok(),await response.text()).toBeTruthy();}
 const current=await(await page.request.get(planPath,{headers:a})).json();
 const alice=current.members.find((m:{user_id:string})=>m.user_id==='alice').name;
 const bob=current.members.find((m:{user_id:string})=>m.user_id==='bob').name;
 await change(a,[{op:'replace',path:['location'],value:'San Francisco'},{op:'replace',path:['budget'],value:500},{op:'add',path:['polls',0,'votes',alice],value:0}]);
 await change(b,[{op:'add',path:['polls',0,'votes',bob],value:0}]);
 const readyPlan=await(await page.request.get(planPath,{headers:a})).json();
 expect((await page.request.post(planPath+'/demo-bookings/approve',{headers:b,data:{confirmed:true,expected_revision:readyPlan.revision}})).status()).toBe(403);
 await page.reload();
 await page.getByRole('button',{name:'Approve group decisions',exact:true}).click();
 await expect(page.getByText('Group decisions approved. You can confirm a reservation.',{exact:true})).toBeVisible();
 await page.getByLabel('Demo city',{exact:true}).fill('San Francisco');await page.getByLabel('Demo party size',{exact:true}).fill('4');
 await page.getByRole('button',{name:'Search fictional restaurants',exact:true}).click();
 await page.getByRole('combobox',{name:'Restaurant',exact:true}).selectOption('demo-lantern');await page.getByRole('button',{name:'Demo slot 19:00',exact:true}).click();
 const quoteResponse=page.waitForResponse(r=>r.url().endsWith('/demo-bookings/quote')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Review demo reservation',exact:true}).click();const quote=await(await quoteResponse).json();expect(quote.simulation).toBe(true);
 await expect(page.getByRole('button',{name:'Confirm demo reservation',exact:true})).toBeVisible();
 const before=await(await page.request.get('/api/backend/v1/plans/'+plan.id+'/demo-bookings',{headers:a})).json();expect(before.bookings).toHaveLength(0);
 await page.getByRole('button',{name:'Confirm demo reservation',exact:true}).click();
 await expect(page.getByText(/DEMO-[A-F0-9]+ · confirmed/)).toBeVisible({timeout:30000});
 const list=await(await page.request.get('/api/backend/v1/plans/'+plan.id+'/demo-bookings',{headers:a})).json();expect(list.bookings).toHaveLength(1);const booking=list.bookings[0];
 const retry=await page.request.post('/api/backend/v1/plans/'+plan.id+'/demo-bookings/confirm',{headers:a,data:{quote_id:quote.quote.id,confirmed:true}});expect(retry.ok()).toBeTruthy();expect((await retry.json()).booking.id).toBe(booking.id);
 const saved=await(await page.request.get('/api/backend/v1/plans/'+plan.id,{headers:a})).json();expect(saved.itinerary.filter((x:{id:string})=>x.id===booking.itinerary_entry_id)).toHaveLength(1);
 await page.getByText('MCP activity trace',{exact:true}).click();await expect(page.locator('details').filter({hasText:'MCP activity trace'})).toContainText('create_demo_booking');
 await page.screenshot({path:'test-results-shared/demo-booking-'+test.info().project.name+'.png',fullPage:true});
 await page.reload();await expect(page.getByText(booking.reference+' · confirmed',{exact:true})).toBeVisible();
 const shared=await(await page.request.get('/api/backend/v1/plans/'+plan.id+'/demo-bookings',{headers:b})).json();expect(shared.bookings[0].reference).toBe(booking.reference);
 expect((await page.request.post('/api/backend/v1/plans/'+plan.id+'/demo-bookings/'+booking.id+'/cancel',{headers:b,data:{confirmed:true}})).status()).toBe(403);
 await page.getByRole('button',{name:'Cancel demo reservation '+booking.reference,exact:true}).click();await page.getByRole('button',{name:'Confirm cancellation',exact:true}).click();
 await expect(page.getByText(booking.reference+' · cancelled',{exact:true})).toBeVisible({timeout:30000});
 const cancelled=await(await page.request.get('/api/backend/v1/plans/'+plan.id+'/demo-bookings',{headers:a})).json();expect(cancelled.bookings[0].status).toBe('cancelled');
 const finalPlan=await(await page.request.get('/api/backend/v1/plans/'+plan.id,{headers:a})).json();expect(finalPlan.itinerary.some((x:{id:string})=>x.id===booking.itinerary_entry_id)).toBe(false);
});

test('connected typing suggests a continuation through the authenticated API without sending a message',async({page})=>{
 await login(page,'alice');
 const headers={Authorization:'Bearer test-alice'};
 const created=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Typing demo '+crypto.randomUUID().slice(0,8),kind:'outing',start:'2027-05-14',end:'2027-05-14'}});expect(created.ok()).toBeTruthy();const plan=await created.json();
 await page.goto('/plans/'+plan.id);
 await page.getByRole('tab',{name:'Chat',exact:true}).click();const draft=page.getByLabel('Message your group');
 const response=page.waitForResponse(r=>r.url().endsWith('/typing-suggestion')&&r.request().method()==='POST');
 await draft.fill('I want to explore');
 expect((await response).ok()).toBeTruthy();
 await expect(page.getByRole('button',{name:'Accept suggestion: together.',exact:true})).toBeVisible();
 await draft.press('Tab');
 await expect(draft).toHaveValue('I want to explore together.');
 const saved=await(await page.request.get('/api/backend/v1/plans/'+plan.id,{headers})).json();expect(saved.messages).toHaveLength(0);
});

test('group fit cites saved preferences and current budget without changing the plan',async({page})=>{
 await login(page,'alice');
 const headers={Authorization:'Bearer test-alice'};
 const created=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Group fit demo '+crypto.randomUUID().slice(0,8),kind:'outing',start:'2027-05-14',end:'2027-05-14'}});expect(created.ok()).toBeTruthy();const plan=await created.json();
 const base='/api/backend/v1/plans/'+plan.id;
 expect((await page.request.patch(base,{headers,data:{expected_revision:plan.revision,patches:[{op:'replace',path:['budget'],value:50},{op:'replace',path:['location'],value:'San Francisco'}]}})).ok()).toBeTruthy();
 expect((await page.request.post(base+'/documents',{headers,data:{title:'Group dinner preferences',text:'Synthetic group preference: vegetarian dinner and a step-free entrance.',content_type:'text/plain'}})).ok()).toBeTruthy();
 const before=await(await page.request.get(base,{headers})).json();
 await page.goto('/plans/'+plan.id+'?tab=Group%20fit');
 await page.getByLabel('Option name',{exact:true}).fill('Fictional Dinner');
 await page.getByLabel('Option details or menu',{exact:true}).fill('User-provided menu lists vegetarian dishes. Entrance access is unknown.');
 await page.getByLabel('Estimated cost per person',{exact:true}).fill('75');
 await page.getByRole('button',{name:'Check group fit',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Conflicts with the group',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Source: Group dinner preferences',exact:true}).click();
 await expect(page.getByText('Synthetic group preference: vegetarian dinner and a step-free entrance.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Source: Current plan facts',exact:true}).click();
 await page.screenshot({path:'test-results-shared/group-fit-'+test.info().project.name+'.png',fullPage:true});
 const after=await(await page.request.get(base,{headers})).json();
 expect(after.revision).toBe(before.revision);expect(after.itinerary).toEqual(before.itinerary);expect(after.messages).toEqual(before.messages);
});

test('reusable demo groups stay separate from connected membership and contacts',async({page})=>{
 const group={id:'private-local-group',name:'Private local group sentinel',theme:'Weekend friends',ownerId:'alex',archived:false,members:[{id:'alex',preferredName:'Alex',color:'#edc6b3'},{id:'local-person',preferredName:'Private Alias',color:'#bcd9cd',email:'hidden-contact@example.test'}]};
 await page.addInitScript(value=>localStorage.setItem('tagalong-groups-v1',JSON.stringify([value])),group);
 await login(page,'alice');
 const headers={Authorization:'Bearer test-alice'};
 const created=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Connected membership '+crypto.randomUUID().slice(0,8),kind:'outing',start:'2027-05-14',end:'2027-05-14'}});expect(created.ok()).toBeTruthy();const plan=await created.json();
 const bodies:string[]=[];page.on('request',request=>{if(request.url().includes('/api/backend/'))bodies.push(request.postData()||'');});
 await page.goto('/groups');
 await expect(page.getByRole('heading',{name:'Good company, on repeat.',exact:true})).toBeVisible();
 await expect(page.getByText(group.name,{exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Create a group',exact:true}).first()).toBeEnabled();
 const before=await(await page.request.get('/api/backend/v1/plans/'+plan.id,{headers})).json();expect(before.members).toHaveLength(1);
 await page.goto('/account');await page.getByRole('button',{name:'Explore the demo',exact:true}).click();await page.goto('/groups');
 await expect(page.getByRole('heading',{name:group.name,exact:true})).toBeVisible();
 const after=await(await page.request.get('/api/backend/v1/plans/'+plan.id,{headers})).json();expect(after.members).toEqual(before.members);expect(after.revision).toBe(before.revision);
 expect(bodies.join('\n')).not.toContain('hidden-contact@example.test');
});

test('natural-language generation creates a reviewed plan and proactively summarizes it',async({page})=>{
 const title='Reviewed proactive weekend '+crypto.randomUUID().slice(0,8);
 await login(page,'alice');await page.goto('/');
 await expect(page.getByRole('heading',{name:'Good company starts here.',exact:true})).toBeVisible();
 await page.getByLabel('Describe your plan').fill('Weekend trip for four friends near Austin under $350 per person');
 await page.getByRole('button',{name:'Start Planning',exact:true}).click();
 const review=page.getByRole('region',{name:'Review AI plan draft'});
 await expect(review).toBeVisible();
 await expect(review.getByLabel('Working start date')).toHaveValue('');
 await review.getByLabel('Generated plan name').fill(title);
 await review.getByLabel('Working start date').fill('2027-05-14');await review.getByLabel('Working end date').fill('2027-05-16');
 await review.getByRole('button',{name:'Create reviewed plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:title+'.',exact:true,level:1})).toBeVisible();
 await expect(page.getByRole('tab',{name:'Decisions',exact:true})).toHaveAttribute('aria-selected','true');
 await page.getByRole('tab',{name:'Chat',exact:true}).click();
 const coordination=page.getByRole('region',{name:'Plan coordination'});
 await expect(coordination.getByText('Waiting for votes',{exact:true})).toBeVisible();
 await expect(coordination).toContainText('The group is planning '+title+'.',{timeout:20000});
 await expect(page.getByText('Planning idea: Weekend trip for four friends near Austin under $350 per person',{exact:true})).toBeVisible();
 await page.goto('/');await expect(page.getByRole('heading',{name:'Your next steps',exact:true})).toBeVisible();
 await expect(page.locator('.decision-next-card').filter({hasText:title})).toBeVisible();
});

test('live discovery shows a clickable external source link and saves a dated venue',async({page})=>{
 test.setTimeout(90000);
 await login(page,'alice');
 await page.context().route('https://places.example.test/restaurant.jpg',async route=>route.fulfill({response:await page.request.get('/images/restaurant.jpg')}));
 await page.context().route('https://places.example.test/restaurant',route=>route.fulfill({contentType:'text/html',body:'<h1>Synthetic restaurant source</h1>'}));
 await page.goto('/discover');await page.getByLabel('Destination',{exact:true}).fill('San Francisco');await page.getByLabel('Looking for').fill('vegetarian dinner');
 await page.getByRole('button',{name:'Update',exact:true}).click();
 const link=page.getByRole('link',{name:'Explore Synthetic vegetarian restaurant',exact:true});
 await expect(page.locator('article.place-card')).toBeVisible();await page.locator('article.place-card').screenshot({path:'test-results-shared/place-card-'+test.info().project.name+'.png'});
 await expect(link).toHaveAttribute('href','https://places.example.test/restaurant');
 await expect(link).toHaveAttribute('rel','noopener noreferrer');
 const opened=page.waitForEvent('popup');await link.click();const source=await opened;
 await expect(source.getByRole('heading',{name:'Synthetic restaurant source'})).toBeVisible();await source.close();
 const token='Bearer test-alice';
 const created=await page.request.post('/api/backend/v1/plans',{headers:{Authorization:token},data:{title:'Discovery saved place '+crypto.randomUUID().slice(0,8),kind:'trip',start:'2027-05-14',end:'2027-05-16'}});
 expect(created.ok()).toBeTruthy();const plan=await created.json();
 await page.reload();await page.getByLabel('Destination',{exact:true}).fill('San Francisco');await page.getByLabel('Looking for').fill('vegetarian dinner');await page.getByRole('button',{name:'Update',exact:true}).click();
 await page.getByRole('button',{name:'Add Synthetic vegetarian restaurant to plan',exact:true}).click();
 await page.getByRole('combobox',{name:'Choose plan',exact:true}).selectOption(plan.id);await page.getByLabel('Activity date',{exact:true}).fill('2027-05-15');await page.getByLabel('Activity time',{exact:true}).fill('19:00');
 await page.getByRole('button',{name:'Save to draft itinerary',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.goto('/plans/'+plan.id+'?tab=Itinerary');await expect(page.getByRole('heading',{name:'Synthetic vegetarian restaurant',exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Venue website',exact:true})).toHaveAttribute('href','https://places.example.test/restaurant');
 await page.reload();await expect(page.getByText('2027-05-15 · Food & drink',{exact:true})).toBeVisible();
 const persisted=await(await page.request.get('/api/backend/v1/plans/'+plan.id,{headers:{Authorization:token}})).json();
 expect(persisted.itinerary[0]).toMatchObject({day:'2027-05-15',time:'19:00',source_url:'https://places.example.test/restaurant',image_source_url:'https://places.example.test/restaurant'});
});

test('owner can transfer a shared plan and the new owner can delete it after confirmation',async({page:alice,browser})=>{
 await login(alice,'alice');
 const context=await browser.newContext();const bob=await context.newPage();
 try{
 await login(bob,'bob');
 const title='Lifecycle review '+crypto.randomUUID().slice(0,8);
 const plan=await alice.evaluate(async title=>{const r=await fetch('/api/backend/v1/plans',{method:'POST',headers:{Authorization:'Bearer test-alice','Content-Type':'application/json'},body:JSON.stringify({title,kind:'outing',start:'2026-12-12',end:'2026-12-12'})});return r.json();},title);
 await alice.goto('/plans/'+plan.id);await alice.getByRole('button',{name:'Add member',exact:true}).click();await alice.getByLabel('Member email').fill('bob@example.test');await alice.getByRole('button',{name:'Add member',exact:true}).last().click();
  await bob.goto('/plans/'+plan.id);
  await expect(bob.getByRole('button',{name:'Delete plan',exact:true})).toHaveCount(0);
  await alice.getByRole('button',{name:'Transfer ownership',exact:true}).click();await alice.getByLabel('New plan owner').selectOption('bob');await alice.getByRole('button',{name:'Confirm transfer ownership',exact:true}).click();
  await expect(alice.getByRole('button',{name:'Delete plan',exact:true})).toHaveCount(0);
  await bob.reload();await bob.getByRole('button',{name:'Delete plan',exact:true}).click();
  await expect(bob.getByRole('button',{name:'Confirm delete plan',exact:true})).toBeDisabled();
  await bob.getByLabel('Plan name confirmation').fill(title);await bob.getByRole('button',{name:'Cancel',exact:true}).click();
  await expect(bob.getByRole('heading',{name:title+'.',exact:true})).toBeVisible();
  await bob.getByRole('button',{name:'Delete plan',exact:true}).click();await bob.getByLabel('Plan name confirmation').fill(title);await bob.getByRole('button',{name:'Confirm delete plan',exact:true}).click();
  await expect(bob).toHaveURL('/');await expect(bob.getByRole('link',{name:'Open '+title,exact:true})).toHaveCount(0);
  await alice.reload();await expect(alice.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
 }finally{await context.close();}
});

test('private link returns through sign-in and joins only after confirmation',async({page:alice,browser})=>{
 await login(alice,'alice');
 const plan=await alice.evaluate(async()=>{const r=await fetch('/api/backend/v1/plans',{method:'POST',headers:{Authorization:'Bearer test-alice','Content-Type':'application/json'},body:JSON.stringify({title:'Invitation-only weekend',kind:'trip',start:'2026-11-05',end:'2026-11-07',participants:''})});return r.json();});
 await alice.goto('/plans/'+plan.id);
 await alice.getByRole('button',{name:'Add member',exact:true}).click();
 await alice.getByRole('button',{name:'Create invitation link'}).click();
 const link=await alice.getByLabel('Private join link',{exact:true}).inputValue();
 expect(link).toContain('/join#');
 const context=await browser.newContext();const bob=await context.newPage();
 try{
  await bob.goto(link);
  await expect(bob.getByRole('link',{name:'Sign in or create account'})).toBeVisible();
  await expect(bob.getByText('Invitation-only weekend',{exact:true})).toHaveCount(0);
  await bob.getByRole('link',{name:'Sign in or create account'}).click();
  await login(bob,'bob');
  await expect(bob.getByRole('link',{name:'Continue to invitation'})).toBeVisible();
  await bob.getByRole('link',{name:'Continue to invitation'}).click();
  await expect(bob.getByRole('button',{name:'Join plan',exact:true})).toBeVisible();
  const before=await bob.evaluate(async()=>{const r=await fetch('/api/backend/v1/plans',{headers:{Authorization:'Bearer test-bob'}});return r.json();});
  expect(before.some((p:{id:string})=>p.id===plan.id)).toBe(false);
  await bob.getByLabel('Preferred display name').fill('Bobby');
  await bob.getByRole('button',{name:'Join plan',exact:true}).click();
  await expect(bob.getByRole('heading',{name:'Invitation-only weekend.'})).toBeVisible();
  expect(await bob.evaluate(()=>sessionStorage.getItem('tagalong-pending-invitation'))).toBeNull();
  await alice.getByRole('button',{name:'Disable invitation link'}).click();
  await bob.goto(link);
  await bob.getByLabel('Preferred display name').fill('Bobby');
  await bob.getByRole('button',{name:'Join plan',exact:true}).click();
  await expect(bob.getByRole('alert').filter({hasText:'unavailable or expired'})).toBeVisible();
 }finally{await context.close();}
});

test('two members share a plan, chat, vote, confirm an AI proposal and preserve it on refresh',async({page:alice,browser,isMobile})=>{
 const bobContext:BrowserContext=await browser.newContext({viewport:isMobile?{width:390,height:844}:{width:1280,height:720},isMobile});
 const bob=await bobContext.newPage();
 try{
  await login(alice,'alice');await login(bob,'bob');
  await alice.goto('/');
  await alice.getByRole('button',{name:'Create a plan',exact:true}).first().click();
  await expect(alice.getByRole('dialog')).toBeVisible(); if(await alice.getByRole('button',{name:'Create a plan manually',exact:true}).isVisible())await alice.getByRole('button',{name:'Create a plan manually',exact:true}).click();
  await alice.getByRole('button',{name:'Trip',exact:true}).click();
  await alice.getByLabel('Plan name').fill('Shared coast '+crypto.randomUUID().slice(0,8));
  await alice.getByLabel('Start date').fill('2026-12-04');await alice.getByLabel('End date').fill('2026-12-06');
  await alice.getByRole('button',{name:'Create shared plan'}).click();
  await expect(alice).toHaveURL(/\/plans\//);
  const url=alice.url();
  await bob.goto(url);await expect(bob.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
  await alice.getByRole('button',{name:'Add member',exact:true}).click();
  await alice.getByLabel('Member email').fill('bob@example.test');
  await alice.getByRole('dialog').getByRole('button',{name:'Add member'}).click();
  await expect(alice.getByRole('dialog')).not.toBeVisible();
  await bob.reload();await expect(bob.getByRole('heading',{name:/Shared coast/})).toBeVisible();
  await openTool(alice,'Documents');
  await alice.getByLabel('Document title').fill('Group food notes');
  await alice.getByLabel('Document text').fill('We prefer vegetarian meals for this trip.');
  await alice.getByRole('button',{name:'Save document'}).click();
  await expect(alice.getByText('Group food notes',{exact:true})).toBeVisible();
  await alice.getByRole('tab',{name:'Chat'}).click();
  await alice.getByRole('tab',{name:'Chat',exact:true}).click();await alice.getByLabel('Message your group').fill('@Tagalong remember our food preferences');
  await alice.getByRole('button',{name:'Send message'}).click();
  await expect(alice.locator('.message-bubble').filter({hasText:'Evidence considered'})).toBeVisible();
  await alice.getByText(/Sources \(/).click();
  await expect(alice.locator('blockquote').filter({hasText:'Group food notes'})).toBeVisible();
  await expect(alice.getByText('@Tagalong remember our food preferences',{exact:true})).toHaveCount(1);
  await openTool(alice,'Planning board');
  await expect(alice.getByRole('button',{name:'Confirm Vegetarian'})).toBeVisible();
  await alice.getByRole('button',{name:'Confirm Vegetarian'}).click();
  await expect(alice.getByText('Confirmed by you',{exact:true})).toBeVisible();
  await openTool(alice,'Polls');
  await alice.getByRole('button',{name:'Create poll',exact:true}).click();
  await alice.getByLabel('Poll question').fill('Dinner time?');await alice.getByLabel('Option 1').fill('6 pm');await alice.getByLabel('Option 2').fill('7 pm');
  await alice.getByRole('button',{name:'Publish poll',exact:true}).click();
  await bob.reload();await openTool(bob,'Polls');
  await bob.getByRole('button',{name:/6 pm/}).click();await expect(bob.getByRole('button',{name:/6 pm/})).toContainText('1 vote');
  await bob.getByRole('button',{name:/7 pm/}).click();await expect(bob.getByRole('button',{name:/7 pm/})).toContainText('1 vote');
  await expect(bob.getByRole('button',{name:/6 pm/})).toContainText('0 votes');
  await alice.reload();await openTool(alice,'Polls');await expect(alice.getByRole('button',{name:/7 pm/})).toContainText('1 vote');
  await alice.getByRole('button',{name:'Add member',exact:true}).click();
  await alice.getByRole('button',{name:'Remove member bob'}).click();
  await expect(alice.getByRole('button',{name:'Remove member bob'})).toHaveCount(0);
  await bob.reload();await expect(bob.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
 }finally{await bobContext.close();}
});

test('sign out ignores a delayed private response and keeps demo storage isolated',async({page})=>{
 await login(page,'alice');
 let release:()=>void=()=>{};let markStarted:()=>void=()=>{};
 const started=new Promise<void>(resolve=>{markStarted=resolve;});
 const wait=new Promise<void>(resolve=>{release=resolve;});
 await page.route('**/api/backend/v1/plans',async route=>{markStarted();await wait;await route.fulfill({json:[{id:'private',title:'Private delayed plan',kind:'trip',location:'Private',date:'',start:'',end:'',budget:0,image:'/images/coast.jpg',members:[],messages:[],preferences:[],polls:[],itinerary:[],tasks:[],revision:1,owner_id:'alice',role:'owner'}]});});
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));await started;
 await page.getByRole('button',{name:'Sign out',exact:true}).click();
 release();await expect(page.getByLabel('Email address')).toBeVisible();
 await page.getByRole('button',{name:'Explore the demo'}).click();await page.goto('/');
 await expect(page.getByRole('link',{name:'Open Private delayed plan'})).toHaveCount(0);
 expect(await page.evaluate(()=>localStorage.getItem('tagalong-demo-v1'))).not.toContain('Private delayed plan');
});

test('app admin reviews saved QA plans and audits private access while normal members are denied',async({page:alice,browser})=>{
 await login(alice,'alice','admin');await alice.goto('/admin');
 await expect(alice.getByRole('heading',{name:'Admin dashboard'})).toBeVisible();
 await alice.getByRole('button',{name:'Create QA review plans'}).click();
 await expect(alice.getByRole('heading',{name:'[QA Review] Chicago dinner',exact:true})).toBeVisible();
 await alice.getByRole('button',{name:'Create QA review plans'}).click();
 await expect(alice.getByRole('heading',{name:'[QA Review] Chicago dinner',exact:true})).toHaveCount(1);
 const review=alice.getByRole('button',{name:'Review private plan: [QA Review] Chicago dinner',exact:true});
 await expect(review).toBeDisabled();
 await alice.getByLabel('Reason for admin action').fill('Review synthetic dinner scenario');
 await review.click();
 await expect(alice.getByRole('region',{name:'Private plan review'})).toContainText('Budget: $65');
  await expect(alice.getByText('inspect_plan',{exact:true}).first()).toBeVisible();
 await alice.getByRole('button',{name:'Close private review'}).click();
 const context=await browser.newContext();const bob=await context.newPage();
 try{
  await login(bob,'bob');await bob.goto('/admin');
  await expect(bob.getByRole('heading',{name:'Admin access required'})).toBeVisible();
  await expect(bob.getByRole('link',{name:'Admin',exact:true})).toHaveCount(0);
  const status=await bob.evaluate(async()=>{const r=await fetch('/api/backend/v1/admin/overview',{headers:{Authorization:'Bearer test-bob'}});return r.status;});
  expect(status).toBe(403);
  await alice.reload();
  await alice.getByLabel('Reason for admin action').fill('QA suspension and restoration');
  await alice.getByRole('button',{name:'Suspend bob',exact:true}).click();
  await expect(alice.getByRole('button',{name:'Restore bob',exact:true})).toBeVisible();
  const denied=await bob.evaluate(async()=>{const r=await fetch('/api/backend/v1/me',{headers:{Authorization:'Bearer test-bob'}});return r.status;});
  expect(denied).toBe(403);
  await bob.evaluate(()=>window.dispatchEvent(new Event('focus')));
  await expect(bob.getByLabel('Email address')).toBeVisible();
  await expect(bob.getByRole('heading',{name:'Admin access required'})).toHaveCount(0);
  await alice.getByRole('button',{name:'Restore bob',exact:true}).click();
  await expect(alice.getByRole('button',{name:'Suspend bob',exact:true})).toBeVisible();
 }finally{await alice.evaluate(async()=>{await fetch('/api/backend/v1/admin/accounts/bob/suspension',{method:'POST',headers:{Authorization:'Bearer test-alice','X-Workspace-Mode':'admin','Content-Type':'application/json'},body:JSON.stringify({suspended:false,reason:'QA cleanup restore test member'})});});await context.close();}
});

test('admin can replay all demo stories then switch to member with no scenarios or dashboard access',async({page})=>{
 await login(page,'alice','admin');await page.goto('/admin');
 const titles=['Christmas weekend in San Francisco','Three days in Yosemite','A San Francisco date night'];
 for(const title of titles){
  await page.getByRole('button',{name:'Open story: '+title,exact:true}).click();
  const replay=page.getByRole('region',{name:'Demo story replay'});
  await expect(replay).toContainText('Fictional people and conversation');
  await expect(replay.getByRole('heading',{name:'Planning in progress'})).toBeVisible();
  await replay.getByRole('button',{name:'Show complete conversation'}).click();
  await expect(replay.getByRole('heading',{name:'Agreed planning outline'})).toBeVisible();
  await expect(replay).toContainText('No bookings have been made.');
  await replay.getByRole('button',{name:'Replay from start'}).click();
  await expect(replay).toContainText('Step 1 of');
 }
 const qa=await page.evaluate(async()=>{const response=await fetch('/api/backend/v1/admin/qa-plans',{method:'POST',headers:{Authorization:'Bearer test-alice','X-Workspace-Mode':'admin','Content-Type':'application/json'},body:'{}'});return response.json();});
 await page.goto('/account');await page.getByRole('button',{name:'Switch to Member',exact:true}).click();
 await expect(page.getByText('Current role: Member',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Admin',exact:true})).toHaveCount(0);
 await page.goto('/');await expect(page.getByRole('link',{name:/Open \[QA Review\]/})).toHaveCount(0);
 await page.goto('/plans/'+qa.plan_ids[0]);await expect(page.getByRole('heading',{name:'This plan wandered off.'})).toBeVisible();
 await page.goto('/admin');await expect(page.getByRole('heading',{name:'Admin access required'})).toBeVisible();
 const status=await page.evaluate(async()=>{const response=await fetch('/api/backend/v1/admin/demo-stories',{headers:{Authorization:'Bearer test-alice'}});return response.status;});
 expect(status).toBe(403);
});
