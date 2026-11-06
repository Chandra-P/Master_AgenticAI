import {test,expect} from '@playwright/test';
import {suggestContinuation} from '../src/services/typing-suggestions';
import {initialPlans} from '../src/services/demo-data';

test('engine completes later words using common and current-plan context only',()=>{
 const plan=initialPlans()[0];
 expect(suggestContinuation('I think we should ',plan)).toBe('meet ');
 expect(suggestContinuation('I think we should me',plan)).toBe('et ');
 expect(suggestContinuation('Our dinner at ',plan)).toBe('Seabrook, ');
 plan.messages=[{id:'test',author:'Maya',text:'We could bring binoculars tomorrow.',time:'Now'}];
 expect(suggestContinuation('Maybe we could bring ',plan)).toBe('binoculars ');
 expect(suggestContinuation('Maybe we could bring ',initialPlans()[1])).toBe('');
 expect(suggestContinuation('Unrecognized aardvark ',plan)).toBe('');
 expect(suggestContinuation('Let',plan)).toBe("'s plan ");
});

test('engine bounds history, completion size and multiline drafts',()=>{
 const plan=initialPlans()[0];
 plan.messages=[{id:'old',author:'Maya',text:'Special old sentinel.',time:'Now'}, {id:'huge',author:'Maya',text:'x'.repeat(12000),time:'Now'}];
 expect(suggestContinuation('Special old ',plan)).toBe('');
 expect(suggestContinuation('I think\nwe should ',plan)).toBe('');
 expect(suggestContinuation('x'.repeat(2000),plan)).toBe('');
});

test('engine supports mentions, ordinary planning drafts and partial first words',()=>{
 const plan=initialPlans()[0];
 expect(suggestContinuation('@Tagalong I want to ',plan)).toBe('plan ');
 expect(suggestContinuation('@tagalong lets fl',plan)).toBe('y ');
 expect(suggestContinuation('restau',plan)).toBe('rants ');
 expect(suggestContinuation('Can we find restau',plan)).toBe('rants ');
 expect(suggestContinuation('@Tagalong Let',plan)).toBe("'s plan ");
 expect(suggestContinuation('aardvark ',plan)).toBe('');
 expect(suggestContinuation('xy',plan)).toBe('');
 expect(suggestContinuation('I want to '+ 'x'.repeat(1989),plan)).toBe('');
});

test.describe('chat typing suggestions',()=>{

test.beforeEach(async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.goto('/');
 await page.getByRole('link',{name:'Open Coastal weekend'}).click();
 await expect(page.getByLabel('Message your group')).toBeVisible();
});

test('local suggestions accept without sending, dismiss, and turn off',async({page})=>{
 const draft=page.getByLabel('Message your group');
 await page.waitForLoadState('networkidle');
 const requests:string[]=[];
 page.on('request',request=>requests.push(request.url()));
 const count=await page.locator('.chat-message').count();
 await draft.fill('Let');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toBeVisible();
 await draft.press('Tab');
 await expect(draft).toHaveValue("Let's plan ");
 await expect(page.locator('.chat-message')).toHaveCount(count);
 await draft.fill('Let');
 await draft.press('Escape');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toHaveCount(0);
 await draft.fill('Lets');
 await draft.fill('Let');
 await page.getByRole('button',{name:/Accept suggestion/}).click();
 await expect(draft).toHaveValue("Let's plan ");
 await draft.fill('@Tagalong lets fl');
 await page.getByRole('button',{name:'Accept suggestion: y',exact:true}).click();
 await expect(draft).toHaveValue('@Tagalong lets fly ');
 await expect(page.locator('.chat-message')).toHaveCount(count);
 await page.getByLabel('Typing suggestions').uncheck();
 await draft.fill('Let');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toHaveCount(0);
 await draft.press('Tab');
 await expect(draft).not.toBeFocused();
 expect(requests).toEqual([]);
});

test('preserves Tab in mid-draft and does not send while composing',async({page})=>{
 const draft=page.getByLabel('Message your group');
 const count=await page.locator('.chat-message').count();
 await draft.fill('Let');
 await draft.evaluate((element:HTMLTextAreaElement)=>element.setSelectionRange(0,0));
 await draft.press('Tab');
 await expect(draft).toHaveValue('Let');
 await draft.focus();
 await draft.dispatchEvent('compositionstart');
 // Synthetic composition does not put the browser's editor into native IME
 // mode. Dispatch the composing key without inserting a physical newline.
 await draft.dispatchEvent('keydown',{key:'Enter',code:'Enter',isComposing:true});
 await expect(draft).toHaveValue('Let');
 await expect(page.locator('.chat-message')).toHaveCount(count);
 await draft.dispatchEvent('compositionend');
 await draft.press('Enter');
 await expect(page.locator('.chat-message')).toHaveCount(count+1);
 await expect(draft).toHaveValue('');
});

test('uses plan context and clears the draft when moving to another plan',async({page})=>{
 const draft=page.getByLabel('Message your group');
 await draft.fill("Let's explore ");
 await expect(page.getByRole('button',{name:'Accept suggestion: Seabrook, California.'})).toBeVisible();
 await draft.fill('Thanks Ma');
 await page.getByRole('button',{name:'Accept suggestion: ya!'}).click();
 await expect(draft).toHaveValue('Thanks Maya!');
 await page.getByRole('link',{name:'All plans',exact:true}).click();
 await page.getByRole('link',{name:'Open Sunday supper club'}).click();
 await expect(draft).toHaveValue('');
 await expect(page.getByRole('button',{name:/Accept suggestion/})).toHaveCount(0);
 await draft.fill("Let's explore ");
 await expect(page.getByRole('button',{name:'Accept suggestion: Brookside, California.'})).toBeVisible();
});
});
