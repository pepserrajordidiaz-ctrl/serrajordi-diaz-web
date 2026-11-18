import asyncio
from playwright.async_api import async_playwright
keys = ['solar', 'A', 'B', 'conjunt', 'paretsA', 'paretsB', 'conjuntT']
BIG = {'conjunt', 'conjuntT'}     # DIN A2 sheets
def page(k):
    svg = open(f'/home/claude/plans/out2/{k}.svg').read()
    return f'<div class="{"a2" if k in BIG else "a3"}">{svg}</div>'
html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:420mm 297mm;margin:0}@page a2{size:594mm 420mm;margin:0}body{margin:0}'
        '.a3{width:420mm;height:297mm;break-after:page}.a2{page:a2;width:594mm;height:420mm;break-after:page}.a3 svg,.a2 svg{display:block;width:100%;height:100%}</style></head><body>'
        + ''.join(page(k) for k in keys) + '</body></html>')
open('/home/claude/plans/out2/plans.html', 'w').write(html)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox'])
        pg = await b.new_page(); await pg.goto('file:///home/claude/plans/out2/plans.html')
        await pg.pdf(path='/home/claude/plans/out2/Plànols – Anselm Clavé 30 – cases A i B (17-11-2026).pdf', prefer_css_page_size=True, print_background=True)
        await b.close()
asyncio.run(main())
