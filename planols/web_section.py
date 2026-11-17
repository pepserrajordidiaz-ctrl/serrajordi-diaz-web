import re, sys
sys.path.insert(0, '/home/claude/plans')
from plans import SHEETS, sheet
NOTES = {
 'situacio': ('Solar i mides', "Mides preses al solar. El veí del darrere ocupa una cantonada de 3,00 × 2,70 m al costat de la casa 1. La línia grisa discontínua és el límit del Cadastre.", ['Façana: 9,20 m', 'Casa 1: fondària 9,70 m', 'Casa 2: fondària 10,00 m', 'Superfície útil: ≈111 m²']),
 'pb': ('Planta baixa', "Garatge per a dos cotxes en filera i l'escala al costat de la paret mitgera.", ['Casa 1: safareig petit, ≈4 m² (nou)', 'Casa 2: sala polivalent o safareig, ≈10 m²']),
 'p1': ('Planta primera', "A la casa 1 la cuina passa a la cantonada del darrere, amb una porta a la seva dreta per sortir a la terrassa, i la sala d'estar va al davant. La casa 2 no canvia.", ["Casa 1: sala d'estar al davant (nou)", 'Casa 1: cuina al darrere i terrassa de ≈5 m² (nou)', "Casa 2: cuina al davant, sala d'estar al darrere i terrassa de ≈13 m²", 'Lavabo a totes dues']),
 'p2': ('Planta segona', 'Igual a totes dues cases.', ['Dues habitacions dobles', 'Bany compartit', 'Estudi obert']),
 'at': ('Altell', 'Igual a totes dues cases.', ['Suite amb bany', 'Terrassa al davant i al darrere']),
}
def web_svg(k, t, s, fn):
    svg = sheet(k, t, s, fn)
    for i in ('eat', 'deck', 'arr'): svg = svg.replace(f'id="{i}"', f'id="{i}-{k}"').replace(f'url(#{i})', f'url(#{i}-{k})')
    svg = svg.replace('viewBox="0 0 420 297"', 'viewBox="18 22 272 272"', 1)
    svg = svg.replace('<svg ', f'<svg class="pl{" on" if k == "situacio" else ""}" data-k="{k}" ', 1)
    return svg
tabs = ''.join(f'<button class="chip" data-k="{k}" aria-pressed="{"true" if k == "situacio" else "false"}">{NOTES[k][0]}</button>' for k, *_ in SHEETS)
side = ''.join(f'<div class="pside{" on" if k == "situacio" else ""}" data-k="{k}"><h3>{NOTES[k][0]}</h3><p>{NOTES[k][1]}</p><ul>' + ''.join(f'<li>{x}</li>' for x in NOTES[k][2]) + '</ul></div>' for k, *_ in SHEETS)
html = f'''
<section class="block" id="planols">
 <div class="wrap grid">
  <p class="eyebrow"><span>06 · Plànols</span><span>Actualitzats el 17/11/2026</span></p>
  <h2>Com seran les cases, planta per planta</h2>
  <p class="lede">La casa 1 és la del costat del núm. 28; la casa 2, la del costat del núm. 32. En groc, el que ha canviat a la casa 1 després de mesurar el solar.<span class="s">Esquema orientatiu, pendent del projecte de l'arquitecte</span></p>
  <div class="tabs ptabs" role="group" aria-label="Plantes">{tabs}</div>
  <figure class="planfig">{"".join(web_svg(*x) for x in SHEETS)}</figure>
  <aside class="planside">{side}<a class="dl-pdf" href="planols.pdf" download>Descarrega els plànols (PDF, A3)</a></aside>
 </div>
</section>
'''
open('/home/claude/web/src/b3_plans.html', 'w').write(html)
print(len(html))
