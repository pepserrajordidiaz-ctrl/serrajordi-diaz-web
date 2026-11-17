import sys
sys.path.insert(0, '/home/claude/plans')
import plans2
SH = [('solar', 'Solar i mides', plans2.site_sheet()), ('A', 'Casa A', plans2.house_sheet('A')), ('B', 'Casa B', plans2.house_sheet('B'))]
NOTES = {
 'solar': "Mides preses al solar el 17/11/2026. El veí del darrere ocupa una cantonada de 3,00 × 2,70 m al costat de la casa A. La línia grisa discontínua és el límit del Cadastre.",
 'A': "Casa del costat del núm. 28. Com que el veí ocupa part del pati, el safareig i la terrassa són més petits, i a la planta primera la cuina passa a la cantonada del darrere, amb una porta a la seva dreta per sortir a la terrassa. L'estar va al davant. En groc, els canvis.",
 'B': "La mateixa distribució que la casa A en espill, sense canvis, ajustada al límit real de la parcel·la: el graó del costat és a 5,90 m de la façana.",
}
def web(k, svg):
    for i in ('eat', 'deck', 'arr'):
        svg = svg.replace(f'id="{i}"', f'id="{i}-{k}"').replace(f'url(#{i})', f'url(#{i}-{k})')
    if k == 'solar': svg = svg.replace('viewBox="0 0 420 297"', 'viewBox="18 22 272 272"', 1)
    return svg.replace('<svg ', f'<svg class="pl{" on" if k == "solar" else ""}" data-k="{k}" ', 1)
tabs = ''.join(f'<button class="chip" data-k="{k}" aria-pressed="{"true" if k == "solar" else "false"}">{t}</button>' for k, t, _ in SH)
side = ''.join(f'<div class="pside{" on" if k == "solar" else ""}" data-k="{k}"><p>{NOTES[k]}</p></div>' for k, *_ in SH)
html = f'''
<section class="block" id="planols">
 <div class="wrap grid">
  <p class="eyebrow"><span>06 · Plànols</span><span>Actualitzats el 17/11/2026</span></p>
  <h2>Com seran les cases, planta per planta</h2>
  <p class="lede">La casa A és la del costat del núm. 28; la casa B, la de l'altre costat. Quatre plantes: garatge, dia, nit i àtic amb suite.<span class="s">Esquema orientatiu, pendent del projecte de l'arquitecte</span></p>
  <div class="tabs ptabs" role="group" aria-label="Plànols">{tabs}</div>
  <aside class="planside">{side}<a class="dl-pdf" href="planols.pdf" download>Descarrega els plànols (PDF, A3)</a></aside>
  <figure class="planfig">{"".join(web(k, s) for k, _, s in SH)}</figure>
 </div>
</section>
'''
open('/home/claude/web/src/b3_plans.html', 'w').write(html)
for k, _, s in SH: open(f'/home/claude/plans/out2/{k}.svg', 'w').write(s)
print(len(html))
