"""Extrae las secciones HSS (cuadradas y rectangulares) del catalogo ATC y genera datos/hss_atc_catalogo.json.

Uso:  python3 extraer_hss_atc.py <catalogo_atc.pdf>
Requiere pdftotext (poppler). Fuente: "Catalogo de productos" ATC, paginas impresas 08 a 10 (PDF 12 a 15).

Reglas (decisiones del usuario):
- Valores de I, S, r, peso y area: como vienen impresos en el catalogo. Las filas con alerta de consistencia
  se conservan tal cual y se marcan en 'alerta_catalogo'; no se corrigen.
- J: formula de pared delgada de seccion cerrada, J = 2 t (b-t)^2 (h-t)^2 / (b+h-2t), con b, h nominales y t el espesor.
- Zx = b h^2/4 - (b-2t)(h-2t)^2/4 (seccion sin radios de esquina); Zy analogo. Cw = 0 (seccion cerrada).
- Designacion en pulgadas (h x b x espesor) y conversion a cm (1 in = 2.54 cm).
"""
import csv, hashlib, json, math, os, re, subprocess, sys

SHA_PDF = None   # se verifica si se conoce; el SHA del PDF usado se escribe en el JSON
FR = {'3/16': 3 / 16, '1/4': 1 / 4, '5/16': 5 / 16, '3/8': 3 / 8, '1/2': 1 / 2}
PAG_PDF_A_IMPRESA = {12: '08', 13: '09', 14: '10', 15: '11'}
TOLERANCIA_S_R = 0.03   # verificacion de consistencia (S = I/c y r = sqrt(I/A)), solo para la alerta


def _num(t):
    if t.count('.') >= 2:
        t = t.replace('.', '', t.count('.') - 1)     # miles con punto: 1.123.8 -> 1123.8
    return float(t)


def _texto_paginas(pdf):
    out = subprocess.run(['pdftotext', '-f', '12', '-l', '15', '-layout', pdf, '-'],
                         capture_output=True, text=True, check=True).stdout
    return out.split('\f')          # una cadena por pagina (PDF 12..15)


def extraer(pdf):
    filas = []
    for k, texto in enumerate(_texto_paginas(pdf)):
        pagina_pdf = 12 + k
        seccion, marcas, ultimo = None, [], None
        bloque = []

        def cerrar(bloque, marcas, seccion):
            if not bloque:
                return
            if len(marcas) != 1:
                raise SystemExit(f'agrupacion ambigua en PDF {pagina_pdf}: {len(marcas)} marcas')
            h, b = marcas[0] if seccion == 'RHS' else (marcas[0][0], marcas[0][0])
            for fr, v in bloque:
                esperado = 5 if seccion == 'SHS' else 8
                if len(v) != esperado:
                    raise SystemExit(f'columnas inesperadas en PDF {pagina_pdf}: {fr} {v}')
                if seccion == 'SHS':
                    peso, area, I, S, r = v; Iy, Sy, ry = I, S, r
                else:
                    peso, area, I, S, r, Iy, Sy, ry = v
                filas.append(dict(seccion=seccion, h_in=h, b_in=b, t_frac=fr, pagina=PAG_PDF_A_IMPRESA[pagina_pdf],
                                  peso=peso, area=area, Ix=I, Sx=S, rx=r, Iy=Iy, Sy=Sy, ry=ry))

        for linea in texto.split('\n'):
            if 'HSS Cuadrado' in linea:
                cerrar(bloque, marcas, seccion); bloque, marcas, ultimo = [], [], None; seccion = 'SHS'
            if 'HSS Rectangular' in linea:
                cerrar(bloque, marcas, seccion); bloque, marcas, ultimo = [], [], None; seccion = 'RHS'
            if seccion is None:
                continue
            m = re.search(r'(\d+)"\s*[xX]\s*(\d+)"', linea)
            if m:
                marcas.append((int(m.group(1)), int(m.group(2))))
            m2 = re.search(r'(\d/\d+)"((?:\s+[\d.]+)+)\s*$', linea)
            if m2 and m2.group(1) in FR:
                fr = m2.group(1)
                # nuevo grupo cuando el espesor no crece (cada grupo va de menor a mayor espesor)
                if ultimo is not None and FR[fr] <= ultimo:
                    cerrar(bloque, marcas, seccion); bloque, marcas = [], []
                bloque.append((fr, [_num(x) for x in m2.group(2).split()]))
                ultimo = FR[fr]
        cerrar(bloque, marcas, seccion)
    return filas


def propiedades(f):
    """Pasa a cm, calcula J, Z y marca alertas de consistencia (no corrige)."""
    h, b, t = f['h_in'] * 2.54, f['b_in'] * 2.54, FR[f['t_frac']] * 2.54
    A = f['area']
    d = {}
    d['j'] = 2.0 * t * (b - t) ** 2 * (h - t) ** 2 / (b + h - 2.0 * t)
    d['zx'] = b * h ** 2 / 4.0 - (b - 2.0 * t) * (h - 2.0 * t) ** 2 / 4.0
    d['zy'] = h * b ** 2 / 4.0 - (h - 2.0 * t) * (b - 2.0 * t) ** 2 / 4.0
    notas = []
    for nombre, val, ref in [('Sx', f['Sx'], f['Ix'] / (h / 2)), ('Sy', f['Sy'], f['Iy'] / (b / 2))]:
        if abs(val / ref - 1) > TOLERANCIA_S_R:
            notas.append(f'{nombre} impreso {val:g} no coincide con I/c = {ref:.1f}')
    for nombre, val, ref in [('rx', f['rx'], math.sqrt(f['Ix'] / A)), ('ry', f['ry'], math.sqrt(f['Iy'] / A))]:
        if abs(val / ref - 1) > TOLERANCIA_S_R:
            notas.append(f'{nombre} impreso {val:g} no coincide con sqrt(I/A) = {ref:.2f}')
    d['alerta'] = '; '.join(notas)
    d['h'], d['b'], d['t'] = h, b, t
    return d


def registro(f):
    p = propiedades(f)
    h_in, b_in = f['h_in'], f['b_in']
    fr = f['t_frac']
    nombre = f'HSS {h_in} × {b_in} × {fr}'
    return {
        'perfil_comercial': nombre,
        'familia': 'HSS',
        'designacion_pulgadas': f'{h_in}" x {b_in}" x {fr}"',
        'seccion': 'cuadrada' if f['seccion'] == 'SHS' else 'rectangular',
        'd_ala_diametro_cm': round(p['h'], 4),
        'bf_b_cm': round(p['b'], 4),
        'tw_cm': round(p['t'], 4),
        'tf_t_cm': round(p['t'], 4),
        'area_cm2': f['area'], 'ix_cm4': f['Ix'], 'iy_cm4': f['Iy'],
        'sx_cm3': f['Sx'], 'sy_cm3': f['Sy'], 'rx_cm': f['rx'], 'ry_cm': f['ry'],
        'j_cm4': round(p['j'], 2), 'cw_cm6': 0.0,
        'zx_cm3': round(p['zx'], 2), 'zy_cm3': round(p['zy'], 2), 'ro_cm': None,
        'masa_kg_m': f['peso'], 'estado': 'Catálogo ATC',
        'pagina_manual': None, 'pagina_pdf': None,
        'pagina_catalogo_atc': f['pagina'],
        'referencia_catalogo': f'ATC, Catálogo de productos, pág. impresa {f["pagina"]} (HSS)',
        'campos_pendientes': [], 'fuente_completado': None,
        'alerta_catalogo': p['alerta'] or None,
        'fuente_propiedades': 'J: formula de pared delgada (seccion cerrada). Zx, Zy: seccion sin radios de esquina. Cw = 0. Resto: catalogo ATC.',
    }


def main():
    pdf = sys.argv[1]
    filas = extraer(pdf)
    regs = [registro(f) for f in filas]
    nombres = [r['perfil_comercial'] for r in regs]
    assert len(set(nombres)) == len(nombres), 'nombres repetidos'
    sha = hashlib.sha256(open(pdf, 'rb').read()).hexdigest()
    out = {'fuente': 'Catálogo de productos ATC (Aceros y Tubulares de la Costa S.A. de C.V.), páginas impresas 08 a 10',
           'sha256_pdf': sha, 'n_registros': len(regs),
           'n_con_alerta_catalogo': sum(1 for r in regs if r['alerta_catalogo']),
           'perfiles': regs}
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hss_atc_catalogo.json')
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print('registros:', len(regs), '| con alerta de catalogo (se mantienen):', out['n_con_alerta_catalogo'])
    print('sha256 pdf:', sha[:16], '| escrito:', ruta)


if __name__ == '__main__':
    main()
