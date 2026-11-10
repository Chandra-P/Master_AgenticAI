import {test,expect,type Page} from '@playwright/test';

async function login(page:Page){
 await page.route('https://tagalong-test.supabase.co/auth/v1/**',route=>route.fulfill({json:{access_token:'test-alice',refresh_token:'refresh-alice',token_type:'bearer',expires_in:3600,user:{id:'alice',email:'alice@example.test',aud:'authenticated',role:'authenticated',app_metadata:{provider:'email'},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}}}));
 await page.goto('/account');await page.getByRole('radio',{name:'Member',exact:true}).check();
 await page.getByLabel('Email address').fill('alice@example.test');await page.getByLabel('Password',{exact:true}).fill('synthetic-password-123');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Signed in',exact:true})).toBeVisible();
}

test('a confirmed group choice is visible in Overview, Chat and Itinerary',async({page})=>{
 await login(page);
 const headers={Authorization:'Bearer test-alice'};
 const created=await page.request.post('/api/backend/v1/plans',{headers,data:{title:'Shared choice sync',kind:'trip',start:'2027-04-16',end:'2027-04-18'}});
 expect(created.ok()).toBeTruthy();const plan=await created.json();
 const decisionsResponse=await page.request.get(`/api/backend/v1/plans/${plan.id}/decisions`,{headers});
 expect(decisionsResponse.ok()).toBeTruthy();let snapshot=await decisionsResponse.json();
 let budget=snapshot.decisions.find((decision:{category:string})=>decision.category==='budget');
 const changed=await page.request.patch(`/api/backend/v1/plans/${plan.id}/decisions/${budget.id}`,{headers,data:{expected_revision:snapshot.plan_revision,expected_version:budget.version,options:['$500 per person']}});
 expect(changed.ok()).toBeTruthy();snapshot=await changed.json();budget=snapshot.decisions.find((decision:{category:string})=>decision.category==='budget');
 const optionId=budget.options[0].id;
 const response=await page.request.put(`/api/backend/v1/plans/${plan.id}/decisions/${budget.id}/response`,{headers,data:{expected_revision:snapshot.plan_revision,expected_version:budget.version,option_id:optionId,response:'support'}});
 expect(response.ok()).toBeTruthy();snapshot=await response.json();budget=snapshot.decisions.find((decision:{category:string})=>decision.category==='budget');
 const confirmed=await page.request.post(`/api/backend/v1/plans/${plan.id}/decisions/${budget.id}/confirm`,{headers,data:{expected_revision:snapshot.plan_revision,expected_version:budget.version,option_id:optionId}});
 expect(confirmed.ok()).toBeTruthy();

 await page.goto(`/plans/${plan.id}?tab=Overview`);
 const agreed=page.getByRole('region',{name:'Confirmed group choices'}).getByText('$500 per person');
 await expect(agreed).toBeVisible();
 await page.getByRole('tab',{name:'Chat'}).click();await expect(agreed).toBeVisible();
 await page.getByRole('tab',{name:'Itinerary'}).click();await expect(agreed).toBeVisible();
});
