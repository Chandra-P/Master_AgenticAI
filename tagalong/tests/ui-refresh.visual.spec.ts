import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';

// Synthetic demo only; screenshots never contain a real account or plan.
test('home, chat and itinerary visual comparison',async({page},info)=>{
 test.skip(info.project.name!=='desktop');
 test.setTimeout(90000);
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 await page.route('**/api/config',route=>route.fulfill({json:{supabaseUrl:'',supabaseAnonKey:'',connectedReady:false}}));
 const phase=process.env.TAGALONG_VISUAL_PHASE||'after';
 const folder=resolve('docs/ui-refresh',phase);await mkdir(folder,{recursive:true});
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});
  for(const [screen,path] of [['home','/'],['chat','/plans/coastal-weekend?tab=Chat'],['itinerary','/plans/coastal-weekend?tab=Itinerary']]){
   await page.goto(path);await expect(page.locator('.app-shell')).toBeVisible();
   if(screen!=='home')await expect(page.getByRole('tab',{name:screen==='chat'?'Chat':'Itinerary',exact:true})).toHaveAttribute('aria-selected','true');
   await page.evaluate(()=>Promise.all([...document.images].map(image=>{image.loading='eager';return image.decode().catch(()=>{});})));
   await page.screenshot({path:resolve(folder,`${screen}-${width}.png`),fullPage:true,scale:'css'});
  }
 }
});
