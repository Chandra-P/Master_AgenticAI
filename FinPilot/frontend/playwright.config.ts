import { defineConfig } from '@playwright/test';
const python=process.platform==='win32'?'..\\.venv\\Scripts\\python.exe':'../.venv/bin/python';
export default defineConfig({
 testDir:'./tests/e2e',timeout:45000,workers:1,
 use:{baseURL:'http://127.0.0.1:3100',trace:'retain-on-failure',launchOptions:process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}},
 webServer:[
  {command:`${python} ../scripts/start_e2e_api.py`,url:'http://127.0.0.1:8100/api/health',timeout:20000,reuseExistingServer:false},
  {command:'npm run start -- --port 3100',url:'http://127.0.0.1:3100',timeout:20000,reuseExistingServer:false,env:{API_URL:'http://127.0.0.1:8100',FINPILOT_ACCESS_TOKEN:'finpilot-local-e2e-service-token'}},
 ],
});
