"""Run the production UI against the real ASGI API without opening network ports.
Requires Python Playwright and a Chromium installation. Network deployment is not tested.
"""
import asyncio
import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
import anyio
import httpx
from playwright.async_api import async_playwright
from finpilot.api import app, connection
from finpilot.db import connect, migrate, seed


async def main():
    conn=connect(':memory:')
    migrate(conn)
    seed(conn)
    async def db():
        yield conn
    async def inline(fn,*args,**kwargs):
        return fn(*args)
    original=anyio.to_thread.run_sync
    anyio.to_thread.run_sync=inline
    app.dependency_overrides[connection]=db
    checks=[]
    errors=[]
    build=ROOT/'frontend/.next'
    if not (build/'server/app/index.html').exists():
        raise RuntimeError('Run npm run build in frontend first')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://asgi') as client:
        async with async_playwright() as p:
            browser=await p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            page=await browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
            page.on('pageerror',lambda err:errors.append(str(err)))
            async def handle(route):
                request=route.request
                url=urlparse(request.url)
                path=unquote(url.path)
                if url.hostname!='finpilot.test':
                    await route.abort()
                elif path.startswith('/api/'):
                    response=await client.request(request.method,path+('?' + url.query if url.query else ''),content=request.post_data_buffer,headers={k:v for k,v in request.headers.items() if k.lower() not in ['host','content-length']})
                    await route.fulfill(status=response.status_code,body=response.content,headers={'content-type':response.headers.get('content-type','application/json')})
                elif path.startswith('/_next/static/'):
                    file=(build/'static'/path.removeprefix('/_next/static/')).resolve()
                    if not file.is_relative_to(build.resolve()) or not file.is_file():
                        await route.fulfill(status=404,body='Not found')
                    else:
                        await route.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(file)[0] or 'application/octet-stream')
                elif path=='/':
                    await route.fulfill(body=(build/'server/app/index.html').read_bytes(),content_type='text/html')
                else:
                    await route.fulfill(status=404,body='Not found')
            await page.route('**/*',handle)
            await page.goto('http://finpilot.test/')
            await page.get_by_role('heading',name='Your money, in focus.').wait_for()
            await page.get_by_text('$60,000',exact=True).wait_for()
            checks.append('demo entry and dashboard')
            await page.screenshot(path=str(ROOT/'artifacts/overview-desktop.png'),full_page=True)
            nav=page.get_by_role('navigation',name='Main navigation')
            await nav.get_by_role('button',name='Transactions',exact=True).click()
            await page.get_by_role('searchbox').count()  # Inputs use explicit accessible names.
            await page.get_by_role('textbox',name='Search merchants').fill('Costco')
            await page.locator('tbody tr').first.wait_for()
            checks.append('searchable transaction ledger')
            await nav.get_by_role('button',name='FinPilot Copilot',exact=True).click()
            await page.get_by_role('button',name='How much did I spend last month?',exact=True).click()
            await page.get_by_text('$6,000.00',exact=True).wait_for()
            checks.append('SQL Copilot question')
            await page.get_by_role('textbox',name='Ask FinPilot').fill('What APR is listed in my current auto-loan offer?')
            await page.get_by_role('button',name='Send question').click()
            await page.get_by_text('6.49%',exact=True).wait_for()
            checks.append('document Copilot question')
            await page.get_by_role('textbox',name='Ask FinPilot').fill('Can I afford the $50,000 car in my current loan offer?')
            await page.get_by_role('button',name='Send question').click()
            await page.get_by_role('heading',name='Higher down payment',exact=True).wait_for()
            await page.get_by_role('heading',name='Lower down payment',exact=True).wait_for()
            await page.get_by_role('heading',name='Postpone purchase',exact=True).wait_for()
            last=page.locator('.answer-card').last
            await last.get_by_text('Evidence & sources',exact=False).click()
            await last.get_by_text('Agent & tool trace',exact=False).click()
            await last.get_by_text('simulate_scenario',exact=True).wait_for()
            checks.append('car affordability, three scenarios, evidence and tool trace')
            await page.screenshot(path=str(ROOT/'artifacts/copilot-desktop.png'),full_page=True)
            await nav.get_by_role('button',name='Scenarios',exact=True).click()
            await page.get_by_role('button',name='Run deterministic simulation',exact=False).click()
            await page.get_by_text('$3,400.00',exact=True).wait_for()
            checks.append('scenario execution')
            await nav.get_by_role('button',name='Documents',exact=True).click()
            await page.get_by_label('Upload financial document').set_input_files({'name':'demo-note.txt','mimeType':'text/plain','buffer':b'SYNTHETIC note\nMonthly allowance: $200.'})
            await page.get_by_role('heading',name='demo-note.txt',exact=True).wait_for()
            checks.append('document upload and ingestion')
            await page.get_by_role('button',name='Security test document',exact=False).click()
            dialog=page.get_by_role('dialog')
            await dialog.wait_for()
            text=await dialog.inner_text()
            assert 'Credit limit: $2,000' in text
            assert 'Ignore previous' not in text
            await dialog.get_by_role('button',name='Close',exact=True).click()
            checks.append('injection quarantine preserves legitimate evidence')
            await nav.get_by_role('button',name='Evaluation Lab',exact=True).click()
            await page.get_by_role('button',name='Run evaluation suite',exact=False).click()
            await page.get_by_text('100%',exact=True).first.wait_for(timeout=20000)
            assert await page.locator('.evaluation-case').count()==59
            checks.append('actual 59-case evaluation from UI')
            await page.screenshot(path=str(ROOT/'artifacts/evaluation-desktop.png'),full_page=True)
            await nav.get_by_role('button',name='Settings',exact=True).click()
            await page.get_by_label('Emergency-fund minimum ($)',exact=True).fill('27000')
            save=page.get_by_role('button',name='Confirm & save constraints',exact=True)
            assert await save.is_disabled()
            await page.get_by_role('checkbox').check()
            await save.click()
            await page.get_by_text('Constraints updated and recorded in the audit log.',exact=True).wait_for()
            checks.append('explicit confirmed memory edit')
            await nav.get_by_role('button',name='Overview',exact=True).click()
            await page.get_by_role('button',name='Switch to dark theme').click()
            await page.screenshot(path=str(ROOT/'artifacts/overview-dark.png'),full_page=True)
            await page.get_by_role('button',name='Switch to light theme').click()
            await page.set_viewport_size({'width':390,'height':844})
            await page.get_by_role('button',name='Open navigation').click()
            await nav.get_by_role('button',name='Goals',exact=True).click()
            await page.get_by_role('heading',name='Give every decision a direction.').wait_for()
            assert await page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile horizontal overflow'
            await page.screenshot(path=str(ROOT/'artifacts/goals-mobile.png'),full_page=True)
            checks.append('theme switching and mobile navigation without overflow')
            assert not errors, errors
            await browser.close()
    anyio.to_thread.run_sync=original
    app.dependency_overrides.clear()
    conn.close()
    report={'passed':len(checks),'checks':checks,'browser_errors':errors,'mode':'production Next build + in-memory ASGI API; no live socket deployment'}
    (ROOT/'artifacts/browser-smoke.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    asyncio.run(main())
