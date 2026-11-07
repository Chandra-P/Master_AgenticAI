import {test,expect} from '@playwright/test';

test('decision pages fit phone tablet and desktop viewports',async({page},info)=>{
 await page.addInitScript(()=>localStorage.setItem('tagalong-workspace-mode','demo'));
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:900});
  await page.goto('/');await expect(page.getByRole('heading',{name:'Good company starts here.',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Your next steps',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  await page.screenshot({path:info.outputPath(`home-${width}.png`)});
  await page.goto('/plans/coastal-weekend');await expect(page.getByRole('heading',{name:'Plan summary',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Destination',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  await page.screenshot({path:info.outputPath(`decisions-${width}.png`)});
 }
});
