# Lámina 4: before / after of the zones changed on 18/11/2026
import re, sys
sys.path.insert(0, '/home/claude/plans')
import plans2
INK, MUTE = plans2.INK, plans2.MUTE
T = plans2.text_xy
def inner(svg, pre):
    body = svg[svg.index('>', svg.index('<svg')) + 1: svg.rindex('</svg>')]
    return body.replace('id="', f'id="{pre}').replace('url(#', f'url(#{pre}')
def sheet():
    after = {k: plans2.house_sheet(k) for k in 'AB'}
    before = {k: open(f'/home/claude/plans/before/casa{k}.svg').read() for k in 'AB'}
    # crops of one floor (sheet mm): floor i spans x 15+101i … +85; the house body sits between y≈100 and y≈243
    def crop(svg, pre, i, x, y, w, y0=98, y1=244):
        h = w*(y1 - y0)/85
        return f'<svg x="{x}" y="{y}" width="{w}" height="{h:.1f}" viewBox="{15+101*i} {y0} 85 {y1-y0}" overflow="hidden">{inner(svg, pre)}</svg>', h
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" font-family="Archivo, Helvetica, Arial, sans-serif" role="img" aria-label="Comparativa abans i després">', '<rect width="420" height="297" fill="#fff"/>']
    o.append(T(12, 20, 'COMPARATIVA · Abans i després de la revisió del 18/11/2026', size=5.2, weight=700, anchor='start'))
    o.append(T(12, 27, "Zones modificades. A l'esquerra de cada parella, el plànol anterior; a la dreta, el corregit. Mateixa escala (1:75 en DIN A3 a les làmines 2 i 3).", size=2.7, fill=MUTE, anchor='start'))
    panels = [('Casa B · P1 · cuina en L', 'B', 1), ('Casa B · P2 · despatx i estar', 'B', 2), ('Casa A · àtic · bany i armari', 'A', 3), ('Casa B · àtic · bany i armari', 'B', 3)]
    W, gap, x0 = 58, 4, 12
    for n, (title, k, i) in enumerate(panels):
        col, row = n % 2, n // 2
        x = x0 + col*(2*W + gap + 14); y = 40 + row*128
        o.append(T(x, y, title, size=3.0, weight=700, anchor='start'))
        for j, (svg, pre, tag, c) in enumerate(((before[k], f'b{k}{n}', 'ABANS', MUTE), (after[k], f'a{k}{n}', 'DESPRÉS', '#2F6B3A'))):
            xx = x + j*(W + gap)
            s, hh = crop(svg, pre, i, xx, y + 6, W)
            o.append(T(xx, y + 4.5, tag, size=2.2, weight=700, fill=c, anchor='start'))
            o.append(s); o.append(f'<rect x="{xx}" y="{y+6}" width="{W}" height="{hh:.1f}" fill="none" stroke="#D5D8D4" stroke-width="0.3"/>')
    # list of changes
    tx = 290; ty = 40
    o.append(T(tx, ty, 'CANVIS PRINCIPALS', size=3.2, weight=700, anchor='start'))
    items = [
        ('Les dues cases', ["Escales al mateix lloc a totes les plantes (1,00 m de pas):", "sense el text «PUJA» ni el requadre «arriba»; es manté la", "fletxa. Compensats dibuixats des del vèrtex interior.", "Porta del porxo: obre cap a l'exterior (el porxo), 0,85 m,", "dins del porxo de 1,25 × 1,13: no envaeix la vorera.", "P2: dues finestres a cada habitació, a la façana del darrere.", "Façanes i mitgeres amb traç gruixut; envans més fins."]),
        ('Àtics', ["Paret del bany alineada amb el davant de la dutxa i", "allargada cap a dins; a la cara de la suite, armari encastat", "de 0,60 m amb portes correderes de cara al llit.", "Llit amb el capçal a la paret lateral; pas lliure al costat", "de l'escala de la porta de la suite fins a la terrassa.", "Casa B: la paret del bany va a la línia del graó (5,90 m),", "la dutxa ocupa el racó del graó i l'armari s'allarga. El", "vestidor passa a la mitgera i el bany té porta corredera."]),
        ('Casa B', ["P1: cuina en L contínua amb mòdul de racó, rentaplats,", "forn i placa al tram de la mitgera i nevera al final.", "P2: el dormitori 2 passa a DESPATX (escriptori llarg sota", "les dues finestres, prestatges, armari a la paret lateral).", "L'estudi obert del davant passa a ESTAR FAMILIAR."]),
        ('Pendent de validar', ["Casa A, P2: les finestres del dormitori 2 donen sobre", "la cantonada ocupada pel veí (llums i vistes).", "Àtics: per l'espai (2,2 m lliures davant l'armari), el llit", "queda arrimat a la façana de la terrassa: accés per un", "costat. Alternativa: llit de 1,35 i armari de 0,55."]),
    ]
    y = ty + 8
    for head, lines in items:
        o.append(T(tx, y, head, size=2.7, weight=700, anchor='start')); y += 4.6
        for ln in lines: o.append(T(tx, y, ln, size=2.3, anchor='start')); y += 3.6
        y += 3.5
    o.append(T(12, 290, 'Avantprojecte orientatiu, pendent de validació tècnica, estructural i urbanística per l\'arquitecte responsable · Serrajordi-Diaz Investments', size=2.4, fill=MUTE, anchor='start'))
    o.append('</svg>'); return '\n'.join(o)
if __name__ == '__main__':
    open('/home/claude/plans/out2/canvis.svg', 'w').write(sheet())
