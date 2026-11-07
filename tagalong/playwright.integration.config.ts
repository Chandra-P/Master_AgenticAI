import {defineConfig,devices} from '@playwright/test';
import {resolve} from 'node:path';
const python=process.env.TAGALONG_TEST_PYTHON||resolve('backend',process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
export default defineConfig({testDir:'./tests',testMatch:'**/shared*.spec.ts',outputDir:'test-results-shared',timeout:45000,workers:1,use:{baseURL:'http://127.0.0.1:3200',trace:'retain-on-failure',screenshot:'only-on-failure'},webServer:[
 {command:'"'+python+'" -m uvicorn tests.http_fixture:app_factory --factory --host 127.0.0.1 --port 8100',cwd:'./backend',url:'http://127.0.0.1:8100/health',reuseExistingServer:false},
 {command:'node .next/standalone/server.js',url:'http://127.0.0.1:3200',reuseExistingServer:false,env:{PORT:'3200',HOSTNAME:'127.0.0.1',FASTAPI_BASE_URL:'http://127.0.0.1:8100',NEXT_PUBLIC_SUPABASE_URL:'https://tagalong-test.supabase.co',NEXT_PUBLIC_SUPABASE_ANON_KEY:'test-publishable-key',TAGALONG_REQUIRE_CONNECTED:'true'}},
],projects:[{name:'desktop',use:{...devices['Desktop Chrome']}},{name:'mobile',use:{...devices['iPhone 13'],defaultBrowserType:'chromium'}}]});
