import asyncio
from playwright.async_api import async_playwright
keys = ['solar', 'A', 'B', 'parets']
html = '<!doctype html><html><head><meta charset="utf-8"><style>@page{size:420mm 297mm;margin:0}body{margin:0}svg{display:block;width:420mm;height:297mm;page-break-after:always}</style></head><body>' + ''.join(open(f'/home/claude/plans/out2/{k}.svg').read() for k in keys) + '</body></html>'
open('/home/claude/plans/out2/plans.html', 'w').write(html)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox'])
        pg = await b.new_page(); await pg.goto('file:///home/claude/plans/out2/plans.html')
        await pg.pdf(path='/home/claude/plans/out2/Plànols – Anselm Clavé 30 – cases A i B (17-11-2026).pdf', width='420mm', height='297mm', print_background=True)
        await b.close()
asyncio.run(main())
