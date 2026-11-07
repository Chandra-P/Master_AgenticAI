import {test,expect} from '@playwright/test';

test('a lodging decision has a complete manual option path with retained details',async({page})=>{
 await page.goto('/');await page.getByRole('link',{name:'Open Coastal weekend'}).click();
 const lodging=page.getByRole('article').filter({has:page.getByRole('heading',{name:'Lodging',exact:true})}).first();
 await lodging.getByRole('button',{name:'Add option',exact:true}).click();
 const dialog=page.getByRole('dialog');
 await dialog.getByLabel('Option name',{exact:true}).fill('Harbor Lodge');
 await dialog.getByLabel('Website link',{exact:true}).fill('https://example.com/harbor-lodge');
 await dialog.getByLabel('Estimated cost per person',{exact:true}).fill('120');
 await dialog.getByLabel('Option notes',{exact:true}).fill('Two rooms; ask about step-free access.');
 await dialog.getByRole('button',{name:'Add to decision',exact:true}).click();
 await expect(lodging.getByRole('link',{name:'Visit Harbor Lodge',exact:true})).toHaveAttribute('href','https://example.com/harbor-lodge');
 await expect(lodging.getByText('Two rooms; ask about step-free access.',{exact:true})).toBeVisible();
 await page.reload();await expect(lodging.getByRole('link',{name:'Visit Harbor Lodge',exact:true})).toBeVisible();
 await expect(lodging.getByText(/120.*estimate/)).toBeVisible();
});
