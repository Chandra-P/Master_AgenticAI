import {test,expect,type Page} from '@playwright/test';

async function openGroups(page:Page){await page.goto('/groups');await expect(page.getByRole('button',{name:'Create a group',exact:true}).first()).toBeEnabled();}
async function savedGroups(page:Page){return page.evaluate(()=>JSON.parse(localStorage.getItem('tagalong-groups-v1')??'[]'));}
async function startEditor(page:Page){await page.getByRole('button',{name:'Create a group',exact:true}).first().click();return page.getByRole('dialog');}

test.beforeEach(async({page})=>{await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));});

// Each test uses a fresh browser context and synthetic adult details only.
test('create a custom group, retain optional details, and preserve existing plans',async({page})=>{
 await openGroups(page);
 await expect(page.getByRole('button',{name:/^View group /})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Share with members',exact:true})).toHaveCount(0);
 const before=await page.evaluate(()=>localStorage.getItem('tagalong-demo-v1'));
 const dialog=await startEditor(page);
 await dialog.getByRole('button',{name:'Custom',exact:true}).click();
 await dialog.getByLabel('Custom theme',{exact:true}).fill('Board game nights');
 await expect(dialog.getByLabel('Group name',{exact:true})).toHaveValue('Board game nights · Alex’s circle');
 await dialog.getByLabel('Group name',{exact:true}).fill('Thursday table crew');
 await dialog.getByRole('button',{name:'Add adult',exact:true}).click();
 await dialog.getByLabel('Preferred name / alias',{exact:true}).fill('River');
 await dialog.getByLabel('Email (optional)',{exact:true}).fill('river@example.test');
 await dialog.getByText('More details (optional)',{exact:true}).click();
 await dialog.getByLabel('First name',{exact:true}).fill('Demo');
 await dialog.getByLabel('Last name',{exact:true}).fill('Adult');
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Thursday table crew',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>localStorage.getItem('tagalong-demo-v1'))).toBe(before);
 await page.reload();
 const groups=await savedGroups(page);
 expect(groups.find((g:{name:string})=>g.name==='Thursday table crew').members[1]).toMatchObject({preferredName:'River',email:'river@example.test',firstName:'Demo',lastName:'Adult'});
 await expect(page.getByRole('heading',{name:'Thursday table crew',exact:true})).toBeVisible();
});

test('plan snapshots aliases only and survives group edits, archive and removal',async({page})=>{
 await openGroups(page);
 const card=page.getByRole('article',{name:'Sunday supper · Table talk',exact:true});
 await card.getByRole('button',{name:'Plan with this group',exact:true}).click();
 await page.getByLabel('Plan name',{exact:true}).fill('Supper snapshot');
 await page.getByRole('button',{name:'Create demo plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Supper snapshot.',exact:true})).toBeVisible();
 const plan=await page.evaluate(()=>JSON.parse(localStorage.getItem('tagalong-demo-v1')!).find((p:{title:string})=>p.title==='Supper snapshot'));
 expect(plan.members).toEqual([{name:'Alex',color:'#edc6b3'},{name:'Maya',color:'#c6d5c4'},{name:'Sam',color:'#c7c7e2'}]);
 expect(plan.group.name).toBe('Sunday supper · Table talk');
 await openGroups(page);
 await card.getByRole('button',{name:'Edit Sunday supper · Table talk',exact:true}).click();
 await page.getByLabel('Preferred name / alias',{exact:true}).first().fill('Maya alias');
 await page.getByRole('button',{name:'Save group',exact:true}).click();
 await card.getByRole('button',{name:'Archive Sunday supper · Table talk',exact:true}).click();
 await expect(card).toHaveCount(0);
 await page.getByRole('button',{name:/^Archived/}).click();
 await expect(card).toBeVisible();
 await card.getByRole('button',{name:'Restore Sunday supper · Table talk',exact:true}).click();
 await page.getByRole('button',{name:/^Active/}).click();
 await card.getByRole('button',{name:'Remove Sunday supper · Table talk',exact:true}).click();
 await page.getByRole('button',{name:'Keep group',exact:true}).click();
 await expect(card).toBeVisible();
 await card.getByRole('button',{name:'Remove Sunday supper · Table talk',exact:true}).click();
 await page.getByRole('button',{name:'Remove group',exact:true}).click();
 expect(await page.evaluate(()=>JSON.parse(localStorage.getItem('tagalong-demo-v1')!).find((p:{title:string})=>p.title==='Supper snapshot'))).toEqual(plan);
});

test('inline group creation preserves plan draft and does not copy contact data',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Create a plan',exact:true}).first().click();
 await page.getByLabel('Plan name',{exact:true}).fill('Keep my plan draft');
 await page.getByRole('button',{name:'Trip',exact:true}).click();
 await page.getByLabel('Start date',{exact:true}).fill('2026-12-10');
 await page.getByLabel('End date',{exact:true}).fill('2026-12-12');
 await page.getByRole('button',{name:'Create a new group',exact:true}).click();
 await page.getByRole('button',{name:'Cancel',exact:true}).click();
 await expect(page.getByLabel('Plan name',{exact:true})).toHaveValue('Keep my plan draft');
 await page.getByRole('button',{name:'Create a new group',exact:true}).click();
 await page.getByLabel('Group name',{exact:true}).fill('Our new circle');
 await page.getByRole('button',{name:'Add adult',exact:true}).click();
 await page.getByLabel('Preferred name / alias',{exact:true}).fill('River');
 await page.getByLabel('Email (optional)',{exact:true}).fill('river@example.test');
 await page.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(page.getByLabel('Plan name',{exact:true})).toHaveValue('Keep my plan draft');
 await expect(page.getByLabel('End date',{exact:true})).toHaveValue('2026-12-12');
 await expect(page.getByLabel('Plan with a group',{exact:true})).not.toHaveValue('');
 await page.getByRole('button',{name:'Create demo plan',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Keep my plan draft.',exact:true})).toBeVisible();
 const plan=await page.evaluate(()=>JSON.parse(localStorage.getItem('tagalong-demo-v1')!)[0]);
 expect(plan.members.map((m:{name:string})=>m.name)).toEqual(['Alex','River']);
 expect(JSON.stringify(plan)).not.toContain('river@example.test');
});

test('validation rejects duplicate names, aliases and emails and malformed emails',async({page})=>{
 await openGroups(page);
 const dialog=await startEditor(page);
 await dialog.getByLabel('Group name',{exact:true}).fill('  SUNDAY   supper · Table talk  ');
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(dialog.getByRole('alert')).toContainText('already in use');
 await dialog.getByLabel('Group name',{exact:true}).fill('Different crew');
 await dialog.getByRole('button',{name:'Add adult',exact:true}).click();
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(dialog.getByRole('alert')).toContainText('Each adult needs');
 await dialog.getByLabel('Preferred name / alias',{exact:true}).fill('alex');
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(dialog.getByRole('alert')).toContainText('different preferred name');
 await dialog.getByLabel('Preferred name / alias',{exact:true}).fill('River');
 await dialog.getByLabel('Email (optional)',{exact:true}).fill('invalid');
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(dialog.getByRole('alert')).toContainText('valid email');
 await dialog.getByLabel('Email (optional)',{exact:true}).fill('river@example.test');
 await dialog.getByRole('button',{name:'Add adult',exact:true}).click();
 await dialog.getByLabel('Preferred name / alias',{exact:true}).nth(1).fill('Sky');
 await dialog.getByLabel('Email (optional)',{exact:true}).nth(1).fill('RIVER@example.test');
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(dialog.getByRole('alert')).toContainText('email address can appear only once');
});

test('empty group list stays empty and corrupt data is not overwritten',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-groups-v1','[]'));
 await openGroups(page);
 await expect(page.getByRole('heading',{name:'Make room for your people.',exact:true})).toBeVisible();
 await page.reload();
 await expect(page.getByRole('heading',{name:'Make room for your people.',exact:true})).toBeVisible();
 await page.evaluate(()=>localStorage.setItem('tagalong-groups-v1','{bad json'));
 // Replace init script effects on the next load using a later script.
 await page.addInitScript(()=>localStorage.setItem('tagalong-groups-v1','{bad json'));
 await page.reload();
 await expect(page.getByRole('main').getByRole('alert')).toContainText('could not be loaded');
 const dialog=await startEditor(page);
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(page.getByRole('main').getByRole('alert')).toContainText('only in memory');
 expect(await page.evaluate(()=>localStorage.getItem('tagalong-groups-v1'))).toBe('{bad json');
});

test('group storage failures are visible and narrow navigation does not overflow',async({page})=>{
 await page.addInitScript(()=>{
  const original=Storage.prototype.setItem;
  Storage.prototype.setItem=function(key,value){if(key==='tagalong-groups-v1')throw new DOMException('Unavailable','QuotaExceededError');return original.call(this,key,value);};
 });
 await openGroups(page);
 const dialog=await startEditor(page);
 await dialog.getByRole('button',{name:'Create group',exact:true}).click();
 await expect(page.getByRole('main').getByRole('alert')).toContainText('only in memory');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
});

test('group editor matches navigation on small screens and supports keyboard dismissal',async({page},testInfo)=>{
 await openGroups(page);
 await page.screenshot({path:testInfo.outputPath('groups-page.png'),fullPage:true});
 const dialog=await startEditor(page);
 await expect(dialog.getByLabel('Group name',{exact:true})).toBeFocused();
 await dialog.getByRole('button',{name:'Add adult',exact:true}).click();
 await dialog.getByLabel('Preferred name / alias',{exact:true}).fill('River');
 await page.screenshot({path:testInfo.outputPath('group-editor.png'),fullPage:true});
 await page.keyboard.press('Escape');
 await expect(dialog).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Create a group',exact:true}).first()).toBeFocused();
 if(testInfo.project.name==='mobile'){
  await page.setViewportSize({width:320,height:700});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await expect(page.locator('.bottom-nav').getByRole('link',{name:'Groups',exact:true})).toBeVisible();
 }
});
