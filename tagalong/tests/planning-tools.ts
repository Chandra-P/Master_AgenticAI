import type {Page} from '@playwright/test';
export async function openTool(page:Page,name:string){
 if(name==='Planning board'){await page.getByRole('tab',{name:'Overview',exact:true}).click();return;}
 const tools=page.locator('details.journey-tools');
 if(!(await tools.getAttribute('open'))&&!(await tools.evaluate(element=>element.hasAttribute('open'))))await tools.getByText('More planning tools',{exact:true}).click();
 await tools.getByRole('button',{name,exact:true}).click();
}
