"""
MEMORIA DE CALCULO del diseno ASD (AISC 360-22) por barra, en HTML imprimible (Archivo > Imprimir > PDF).
Usa el mismo motor que el bloque 10 (diseno_asd.py): cada numero de la memoria sale de los mismos calculos.
Por barra: datos de entrada, propiedades, cada verificacion con su ecuacion, los valores sustituidos y el FU.
Unidades: fuerzas kgf, momentos kgf·cm, longitudes cm, esfuerzos kgf/cm2.
"""
import base64
import copy
import html
import io
import math

import numpy as np
import pandas as pd
import diseno_asd as DA
import perfiles_gerdau as G

CSS = """
body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #1b1b1b; margin: 24px; }
h1 { font-size: 16pt; margin: 0 0 4px 0; }
h2 { font-size: 12pt; border-bottom: 1.5px solid #1F4E79; color: #1F4E79; margin: 22px 0 8px 0; padding-bottom: 2px; }
h3 { font-size: 10.5pt; color: #1F4E79; margin: 12px 0 4px 0; }
h4 { font-size: 9.5pt; color: #1F4E79; margin: 9px 0 3px 0; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 8px 0; font-size: 9pt; }
th, td { border: 1px solid #b9c7d6; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #DDEBF7; }
td.num { text-align: right; white-space: nowrap; }
.meta td { border: none; padding: 1px 6px 1px 0; }
.cumple { color: #1e6b33; font-weight: bold; }
.nocumple { color: #a61b1b; font-weight: bold; }
.pend { color: #8a5a00; font-weight: bold; }
.nota { color: #555; font-size: 8.5pt; }
.norev { color: #8a5a00; font-weight: bold; }
.barra { page-break-inside: avoid; margin-top: 18px; }
.ec { font-family: 'Courier New', monospace; font-size: 8.5pt; }
@media print { body { margin: 10mm; } h2 { page-break-after: avoid; } }
"""


def _v(x, dec=2):
    """Numero con separador de miles y punto decimal; guion si no hay dato."""
    if x is None:
        return '—'
    if isinstance(x, str):
        return html.escape(x)
    try:
        x = float(x)
    except (TypeError, ValueError):
        return html.escape(str(x))
    if math.isnan(x):
        return '—'
    if abs(x) >= 1000:
        return f'{x:,.0f}'
    return f'{x:,.{dec}f}'


def _fu(x):
    if x is None or isinstance(x, str):
        return '—' if x is None else html.escape(x)
    cls = 'cumple' if x <= 1.0 else 'nocumple'
    if not math.isfinite(x):
        return f'<span class="{cls}">no admisible</span>'
    return f'<span class="{cls}">{x:.3f}</span>'


def _evaluar(dib, i, id_barra, lon, mat, comb):
    """Evalua la barra i con el motor del bloque 10 y devuelve todo lo necesario para la memoria."""
    b = dib.barras[i]
    id_ = id_barra.get(i, i)
    out = dict(id=id_, perfil=b['perfil'], grupo=b['elemento'], material=b.get('material'))
    fam = G.obtener_perfil(b['perfil'])
    if fam is None:
        out.update(estado='NO REVISADO', motivo='perfil no existe en la base Gerdau')
        return out
    familia = fam['familia']
    out['familia'] = familia
    if familia not in DA.FAMILIAS_ASD:
        out.update(estado='FUERA DE ALCANCE', motivo=f'familia {familia}: no se disena (solo IR, CE, LI y HSS)')
        return out
    e = DA._entrada_barra(dib, i, id_barra, lon, mat)
    m = e['m']
    out.update(L=e['L'], lx=e['lx'], ly=e['ly'], lb=e['lb'], kx=e['kx'], ky=e['ky'], cb=e['cb'],
               e5=e['e5'], conexion=e['conexion'], l_li=e['l_li'])
    supuestos = list(e['supuestos'])
    if m is None or m['fy'] is None or m['E'] is None or m['nu'] is None:
        out.update(estado='NO REVISADO', motivo='material sin fy, E o nu en MATERIALES', supuestos=supuestos)
        return out
    out.update(fy=m['fy'], fu=m['fu'], E=m['E'], nu=m['nu'])
    p, falta = DA._props_asd(b['perfil'], familia)
    if p is None:
        out.update(estado='NO REVISADO', motivo=falta, supuestos=supuestos)
        return out
    es_li = familia == 'LI'
    e5_b = es_li and e['e5']
    u_b = DA.factor_u_angulo(p['xc'], e['l_li'], e['conexion']) if es_li else 1.0
    if es_li:
        supuestos += e['sup_li']
    supuestos += ['estimado: ' + s for s in p.get('_estimados', [])]
    out.update(p=p, U=u_b, e5_b=e5_b, supuestos=supuestos)
    f = comb[comb['BARRA'] == id_]
    dem = [DA._demanda_fila(x) for _, x in f.iterrows()]
    casos = [x['CASO'] for _, x in f.iterrows()]
    ev = DA._chequear(p, familia, m['fy'], m['fu'], m['E'], m['nu'], e['lx'] * 100.0, e['ly'] * 100.0,
                      e['lb'] * 100.0, e['kx'], e['ky'], b['elemento'], dem, cb=e['cb'],
                      e5=e5_b, u_t=u_b)
    if ev['motivo'] and any(d['Pr_c'] > 0 for d in dem):
        out.update(estado='NO REVISADO', motivo='NO REVISADO: ' + ev['motivo'])
        return out
    out.update(ev=ev, res=ev['res'], klr=ev['klr'])
    if not dem:
        out.update(estado='SIN COMBINACIONES', fu_res=None)
        return out
    if familia != 'HSS' and any(d.get('Tr', 0.0) > 0 for d in dem):              # H3: solo HSS
        supuestos.append('torsión de la barra (T): H3 aplica a HSS')
    pares = list(zip(ev['filas'], casos))
    fu = DA._resumen_fu(ev, pares)
    out.update(fu_res=fu, estado='CUMPLE' if fu['FU MAXIMO'] <= 1.0 else 'NO CUMPLE')
    out.update(dem_all=dem, casos_all=casos)
    mejor = None
    for (u, caso), d in zip(pares, dem):
        vals = [u[c] for c in DA.CHEQUEOS_DEMANDA if u.get(c) is not None]
        mx = max(vals) if vals else 0.0
        if mejor is None or mx > mejor[0]:
            mejor = (mx, caso, d)
    out.update(caso_dem=mejor[1], dem=mejor[2])
    return out


def _props_tabla(v):
    p, familia = v['p'], v['familia']
    if familia == 'LI':
        filas = [('Lado b (pata)', p['H'], 'cm'), ('Espesor t', p['t'], 'cm'), ('Area Ag', p['A'], 'cm²'),
                 ('Ix = Iy (catálogo)', p['Ix'], 'cm⁴'), ('Centroide x̄ = ȳ', p['xc'], 'cm'),
                 ('Producto de inercia Ixy', p['Ixy'], 'cm⁴'), ('Iu (eje mayor principal)', p['Iu'], 'cm⁴'),
                 ('Iv (eje menor principal)', p['Iv'], 'cm⁴'), ('ru', p['ru'], 'cm'), ('rz', p['rz'], 'cm'),
                 ('Su (u)', p['Su'], 'cm³'), ('Sv (v)', p['Sv'], 'cm³'), ('J (catálogo)', p.get('J'), 'cm⁴')]
    elif familia == 'HSS':
        tn = p.get('t_nominal', p['t'])
        filas = [('Peralte H', p['H'], 'cm'), ('Ancho B', p['B'], 'cm'),
                 ('Espesor nominal t (catálogo)', tn, 'cm'),
                 (f'Espesor de diseño t = {DA.FACTOR_ESPESOR_HSS:g} · t nominal (B4.2)', p['t'], 'cm'),
                 ('Ancho plano bp = B − 3t (con t de diseño)', p['B'] - 3.0 * p['t'], 'cm'),
                 ('Peralte plano hp = H − 3t (con t de diseño)', p['H'] - 3.0 * p['t'], 'cm'),
                 ('Área Ag (diseño)', p['A'], 'cm²'), ('Ix (diseño)', p['Ix'], 'cm⁴'), ('Iy (diseño)', p['Iy'], 'cm⁴'),
                 ('Sx (diseño)', p['Sx'], 'cm³'), ('Sy (diseño)', p['Sy'], 'cm³'),
                 ('Zx (diseño)', p['Zx'], 'cm³'), ('Zy (diseño)', p['Zy'], 'cm³'),
                 ('rx (diseño)', p['rx'], 'cm'), ('ry (diseño)', p['ry'], 'cm'), ('J (diseño)', p['J'], 'cm⁴')]
    else:
        filas = [('Peralte H', p['H'], 'cm'), ('Ancho B', p['B'], 'cm'), ('Espesor del alma e', p['e'], 'cm'),
                 ('Espesor del patín t', p['t'], 'cm'), ('Area Ag', p['A'], 'cm²'), ('Ix', p['Ix'], 'cm⁴'),
                 ('Iy', p['Iy'], 'cm⁴'), ('Sx', p['Sx'], 'cm³'), ('Sy', p['Sy'], 'cm³'), ('Zx', p['Zx'], 'cm³'),
                 ('Zy', p['Zy'], 'cm³'), ('rx', p['rx'], 'cm'), ('ry', p['ry'], 'cm'), ('J', p['J'], 'cm⁴'),
                 ('Cw', p['Cw'], 'cm⁶')]
        if familia == 'CE':
            filas.append(('ro', p.get('ro'), 'cm'))
    body = ''.join(f'<tr><td>{html.escape(n)}</td><td class="num">{_v(x, 3)}</td><td>{u}</td></tr>'
                   for n, x, u in filas)
    if familia == 'HSS' and p.get('t_nominal') is not None:
        body += ('<tr><td colspan="3" class="nota">AISC 360-22 B4.2: propiedades de diseño = catálogo × razón entre la '
                 'sección de esquina viva con t de diseño y con t nominal (A, I, S, Z, J); r = r catálogo · √(razón I / '
                 'razón A). Con t nominal la razón es 1. Masa sin cambio. El análisis (OpenSees) usa estas mismas propiedades.</td></tr>')
    if p.get('pagina_manual') is not None:
        body += f'<tr><td colspan="3" class="nota">Catálogo Gerdau rev04, pág. impresa {p["pagina_manual"]}.</td></tr>'
    if p.get('pagina_catalogo_atc'):
        body += (f'<tr><td colspan="3" class="nota">Catálogo ATC, pág. impresa {p["pagina_catalogo_atc"]}. '
                 'J por fórmula de pared delgada; Zx y Zy sin radios de esquina; Cw = 0.</td></tr>')
    if p.get('fuente_completado'):
        body += f'<tr><td colspan="3" class="nota">Completado desde el manual: {html.escape(p["fuente_completado"])}.</td></tr>'
    if any('estimado' in s for s in v.get('supuestos', [])):
        body += '<tr><td colspan="3" class="nota">Valores marcados como estimados en supuestos (geometría).</td></tr>'
    return f'<table><tr><th>Propiedad</th><th>Valor</th><th>Unidad</th></tr>{body}</table>'


def _verificaciones(v):
    """Filas de la tabla de verificaciones: (verificacion, ecuacion, calculo sustituido, capacidad, demanda, FU)."""
    res, fu, p, familia = v['res'], v['fu_res'], v['p'], v['familia']
    fy, fuu, U, A = v['fy'], v['fu'], v['U'], p['A']
    d = v.get('dem') or {}
    dem_all = v.get('dem_all') or []
    ev_filas = (v.get('ev') or {}).get('filas') or []

    def dem_de(chequeo):
        """Demanda de la combinacion que controla ESTA verificacion (no la de toda la barra)."""
        if not dem_all or len(ev_filas) != len(dem_all):
            return d
        idx = max(range(len(ev_filas)),
                  key=lambda k: ev_filas[k].get(chequeo) if ev_filas[k].get(chequeo) is not None else -1.0)
        return dem_all[idx]

    filas = []
    # Traccion
    calc_t = f'Fy·Ag/Ωt = {_v(fy, 1)}·{_v(A, 3)}/1.67 = {_v(res["Pa_t_fluencia"], 1)}'
    if fuu:
        calc_t += (f'; Fu·U·Ag/Ωt = {_v(fuu, 1)}·{_v(U, 3)}·{_v(A, 3)}/2.00 = {_v(res["Pa_t_fractura"], 1)}')
    filas.append(('Tracción', '§D2: D2-1 Pn = Fy·Ag (Ωt = 1.67); D2-2 Pn = Fu·Ae (Ωt = 2.00). §D3 Tabla D3.1: Ae = U·Ag (ángulos)' if familia == 'LI' else '§D2: D2-1 Pn = Fy·Ag (Ωt = 1.67); D2-2 Pn = Fu·Ae (Ωt = 2.00), Ae = Ag',
                  calc_t + f'; Pa = mín = {_v(res["Pa_t"], 1)}', res['Pa_t'], dem_de('T traccion').get('Pr_t'), fu and fu['FU TRACCION']))
    # Compresion
    dc = res['detalle_c']
    if familia == 'LI':
        klr_txt = f'λz = {_v(dc["lam_z"], 1)} (eje z), λu = {_v(dc["lam_u"], 1)} (eje u)'
        ecu_c = '§E3: E3-4 Fe = π²E/(KL/r)², E3-2/E3-3 Fn. §E5: E5-1/E5-2 (Lc/rz) si se verifica. §E7: Ae con patas. Ωc = 1.67'
    else:
        klr_txt = f'KL/rx = {_v(res["KLr_fuerte"], 1)}; KL/ry = {_v(res["KLr_debil"], 1)}'
        ecu_c = '§E3: E3-4 Fe, E3-2/E3-3 Fn. §E4: E4-2, E4-3 (Fex), E4-7. §E7: Ae = Ag − Σ(b − be)·t. Ωc = 1.67'
    if familia == 'HSS':
        ecu_c = ('§E3: E3-4 Fe (Fex, Fey; sección cerrada sin pandeo torsional), E3-2/E3-3 Fn. '
                 '§E7.1: Ae = Ag − Σ(b − be)·t, be por E7-2/E7-3 (c1 = 0.20, c2 = 1.38; λr = 1.40√(E/Fy)). Ωc = 1.67')
    calc_c = (f'{klr_txt}; gobierna {html.escape(str(dc.get("gobierna")))}; '
              + (f'Fe = {_v(dc["Fe"], 1)} kgf/cm²; ' if 'Fe' in dc else '') +
              f'Fn = {_v(dc["Fn"], 1)} kgf/cm²; Ae = {_v(dc["Ae"], 3)} cm²; '
              f'Pn = Fn·Ae = {_v(dc["Fn"] * dc["Ae"], 0)}')
    if fu and fu['FU COMPRESION'] == 0.0:
        calc_c += '; sin compresión en las combinaciones'
    filas.append(('Compresión', ecu_c, calc_c, res['Pa_c'], dem_de('C compresion').get('Pr_c'), fu and fu['FU COMPRESION']))
    # Flexion eje mayor
    dx = res['detalle_x']
    if familia == 'LI':
        calc_x = (f'My = Fy·Su = {_v(dx["My"], 1)}; Mcr (F10-4) = {_v(dx["Mcr"], 1)}; LTB (F10-2/3) = {_v(dx["LTB"], 1)}; '
                  f'Mn = {_v(dx["Mn"], 1)}')
        ecu_x = '§F10: F10-1 Mn = 1.5·My; F10-2/F10-3 LTB; F10-4 Mcr (βw = 0). §F10.3: F10-6 a F10-8 (pata). Ωb = 1.67'
        dfx = dem_de('F flexion eje mayor')
        mr = math.hypot(dfx.get('Mr_x', 0.0), dfx.get('Mr_y', 0.0)) if dfx else None
    else:
        calc_x = (f'Mp = Fy·Zx = {_v(dx["Mp"], 1)}; LTB (F2) = {_v(dx["LTB"], 1)}; patín (F3) = {_v(dx.get("LFB"), 1)}; '
                  f'Mn = {_v(min(dx["LTB"], dx.get("LFB", dx["LTB"])), 1)}')
        ecu_x = '§F2: F2-1 Mn = Mp; F2-2 LTB inelástico; F2-3 LTB elástico (F2-4 a F2-8). §F3: F3-1, F3-2 (patín). Ωb = 1.67'
        mr = dem_de('F flexion eje mayor').get('Mr_x')
    if familia == 'HSS':
        calc_x = (f'Mp = Fy·Zx = {_v(dx["Mp"], 1)}; patín (F7-2/F7-3) = {_v(dx["LFB"], 1)}; '
                  f'alma (F7-6) = {_v(dx["LWB"], 1)}; LTB (F7-8/F7-9) = {_v(dx["LTB"], 1)}; Mn = {_v(dx["Mn"], 1)}')
        ecu_x = ('§F7: F7-1 Mn = Mp = Fy·Z; F7-2 y F7-3 patín (F7-4: be); F7-6 alma; '
                 '§F7.4: F7-8 y F7-9 LTB (F7-10 y F7-11). Ωb = 1.67')
    filas.append(('Flexión eje mayor', ecu_x, calc_x + f'; Ma = Mn/1.67 = {_v(res["Ma_x"], 1)}',
                  res['Ma_x'], mr, fu and fu['FU FLEXION EJE MAYOR']))
    # Flexion eje menor
    dy = res['detalle_y']
    if familia == 'LI':
        calc_y = f'My = Fy·Sv = {_v(dy["My"], 1)}; Mn = mín(1.5My; LLB) = {_v(dy["Mn"], 1)}'
        ecu_y = '§F10: F10-1 Mn = 1.5·My. §F10.3: F10-6 a F10-8 (pata, eje v). Ωb = 1.67'
        dfy = dem_de('F flexion eje menor')
        mr_y = math.hypot(dfy.get('Mr_x', 0.0), dfy.get('Mr_y', 0.0)) if dfy else None
    else:
        calc_y = (f'Mp = mín(Fy·Zy; 1.6·Fy·Sy) = {_v(dy["Mp"], 1)}; My = Fy·Sy = {_v(dy["My"], 1)}')
        ecu_y = '§F6: F6-1 Mp = mín(Fy·Zy; 1.6·Fy·Sy); F6-2, F6-3 (patín y alma). Ωb = 1.67'
        mr_y = dem_de('F flexion eje menor').get('Mr_y')
    if familia == 'HSS':
        calc_y = (f'Mp = Fy·Zy = {_v(dy["Mp"], 1)}; patín (F7-2/F7-3) = {_v(dy["LFB"], 1)}; '
                  f'alma (F7-6) = {_v(dy["LWB"], 1)}; Mn = {_v(dy["Mn"], 1)}')
        ecu_y = ('§F7 (eje menor; las paredes verticales hacen de patín): F7-1, F7-2/F7-3, F7-6. '
                 'Sin pandeo lateral-torsional. Ωb = 1.67')
    filas.append(('Flexión eje menor', ecu_y, calc_y + f'; Ma = {_v(res["Ma_y"], 1)}',
                  res['Ma_y'], mr_y, fu and fu['FU FLEXION EJE MENOR']))
    # Cortante
    dvx, dvy = res['detalle_vx'], res['detalle_vy']
    if familia == 'LI':
        calc_vx = f'Vn = 0.6·Fy·b·t·Cv2 = 0.6·{_v(fy, 1)}·{_v(p["b"], 3)}·{_v(p["t"], 3)}·{_v(dvx["Cv2"], 3)}; Ωv = 1.67'
        ecu_vx = '§G3: G3-1 Vn = 0.6·Fy·b·t·Cv2 (una pata, kv = 1.2). Ωv = 1.67'
        ecu_vy = '§G3: G3-1 (una pata). Ωv = 1.67'
        calc_vy = calc_vx
    else:
        calc_vx = (f'Vn = 0.6·Fy·Aw·Cv1 = 0.6·{_v(fy, 1)}·{_v(p["H"] * p["e"], 2)}·{_v(dvx["Cv1"], 3)}; '
                   f'Ωv = 1.50 si I laminada, 1.67 si no')
        ecu_vx = '§G2.1: G2-1 Vn = 0.6·Fy·Aw·Cv1; G2-2 (I laminada, Ωv = 1.50). §G2.2: G2-3, G2-4 (kv = 5.34). Ωv = 1.67'
        calc_vy = (f'Vn = 2·0.6·Fy·B·t·Cv2 = 2·0.6·{_v(fy, 1)}·{_v(p["B"], 2)}·{_v(p["t"], 3)}·{_v(dvy["Cv2"], 3)}; Ωv = 1.67')
        ecu_vy = '§G6: Vn = 2·0.6·Fy·B·t·Cv2 (dos patines, kv = 1.2). Ωv = 1.67'
    if familia == 'HSS':
        calc_vx = (f'Vn = 0.6·Fy·Aw·Cv2 = 0.6·{_v(fy, 1)}·{_v(dvx["Aw"], 2)}·{_v(dvx["Cv2"], 3)}; '
                   f'Aw = 2·h·t, h/t = {_v(dvx["h_tw"], 2)}; Ωv = 1.67')
        calc_vy = (f'Vn = 0.6·Fy·Aw·Cv2 = 0.6·{_v(fy, 1)}·{_v(dvy["Aw"], 2)}·{_v(dvy["Cv2"], 3)}; '
                   f'Aw = 2·h·t, h/t = {_v(dvy["h_tw"], 2)}; Ωv = 1.67')
        ecu_vx = '§G4: G4-1 Vn = 0.6·Fy·Aw·Cv2, Aw = 2·h·t (h = peralte plano). Cv2 de §G2.2: G2-9 a G2-11 con kv = 5. Ωv = 1.67'
        ecu_vy = '§G4: G4-1 Vn = 0.6·Fy·Aw·Cv2, Aw = 2·h·t (h = ancho plano). Cv2 de §G2.2 con kv = 5. Ωv = 1.67'
    filas.append(('Cortante eje mayor', ecu_vx, calc_vx + f'; Va = {_v(res["Va_x"], 1)}', res['Va_x'],
                  dem_de('V cortante eje mayor').get('Vr_x'), fu and fu['FU CORTANTE EJE MAYOR']))
    filas.append(('Cortante eje menor', ecu_vy, calc_vy + f'; Va = {_v(res["Va_y"], 1)}', res['Va_y'],
                  dem_de('V cortante eje menor').get('Vr_y'), fu and fu['FU CORTANTE EJE MENOR']))
    # Interaccion
    if familia == 'LI':
        ecu_i = '§H2: H2-1 fra/Fca + frbw/Fcbw + frbz/Fcbz ≤ 1 (Mr = momento resultante sobre cada eje principal)'
        calc_i = (f'Pa compresión = {_v(res["Pa_c"], 1)} kgf; Pa tracción = {_v(res["Pa_t"], 1)} kgf; '
                  f'Mau = {_v(res["Ma_x"], 1)} kgf·cm; Mav = {_v(res["Ma_y"], 1)} kgf·cm')
    else:
        ecu_i = '§H1.1: H1-1a Pr/Pc + 8/9·(Mrx/Mcx + Mry/Mcy) ≤ 1 (Pr/Pc ≥ 0.2); H1-1b Pr/(2Pc) + (Mrx/Mcx + Mry/Mcy) ≤ 1 (Pr/Pc < 0.2)'
        calc_i = f'Pc = {_v(res["Pa_c"], 1)} (compresión) o Pt = {_v(res["Pa_t"], 1)} (tracción)'
    if familia == 'HSS' and res.get('Tc') is not None:                           # H3: torsion y H3.2
        dt = res['detalle_t']
        tr = d.get('Tr', 0.0) if d else 0.0
        calc_t = (f'h = {_v(dt["h"], 3)} cm (lado plano mayor), h/t = {_v(dt["ht"], 2)}, {dt["reg"]}: '
                  f'Fcr = {_v(dt["Fcr"], 1)} kgf/cm²; C = {_v(dt["C"], 2)} cm³; Tn = Fcr·C = {_v(dt["Tn"], 0)} kgf·cm; '
                  f'Tc = Tn/ΩT = {_v(res["Tc"], 0)} kgf·cm')
        filas.append(('Torsión', '§H3.1: H3-1 Tn = Fcr·C; H3-3, H3-4 o H3-5 para Fcr; C = 2(B−t)(H−t)t − 4.5(4−π)t³ '
                      '(nota de usuario). ΩT = 1.67', calc_t, res['Tc'], tr, fu and fu['FU TORSION (H3.1)']))
        activa = tr > 0.2 * res['Tc']
        ecu_i = ('§H3.2: si Tr ≤ 0.2·Tc, interacción H1 y la torsión se descarta. Si Tr > 0.2·Tc: '
                 'H3-6 Pr/Pc + Mrx/Mcx + Mry/Mcy + (Vr/Vc + Tr/Tc)² ≤ 1.0')
        calc_i = (f'Tr/Tc = {_v(tr / res["Tc"], 3)}: ' + ('aplica H3-6' if activa else 'aplica H1 (torsión descartada)')
                  + (f'; H3-6 = {_v(d["Pr_c"] / res["Pa_c"] if d.get("Pr_c", 0) > 0 else 0.0, 3)} (P) + {_v(d["Mr_x"] / res["Ma_x"], 3)} (Mx) + '
                     f'{_v(d["Mr_y"] / res["Ma_y"], 3)} (My) + ...' if activa and d else ''))
    filas.append(('Interacción', ecu_i, calc_i, None, None, fu and fu['FU INTERACCION (H1/H2)']))
    return filas


def _estado_txt(ok):
    if ok is None:
        return '—'
    return f'<span class="{"cumple" if ok else "nocumple"}">{"CUMPLE" if ok else "NO CUMPLE"}</span>'


CAB_VERIF = ('<tr><th>Verificación</th><th>Ecuación</th><th>Cálculo</th><th>Límite / capacidad</th>'
             '<th>Calculado / demanda</th><th>FU o estado</th></tr>')


def _fila_verif(nombre, ecu, calc, cap, dem, fu, familia):
    return (f'<tr><td>{nombre}{_refs_verif(nombre, familia)}</td><td class="ec">{html.escape(ecu)}</td>'
            f'<td class="ec">{calc}</td><td class="num">{_v(cap, 1) if cap is not None else "—"}</td>'
            f'<td class="num">{_v(dem, 1) if dem is not None else "—"}</td>'
            f'<td class="num">{_fu(fu)}</td></tr>')


def _tabla_esbeltez(v):
    """Paso 3: clasificacion de elementos (AISC B4.1) y esbeltez global KL/r (IMCA cap. E)."""
    ev = v['ev']
    cuerpo = []
    for nombre, (lam, lr) in ev['el_det'].items():
        cuerpo.append(f'<tr><td>Esbeltez local: {html.escape(nombre)}{_ref_local(v)}</td>'
                      f'<td class="ec">AISC 360-22 Tabla B4.1a (compresión) / B4.1b (flexión): λ ≤ λr</td>'
                      f'<td class="ec">λ = {_v(lam, 2)}; λr = {_v(lr, 2)}</td>'
                      f'<td class="num">{_v(lr, 2)}</td><td class="num">{_v(lam, 2)}</td>'
                      f'<td class="num">{_estado_txt(lam <= lr)}</td></tr>')
    if DA.CHEQUEO_EG in ev['const']:
        lim = DA.LIMITE_KLR
        cuerpo.append(f'<tr><td>Esbeltez global{_ref_html("PROY_KLR")}</td>'
                      f'<td class="ec">IMCA cap. E: KL/r ≤ {lim:.0f}</td>'
                      f'<td class="ec">KL/r máx = {_v(v["klr"], 1)}</td><td class="num">{_v(lim, 0)}</td>'
                      f'<td class="num">{_v(v["klr"], 1)}</td><td class="num">{_estado_txt(v["klr"] <= lim)}</td></tr>')
    else:
        motivo = ('no aplica: elemento a flexión (VIGA); el límite de KL/r es para miembros comprimidos'
                  if v.get('grupo') == 'VIGA' else 'no aplica: sin compresión en ninguna combinación')
        cuerpo.append('<tr><td>Esbeltez global</td><td class="ec">IMCA cap. E: KL/r ≤ 200</td>'
                      f'<td class="ec">{motivo}</td><td class="num">—</td>'
                      '<td class="num">—</td><td class="num">—</td></tr>')
    return f'<table>{CAB_VERIF}{"".join(cuerpo)}</table>'


def _tabla_resistencias(v):
    """Paso 4: resistencias admisibles ASD (D traccion, E compresion, F flexion, G cortante, H3 torsion)."""
    cuerpo = [_fila_verif(n, e, c, cap, dem, fu, v['familia'])
              for n, e, c, cap, dem, fu in _verificaciones(v) if n != 'Interacción']
    return f'<table>{CAB_VERIF}{"".join(cuerpo)}</table>'


def _tabla_interaccion(v):
    """Paso 5: interaccion de flexocompresion y flexotension (H1, H2) o torsion combinada (H3)."""
    cuerpo = [_fila_verif(n, e, c, cap, dem, fu, v['familia'])
              for n, e, c, cap, dem, fu in _verificaciones(v) if n == 'Interacción']
    return f'<table>{CAB_VERIF}{"".join(cuerpo)}</table>'


def _resultado_barra(v):
    """Paso 6: FU de esfuerzos y de esbeltez, FU maximo, verificacion que gobierna y combinacion que controla."""
    fr = v['fu_res']

    def fila(concepto, valor, gobierna):
        return (f'<tr><td>{concepto}</td><td class="num">{_fu(valor)}</td>'
                f'<td>{html.escape(str(gobierna)) if gobierna else "—"}</td></tr>')
    cuerpo = (fila('FU de esfuerzos (D, E, F, G, H3)', fr.get('FU ESFUERZOS'), fr.get('ESFUERZO QUE GOBIERNA'))
              + fila('FU de esbeltez (B4.1 y KL/r)', fr.get('FU ESBELTEZ'), fr.get('ESBELTEZ QUE GOBIERNA')))
    return (f'<table><tr><th>Concepto</th><th>FU</th><th>Verificación que gobierna</th></tr>{cuerpo}</table>'
            f'<p>FU máximo de la barra = máx(FU de esfuerzos; FU de esbeltez) = <b>{_fu(fu_max(v))}</b>. '
            f'Estado: {_estado_txt(v["estado"] == "CUMPLE")}. Combinación que controla: '
            f'<b>{html.escape(str(v.get("caso_dem")))}</b>.</p>')


COLS_GRUPO = ['ID', 'PERFIL', 'FU ESFUERZOS', 'ESFUERZO QUE GOBIERNA', 'FU ESBELTEZ', 'ESBELTEZ QUE GOBIERNA',
              'ELEM. LOCAL CRÍTICO', 'CLASIF. AISC (B4.1)', 'λ LOCAL CALC', 'λ LOCAL LÍMITE', 'KL/r CALC', 'KL/r LÍMITE',
              'ESTADO', 'NOTA']


def _interaccion(v):
    """FU de interaccion flexocompresion (H1-1 o H2-1), el maximo sobre combinaciones. Sin carga axial, H1 se reduce
    a Mrx/Mcx + Mry/Mcy: se toma la suma de los FU de flexion."""
    ev = v.get('ev')
    if not ev or not ev.get('filas'):
        return None
    vals = []
    for u in ev['filas']:
        x = u.get('H1 flexocompresion', u.get('H1 flexotension', u.get('H2 angulo (H2-1)')))
        if x is None:
            x = u.get('F flexion eje mayor', 0.0) + u.get('F flexion eje menor', 0.0)
        vals.append(x)
    return max(vals) if vals else None


def _fila_grupo(v):
    """Una fila de la tabla por grupo: FU de esfuerzos y de esbeltez (local y KL/r), valores calculados y limites, estado."""
    if 'res' not in v or not v.get('fu_res'):
        return [v['id'], v['perfil']] + [None] * 10 + [v['estado'], v.get('motivo', '')]
    ev = v['ev']
    crit, lam_c, lam_l = max(((n, l, r) for n, (l, r) in ev['el_det'].items()), key=lambda t: t[1] / t[2])
    klr_c = klr_l = None
    if DA.CHEQUEO_EG in v['ev']['const']:
        klr_c = round(v['klr'], 2)
        klr_l = DA.LIMITE_KLR
    nota = []
    if v['familia'] == 'LI' and not v['e5_b'] and DA.CHEQUEO_EG in v['ev']['const']:
        nota.append('E5 no aplicado: K L/rz y H2')
    if DA.CHEQUEO_EG not in v['ev']['const']:
        nota.append('KL/r no aplica (VIGA: elemento a flexión)' if v['grupo'] == 'VIGA'
                    else 'sin compresión en ninguna combinación: KL/r no aplica')
    clasif = (DA.clasificacion_flexion(v['p'], v['familia'], v['fy'], v['E']) if v['grupo'] == 'VIGA'
              else DA.clasificacion_compresion(v['p'], v['familia'], v['fy'], v['E']))
    fr = v['fu_res']
    return [v['id'], v['perfil'], round(fr['FU ESFUERZOS'], 3) if fr.get('FU ESFUERZOS') is not None else None,
            fr.get('ESFUERZO QUE GOBIERNA'), round(fr['FU ESBELTEZ'], 3) if fr.get('FU ESBELTEZ') is not None else None,
            fr.get('ESBELTEZ QUE GOBIERNA'), crit, clasif, round(lam_c, 2), round(lam_l, 2), klr_c, klr_l,
            v['estado'], '; '.join(nota)]


def resultados_grupo(dib, grupo, perfil, materiales_filas, longitudes_df, demandas, id_barra):
    """Tabla por grupo con un perfil elegido para todas sus barras (no cambia el modelo)."""
    d2 = copy.copy(dib)
    d2.barras = [dict(b, perfil=perfil) if b['elemento'] == grupo else b for b in dib.barras]
    mat, lon, comb = DA._preparar_entradas(materiales_filas, longitudes_df, demandas)
    filas = [_fila_grupo(_evaluar(d2, i, id_barra, lon, mat, comb))
             for i, b in enumerate(d2.barras) if b['elemento'] == grupo]
    return pd.DataFrame(filas, columns=COLS_GRUPO).fillna('—')


def opciones_grupo(fu_matriz, grupo):
    """Opciones del desplegable de un grupo: todas las secciones IR, CE y LI ordenadas por tipo y seccion, con el
    resultado para todas las barras del grupo (cada una con su demanda), segun FU_MATRIZ."""
    catalogo = sorted([n for n, d in G.PERFILES.items() if d['familia'] in DA.FAMILIAS_ASD], key=DA.clave_orden)
    peor = DA.fu_grupo_por_perfil(fu_matriz, grupo)
    det = DA.esbeltez_grupo_por_perfil(fu_matriz, grupo)
    ops = []
    for n in catalogo:
        if n not in peor:
            etiqueta = f'{n}  —  sin datos para este grupo'
        elif peor[n] is None:
            etiqueta = f'{n}  —  no revisado en alguna barra'
        else:
            x = peor[n]
            cumple = 'cumple' if x <= 1.0 else 'no cumple'
            r = det.get(n)
            if r is not None:
                etiqueta = f'{n}  —  {cumple} · FU esfuerzos {r[0]:.2f} · FU esbeltez {r[1]:.2f} ({r[2]})'
            else:
                etiqueta = f'{n}  —  {cumple} (FU máx {x:.2f})'
        ops.append((etiqueta, n))
    return ops


def _maximo_fila(u):
    """FU maximo de una combinacion (todas las verificaciones de demanda)."""
    vals = [u[c] for c in DA.CHEQUEOS_DEMANDA if u.get(c) is not None]
    return max(vals) if vals else None


def _inter_fila(u):
    """FU de interaccion flexocompresion de una combinacion (H1 o H2; sin axial, suma de los FU de flexion)."""
    x = u.get('H1 flexocompresion', u.get('H1 flexotension', u.get('H2 angulo (H2-1)')))
    if x is None:
        x = u.get('F flexion eje mayor', 0.0) + u.get('F flexion eje menor', 0.0)
    return x


def _tabla_combinaciones(v):
    """Demandas y FU de cada combinacion de servicio de la barra. Resalta la combinacion que controla."""
    dem_all, casos, filas = v.get('dem_all'), v.get('casos_all'), v['ev']['filas']
    if not dem_all:
        return '<p class="nota">Sin combinaciones de servicio para esta barra.</p>'
    k_max = max(range(len(filas)), key=lambda k: _maximo_fila(filas[k]) or 0.0)
    cuerpo = []
    for k, (d, caso, u) in enumerate(zip(dem_all, casos, filas)):
        est = ' style="font-weight:bold;background:#fff4d6"' if k == k_max else ''
        cuerpo.append(f'<tr{est}><td>{html.escape(str(caso))}</td><td class="num">{_v(d["Pr_t"], 1)}</td>'
                      f'<td class="num">{_v(d["Pr_c"], 1)}</td><td class="num">{_v(d["Mr_x"], 1)}</td>'
                      f'<td class="num">{_v(d["Mr_y"], 1)}</td><td class="num">{_v(d["Vr_x"], 1)}</td>'
                      f'<td class="num">{_v(d["Vr_y"], 1)}</td><td class="num">{_fu(_inter_fila(u))}</td>'
                      f'<td class="num">{_fu(_maximo_fila(u))}</td></tr>')
    return ('<table><tr><th>Combinación</th><th>Pr tracción (kgf)</th><th>Pr compresión (kgf)</th>'
            '<th>Mrx (kgf·cm)</th><th>Mry (kgf·cm)</th><th>Vrx (kgf)</th><th>Vry (kgf)</th>'
            '<th>FU interacción</th><th>FU máx. combinación</th></tr>' + ''.join(cuerpo) + '</table>')


def _bloque_barra(v):
    """Detalle de una barra en los pasos del calculo (seccion 1): 1 datos y propiedades, 2 demandas, 3 esbeltez,
    4 resistencias, 5 interaccion y 6 resultado. Cada paso lleva su ecuacion y su referencia."""
    if 'res' not in v or not v.get('fu_res'):
        return (f'<section class="barra"><h2>Barra {v["id"]} · {html.escape(v["perfil"])} · {v["grupo"]} · '
                f'{v["estado"]}</h2><p>{html.escape(v.get("motivo", ""))}</p></section>')
    cl = 'cumple' if v['estado'] == 'CUMPLE' else 'nocumple'
    datos = (f'<table class="meta"><tr><td><b>Material</b>: {html.escape(str(v["material"]))} · '
             f'Fy = {_v(v["fy"], 0)} kgf/cm² · Fu = {_v(v["fu"], 0)} kgf/cm² · E = {_v(v["E"], 0)} kgf/cm² · '
             f'ν = {_v(v["nu"], 2)}</td></tr>'
             f'<tr><td><b>Longitudes</b>: L = {_v(v["L"], 1)} cm · LX = {_v(v["lx"] * 100, 1)} cm · '
             f'LY = {_v(v["ly"] * 100, 1)} cm · LB = {_v(v["lb"] * 100, 1)} cm · KX = {_v(v["kx"], 2)} · '
             f'KY = {_v(v["ky"], 2)} · Cb = {_v(v["cb"], 2)}</td></tr>'
             + ('<tr><td><b>Ángulo</b>: E5 ' + ('verificado (LONGITUDES)' if v['e5_b'] else
                                                  'no cumple las cuatro condiciones de E5: se usa K L/rz y H2')
                + f' · conexión {html.escape(v["conexion"])} · U = {_v(v["U"], 3)} · l = {_v(v["l_li"], 1)} cm</td></tr>'
                if v['familia'] == 'LI' else '')
             + '</table>')
    sup = ''.join(f'<li>{html.escape(s)}</li>' for s in v.get('supuestos', []))
    return (f'<section class="barra" id="barra-{v["id"]}">'
            f'<h2>Barra {v["id"]} · {html.escape(v["perfil"])} · {html.escape(v["grupo"])} · '
            f'<span class="{cl}">{v["estado"]}</span> · FU máximo {_v(fu_max(v), 3)}</h2>'
            '<h3>Paso 1. Datos y propiedades de la sección</h3>'
            f'{datos}{_props_tabla(v)}'
            + (f'<h4>Supuestos de esta barra</h4><ul class="nota">{sup}</ul>' if sup else '')
            + '<h3>Paso 2. Demandas: combinaciones de servicio ASD</h3>'
            f'<p class="nota">Cada combinación se revisa con sus propias demandas. Resaltada: la que controla '
            f'(<b>{html.escape(str(v.get("caso_dem")))}</b>).</p>{_tabla_combinaciones(v)}'
            '<h3>Paso 3. Esbeltez: clasificación local (AISC B4.1) y KL/r (IMCA cap. E)</h3>'
            '<p class="nota">λ calculado frente a λr. KL/r ≤ 200 se verifica en miembros comprimidos; las vigas '
            '(elementos a flexión) están exentas.</p>'
            f'{_tabla_esbeltez(v)}'
            '<h3>Paso 4. Resistencias admisibles (ASD): D, E, F, G y H3</h3>'
            '<p class="nota">Capacidad = resistencia admisible; demanda = la de la combinación que controla esa '
            'verificación. FU = demanda / capacidad (cumple si FU ≤ 1.0).</p>'
            f'{_tabla_resistencias(v)}'
            '<h3>Paso 5. Interacción (H1, H2 o H3)</h3>'
            f'{_tabla_interaccion(v)}'
            '<h3>Paso 6. Resultado de la barra</h3>'
            f'{_resultado_barra(v)}'
            '</section>')


def fu_max(v):
    """FU maximo de la barra (todas las verificaciones)."""
    return v['fu_res']['FU MAXIMO']


def _desplazamientos(dib, casos, id_de_indice):
    """Desplazamiento maximo de los nodos por combinacion (mm). casos: [(nombre, tipo, res)], res['nodos'] en cm."""
    filas, mejor = [], None
    for nombre, tipo, res in casos:
        if tipo != 'COMBINACION':
            continue
        d = np.array([res['nodos'][i][:3] for i in range(len(dib.nodos))], float) * 10.0        # cm -> mm
        r = np.linalg.norm(d, axis=1)
        k = int(np.argmax(r))
        fila = dict(combinacion=nombre, ux=float(np.abs(d[:, 0]).max()), uy=float(np.abs(d[:, 1]).max()),
                    uz=float(np.abs(d[:, 2]).max()), resultante=float(r[k]), nodo=id_de_indice[k])
        filas.append(fila)
        if mejor is None or fila['resultante'] > mejor[0]['resultante']:
            mejor = (fila, res)
    return pd.DataFrame(filas), mejor


def _png_deformada(dib, res, titulo):
    """Imagen de la deformada (3D) de un caso: original en gris, deformada en azul. Devuelve (base64, escala)."""
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    P0 = np.array(dib.nodos, float)
    U = np.array([res['nodos'][i][:3] for i in range(len(P0))], float) / 100.0             # cm -> m
    tam = max(float(np.ptp(P0[:, k])) for k in range(3)) or 1.0
    dmax = float(np.max(np.linalg.norm(U, axis=1)))
    escala = 0.1 * tam / dmax if dmax > 0 else 1.0
    P = P0 + escala * U
    fig = Figure(figsize=(7.2, 5.4), dpi=110)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111, projection='3d')
    for b in dib.barras:
        a, c = b['n1'], b['n2']
        ax.plot([P0[a, 0], P0[c, 0]], [P0[a, 1], P0[c, 1]], [P0[a, 2], P0[c, 2]], color='#bbbbbb', ls='--', lw=1)
        ax.plot([P[a, 0], P[c, 0]], [P[a, 1], P[c, 1]], [P[a, 2], P[c, 2]], color='#1f77b4', lw=2.2)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title(titulo, fontsize=9)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    return base64.b64encode(buf.getvalue()).decode('ascii'), escala


# Referencias de las verificaciones: apartado y pagina del documento (AISC 360-22 y criterio del proyecto).
REF = {
    'D2': 'AISC 360-22 §D2, ecs. D2-1 y D2-2, pág. 16.1-32 y 16.1-33',
    'D3': 'AISC 360-22 §D3, Tabla D3.1 (factor U), pág. 16.1-34',
    'E3': 'AISC 360-22 §E3, ecs. E3-1 a E3-4, pág. 16.1-40 y 16.1-41',
    'E4': 'AISC 360-22 §E4, ecs. E4-2, E4-3 y E4-7, pág. 16.1-41 y 16.1-42',
    'E5': 'AISC 360-22 §E5 (ángulos sencillos), ecs. E5-1 y E5-2, pág. 16.1-43 y 16.1-44',
    'E7': 'AISC 360-22 §E7 (elementos esbeltos), pág. 16.1-48 y 16.1-49',
    'F2': 'AISC 360-22 §F2, ecs. F2-1 a F2-8, pág. 16.1-53 y 16.1-54',
    'F3': 'AISC 360-22 §F3, ecs. F3-1 y F3-2, pág. 16.1-55',
    'F6': 'AISC 360-22 §F6, ecs. F6-1 a F6-3, pág. 16.1-61 y 16.1-62',
    'F10': 'AISC 360-22 §F10 (ángulos sencillos), ecs. F10-1 a F10-4, pág. 16.1-68 y 16.1-69',
    'F10.3': 'AISC 360-22 §F10.3 (pandeo local de pata), ecs. F10-6 a F10-8, pág. 16.1-69 y 16.1-70',
    'G2': 'AISC 360-22 §G2.1 y §G2.2, ecs. G2-1 a G2-4, pág. 16.1-75 y 16.1-76',
    'G3': 'AISC 360-22 §G3 (ángulo sencillo), ec. G3-1, pág. 16.1-80',
    'G4': 'AISC 360-22 §G4 (HSS rectangulares y cajón), ec. G4-1 con Cv2 de §G2.2 (G2-9 a G2-11, kv = 5), pág. 16.1-80 y 16.1-77',
    'G6': 'AISC 360-22 §G6 (cortante en eje menor), pág. 16.1-81',
    'H1': 'AISC 360-22 §H1.1, ecs. H1-1a y H1-1b, pág. 16.1-82 y 16.1-83',
    'H2': 'AISC 360-22 §H2 (secciones no cubiertas por H1), ec. H2-1, pág. 16.1-84',
    'H3': 'AISC 360-22 §H3.1 (ecs. H3-1 a H3-5) y §H3.2 (ec. H3-6), pág. 16.1-85 a 16.1-87',
    'F7': 'AISC 360-22 §F7 (HSS cuadradas y rectangulares), ecs. F7-1 a F7-11, pág. 16.1-63 a 16.1-65',
    'B4_1A': 'AISC 360-22 Tabla B4.1a (esbeltez local de elementos comprimidos), con E7 para anchos efectivos',
    'B4_1B': 'AISC 360-22 Tabla B4.1b (esbeltez local de elementos en flexión)',
    'PROY_KLR': 'IMCA 5ta ed., cap. E, pág. II-89 (pdf 185): nota "preferiblemente KL/r ≤ 200", verificada en imagen; aplicada como límite del proyecto',
    'L2_FLECHA': 'AISC 360-22 Comentario L2, pág. 16.1-543. L/360 es el criterio adoptado para este proyecto (pisos); no es un límite universal para soportes industriales (R04-22)',
    'BASE_J8': 'AISC DG1 2.ª ed., pág. 14 (pdf 21), verificada en imagen: J8 con Ω_c = 2.50 y φ_c = 0.60 (AISC 2005)',
    'BASE_DG1_PL': 'AISC Design Guide 1, 2.ª ed., §3.1.2 (m, n, n′, λn′ y espesor; base AISC 2005). φ = 0.90 y Ω = 1.67',
    'BASE_DG1_T': 'AISC Design Guide 1, 2.ª ed., pág. 19 (pdf 26): R_n = 0.7 F_u (verificada en imagen) y Ω = 2.00; área A_t según §3.2.1',
    'BASE_CONO': 'ACI 318-02, Apéndice D, §D.5.2, ec. D-7 φ = 0.70: AISC DG1 págs. 19 y 42 (verificada en imagen)',
    'BASE_DG1_V': 'AISC Design Guide 1, 2.ª ed., pág. 42 (pdf 49), ejemplo 4.10: φ(0.4)F_u A_b con roscas, φ = 0.75. Verificada en imagen',
    'BASE_CONV': 'Conversión de factores LRFD a ASD: Ω = 1.5/φ. Reproduce Ω_c = 2.50 (DG1, φ = 0.60), Ω = 2.00 (φ = 0.75) y Ω = 1.67 (φ = 0.90)',
    'BASE_SOLD': 'AISC Design Guide 1, 2.ª ed., pág. 42 (pdf 49): electrodo E70, φ(0.6)F_EXX, φ = 0.75. Verificada en imagen',
}


def _ref_html(k):
    """Linea de referencia (apartado y pagina) bajo el nombre de una verificacion."""
    return f'<br><span class="nota">{REF[k]}</span>'


def _refs_verif(nombre, familia):
    """Referencias de AISC para cada verificacion de la tabla (I y canal, o angulo LI)."""
    li = familia == 'LI'
    mapa = {
        'Tracción': ['D2', 'D3'] if li else ['D2'],
        'Compresión': ['E3', 'E5', 'E7'] if li else ['E3', 'E4', 'E7'],
        'Flexión eje mayor': ['F10', 'F10.3'] if li else ['F2', 'F3'],
        'Flexión eje menor': ['F10', 'F10.3'] if li else ['F6'],
        'Cortante eje mayor': ['G3'] if li else ['G2'],
        'Cortante eje menor': ['G3'] if li else ['G6'],
        'Interacción': ['H2'] if li else ['H1'],
    }
    if familia == 'HSS':
        mapa = {'Tracción': ['D2'], 'Compresión': ['E3', 'E7'], 'Flexión eje mayor': ['F7'], 'Flexión eje menor': ['F7'],
                'Cortante eje mayor': ['G4'], 'Cortante eje menor': ['G4'], 'Torsión': ['H3'], 'Interacción': ['H1', 'H3']}
    return ''.join(_ref_html(k) for k in mapa.get(nombre, []))


def _ref_local(v):
    """Referencia AISC de la esbeltez local: Tabla B4.1a para miembros comprimidos (no VIGA); Tabla B4.1b para flexion."""
    comprimido = DA.CHEQUEO_EG in (v.get('ev') or {}).get('const', {}) and v.get('grupo') != 'VIGA'
    return _ref_html('B4_1A' if comprimido else 'B4_1B')


def _nota_normativa():
    """Nota de la memoria: diseno AISC 360-22 ASD. No se aplica la NTC-Acero ni la NTC de sismo (criterio del revisor)."""
    filas = [
        ('Esbeltez global en compresión (IMCA cap. E)', REF['PROY_KLR'], 'KL/r ≤ 200',
         'COLUMNA, ARRIOSTRE y DIAGONAL con compresión en alguna combinación (la VIGA, elemento a flexión, no se verifica por KL/r)'),
        ('Esbeltez local en compresión: patín', REF['B4_1A'],
         'b/t ≤ 0.56·√(E/Fy) (I y canal); ala de ángulo b/t ≤ 0.45·√(E/Fy)', 'COLUMNA, ARRIOSTRE y DIAGONAL con compresión (la VIGA se revisa a flexión)'),
        ('Esbeltez local en compresión: alma', REF['B4_1A'], 'h/t ≤ 1.49·√(E/Fy)',
         'COLUMNA, ARRIOSTRE y DIAGONAL con compresión (la VIGA se revisa a flexión)'),
        ('Esbeltez local en flexión: patín', REF['B4_1B'],
         'b/t ≤ 1.00·√(E/Fy) (λr); 0.38·√(E/Fy) (λp)', 'VIGA'),
        ('Esbeltez local en flexión: alma', REF['B4_1B'],
         'h/t ≤ 5.70·√(E/Fy) (λr); 3.76·√(E/Fy) (λp)', 'VIGA'),
        ('Esbeltez local en flexión: ala de ángulo', REF['B4_1B'],
         'b/t ≤ 0.91·√(E/Fy) (λr); 0.54·√(E/Fy) (λp)', 'VIGA (LI)'),
        ('Clasificación de la sección en flexión', REF['B4_1B'],
         'compacta si λ ≤ λp; no compacta si λ ≤ λr; esbelta si λ > λr', 'VIGA'),
    ]
    cuerpo = ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in filas)
    return ('<h2>Nota normativa: diseño AISC 360-22 (ASD)</h2>'
            '<p>El diseño de resistencia (tracción, compresión, flexión, cortante e interacción) y la esbeltez local se hacen '
            'con AISC 360-22 (ASD). No se aplica la NTC-Acero CDMX ni la NTC de diseño por sismo (criterio del revisor). '
            'El límite KL/r ≤ 200 proviene del capítulo E del IMCA 5ta ed. (pág. II-89, nota verificada en imagen); el proyecto lo aplica como límite. '
            'Cada límite indica el apartado y la página del documento.</p>'
            '<table><tr><th>Verificación</th><th>Referencia (documento, apartado y página)</th><th>Límite</th>'
            '<th>Aplica a</th></tr>' + cuerpo + '</table>'
            '<ul class="nota">'
            '<li>Elementos esbeltos en compresión: anchos efectivos de AISC E7.</li>'
            '<li>λ = b/t en patines y alas (b = B/2 en patines de I; b = B en canales); h/t en almas, con h = H − 2t.</li>'
            '</ul>')




def _cumple_html(ok):
    return f'<span class="{"cumple" if ok else "nocumple"}">{"CUMPLE" if ok else "NO CUMPLE"}</span>'


def _seccion_desplazamientos(dib, casos, id_de_indice, id_barra, clase, proyecto):
    """Seccion 6: desplazamientos por combinacion y deformada de la que controla (6.1); flecha vertical de vigas con
    el limite L/divisor de AISC 360-22 Comentario L2 (6.2). Valores de la hoja PARAMETROS y NORMA."""
    cf = proyecto['conf']
    tabla, mejor = _desplazamientos(dib, casos, id_de_indice)
    if tabla.empty:
        return '<p>Sin combinaciones de servicio: no hay desplazamientos que reportar.</p>'
    filas = ''.join(
        f'<tr><td>{html.escape(str(r.combinacion))}</td><td class="num">{_v(r.ux, 2)}</td>'
        f'<td class="num">{_v(r.uy, 2)}</td><td class="num">{_v(r.uz, 2)}</td>'
        f'<td class="num">{_v(r.resultante, 2)}</td><td class="num">{r.nodo}</td></tr>'
        for r in tabla.itertuples())
    fila_max, res_ctrl = mejor
    png, escala = _png_deformada(dib, res_ctrl, f'Deformada: combinación que controla {fila_max["combinacion"]}')

    # DECISION (cerrada por el revisor): el limite de flecha es el de AISC Comentario L2 (L/360 para pisos).
    divisor = cf['flecha_divisor']
    filas_f = []
    for i, r in sorted((getattr(dib, 'flechas', {}) or {}).items()):
        lim = r['L_cm'] * 10.0 / divisor
        filas_f.append(
            f'<tr><td class="num">{id_barra.get(i, i)}</td><td>{html.escape(str(dib.barras[i]["perfil"]))}</td>'
            f'<td class="num">{_v(r["L_cm"], 1)}</td><td class="num">{_v(r["max_mm"], 2)}</td>'
            f'<td>{html.escape(str(r["comb"]))}</td><td class="num">{r["xi"]:.2f}</td>'
            f'<td class="num">{_v(lim, 2)}</td><td>{_cumple_html(r["max_mm"] <= lim)}</td></tr>')
    if filas_f:
        tabla_f = ('<table><tr><th>Barra</th><th>Perfil</th><th>L (cm)</th><th>Flecha máx (mm)</th>'
                   '<th>Combinación que controla</th><th>Posición x/L</th>'
                   f'<th>Límite L/{divisor:g} (mm)</th><th>Estado</th></tr>' + ''.join(filas_f) + '</table>')
    else:
        tabla_f = '<p class="nota">No hay vigas horizontales en el modelo para revisar la flecha.</p>'

    return (f'<h3>6.1 Máximos por combinación</h3>'
            f'<table><tr><th>Combinación</th><th>|UX| máx (mm)</th><th>|UY| máx (mm)</th><th>|UZ| máx (mm)</th>'
            f'<th>Desplazamiento resultante máx (mm)</th><th>Nodo</th></tr>{filas}</table>'
            f'<p><b>Desplazamiento máximo</b>: {_v(fila_max["resultante"], 2)} mm en el nodo {fila_max["nodo"]}, '
            f'combinación <b>{html.escape(str(fila_max["combinacion"]))}</b> (controla).</p>'
            f'<img src="data:image/png;base64,{png}" alt="Deformada" style="max-width:100%">'
            f'<p class="nota">Deformada de la combinación que controla, escala ×{escala:.3g} (el máximo mide 10 % '
            f'de la dimensión del modelo). Gris: sin carga; azul: deformada.</p>'
            f'<h3>6.2 Flecha vertical de vigas</h3>'
            f'<p><b>Límite L/{divisor:g}</b>. Justificación: AISC 360-22, Comentario L2 (pág. 16.1-543): la flecha de '
            f'alrededor de 1/300 del claro es visible y puede causar daño arquitectónico; el comentario indica que los límites '
            f'dependen de la estructura (1/360 para pisos y 1/240 para cubiertas son los usuales).</p>'
            f'<p>La flecha es la desviación vertical máxima de la viga respecto a la cuerda entre sus extremos, en las '
            f'combinaciones gravitacionales (D y L), sin el movimiento de cuerpo rígido de los apoyos. Se calcula con la '
            f'solución exacta de Euler-Bernoulli entre extremos, a partir de los giros de extremo del modelo y del peso '
            f'propio; no incluye la deformación por cortante.</p>'
            f'{tabla_f}')


# ---------------------------------------------------------------- 6.3 Derivas de entrepiso bajo sismo
def _sin_dato(v):
    return v is None or str(v).strip() == ''


def _numero_opcional(v, etiqueta):
    """Dato numerico de la hoja DESPLAZAMIENTOS. Vacio = None (pendiente); texto que no es numero = error de la planilla."""
    if _sin_dato(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        raise DA.ErrorAsd(f'DESPLAZAMIENTOS: {etiqueta} debe ser un número (leído: {v}). Corríjalo y vuelva a ejecutar.')


def _estado_limite(valor, limite):
    """CUMPLE / NO CUMPLE frente a un limite. Sin limite informado = PENDIENTE (nunca OK)."""
    if limite is None:
        return 'PENDIENTE'
    return 'CUMPLE' if valor <= limite else 'NO CUMPLE'


def _estado_html(estado):
    clase = {'CUMPLE': 'cumple', 'NO CUMPLE': 'nocumple'}.get(estado, 'pend')
    return f'<span class="{clase}">{estado}</span>'


def _nivel_nodos(z_mm, ux_mm, uy_mm, tol_mm=1.0):
    """Agrupa los nudos por cota Z (tolerancia tol_mm). Por nivel: cota y maximo |UX| y |UY| de sus nudos (mm),
    de menor a mayor cota."""
    niveles = []
    for k in np.argsort(z_mm, kind='stable'):
        if niveles and z_mm[k] - niveles[-1]['z_hi'] <= tol_mm:
            g = niveles[-1]
            g['z_hi'] = float(z_mm[k])
            g['ux'] = max(g['ux'], abs(float(ux_mm[k])))
            g['uy'] = max(g['uy'], abs(float(uy_mm[k])))
        else:
            niveles.append({'z': float(z_mm[k]), 'z_hi': float(z_mm[k]),
                            'ux': abs(float(ux_mm[k])), 'uy': abs(float(uy_mm[k]))})
    return niveles


def _derivas_niveles(niveles, limite):
    """Entrepisos: Δ_i = δ_i − δ_(i−1) y deriva = |Δ_i| / h_i en X e Y. Cada fila es el entrepiso entre un nivel y el
    inmediato inferior; el estado se da con la mayor de las dos derivas."""
    filas = []
    for abajo, arriba in zip(niveles, niveles[1:]):
        h = arriba['z'] - abajo['z']
        dx = abs(arriba['ux'] - abajo['ux'])
        dy = abs(arriba['uy'] - abajo['uy'])
        deriva = max(dx, dy) / h
        filas.append({'z': arriba['z'], 'h': h, 'ux': arriba['ux'], 'uy': arriba['uy'],
                      'deriva_x': dx / h, 'deriva_y': dy / h, 'deriva': deriva,
                      'estado': _estado_limite(deriva, limite)})
    return filas


def _seccion_desplazamientos_sismicos(dib, casos, desp):
    """6.3 Derivas de entrepiso de la estructura bajo sismo: desplazamientos del analisis en las combinaciones de sismo,
    agrupados por nivel (cota Z) y comparados con el limite de deriva de la hoja DESPLAZAMIENTOS."""
    titulo = '<h3>6.3 Derivas de entrepiso bajo sismo</h3>'
    if desp is None:
        return titulo + ('<p class="nota">La planilla no tiene la hoja DESPLAZAMIENTOS: copie esa hoja desde la plantilla '
                         'nueva para ingresar el límite de deriva.</p>')
    limite = _numero_opcional(desp.get('limite'), 'LIMITE_DERIVA')
    convencion = '' if _sin_dato(desp.get('convencion')) else html.escape(str(desp['convencion']).strip())
    if limite is None:
        lim_txt = 'no informado: el resultado queda <span class="pend">PENDIENTE</span>'
    else:
        lim_txt = f'δ_lim / h = {limite:g} ({limite * 100:.2f} %)'
    intro = ('<p>Desplazamientos laterales de los nudos en las combinaciones de sismo (estado E). Los nudos se agrupan '
             'por cota Z en niveles; δ de cada nivel = máximo |UX| y |UY| de sus nudos. Entrepiso: Δ = δ<sub>i</sub> − '
             'δ<sub>i−1</sub>; deriva = |Δ| / h. Convención de desplazamientos del modelo: '
             f'<b>{convencion or "sin informar"}</b>.</p>'
             f'<p><b>Límite de deriva de entrepiso</b>: {lim_txt}.</p>')

    cls = getattr(dib, 'clase_combinacion', {}) or {}
    sismo = [(n, res) for n, tipo, res in casos if tipo == 'COMBINACION' and cls.get(n) == 'sismo']
    z_mm = np.array([dib.nodos[i][2] for i in range(len(dib.nodos))], float) * 1000.0
    bloques, peor = [], None
    for nombre, res in sismo:
        d = np.array([res['nodos'][i][:3] for i in range(len(dib.nodos))], float) * 10.0     # cm -> mm
        filas = _derivas_niveles(_nivel_nodos(z_mm, d[:, 0], d[:, 1]), limite)
        if not filas:
            continue
        for f in filas:
            if peor is None or f['deriva'] > peor[1]['deriva']:
                peor = (nombre, f)
        cuerpo = ''.join(
            f'<tr><td class="num">{_v(f["z"], 1)}</td><td class="num">{_v(f["h"], 1)}</td>'
            f'<td class="num">{_v(f["ux"], 2)}</td><td class="num">{_v(f["uy"], 2)}</td>'
            f'<td class="num">{f["deriva_x"]:.5f}</td><td class="num">{f["deriva_y"]:.5f}</td>'
            f'<td class="num">{f["deriva"]:.5f}</td><td>{_estado_html(f["estado"])}</td></tr>'
            for f in filas)
        bloques.append(f'<h4>Combinación {html.escape(str(nombre))}</h4>'
                       '<table><tr><th>Cota Z del nivel (mm)</th><th>h entrepiso (mm)</th><th>δX (mm)</th>'
                       '<th>δY (mm)</th><th>Deriva X</th><th>Deriva Y</th><th>Deriva máx</th><th>Estado</th></tr>'
                       f'{cuerpo}</table>')
    if bloques:
        derivas = ''.join(bloques)
        nombre, f = peor
        derivas += (f'<p><b>Deriva máxima</b>: {f["deriva"]:.5f} ({f["deriva"] * 100:.3f} %) en el entrepiso de cota '
                    f'Z = {_v(f["z"], 1)} mm, combinación {html.escape(str(nombre))}. Estado: {_estado_html(f["estado"])}.</p>')
    elif sismo:
        derivas = '<p class="nota">El modelo tiene un solo nivel: no hay entrepisos que revisar.</p>'
    else:
        derivas = '<p class="nota">No hay combinaciones de sismo (estado E) en la planilla: no hay derivas que revisar.</p>'
    return titulo + intro + '<h4>Derivas de entrepiso por combinación de sismo</h4>' + derivas


# ---------------------------------------------------------------- 6.4 Periodo natural del soporte
def _seccion_periodo(periodo):
    """6.4 Periodo natural del soporte: autovalores del modelo lineal con la masa de peso propio (barras y cargas en
    nudos de los estados con PESO PROPIO = SI). Lo calcula el bloque 9c del notebook; aqui solo se reporta."""
    titulo = '<h3>6.4 Periodo natural del soporte</h3>'
    if periodo is None:
        return titulo + '<p class="nota">No se calculó el periodo natural (bloque 9c del notebook).</p>'
    tabla, peso_barras, peso_nudos = periodo['tabla'], periodo['barras'], periodo['nudos']
    peso = peso_barras + peso_nudos
    t1 = tabla.iloc[0]
    eje_t1 = max([('X', t1['Masa efectiva X (%)']), ('Y', t1['Masa efectiva Y (%)']),
                  ('Z', t1['Masa efectiva Z (%)'])], key=lambda p: p[1])
    filas = ''.join(
        f'<tr><td class="num">{int(r["Modo"])}</td><td class="num">{r["T (s)"]:.4f}</td>'
        f'<td class="num">{r["f (Hz)"]:.4f}</td><td class="num">{r["Masa efectiva X (%)"]:.2f}</td>'
        f'<td class="num">{r["Masa efectiva Y (%)"]:.2f}</td><td class="num">{r["Masa efectiva Z (%)"]:.2f}</td></tr>'
        for _, r in tabla.iterrows())
    suma = {eje: tabla[f'Masa efectiva {eje} (%)'].sum() for eje in ('X', 'Y', 'Z')}
    return (titulo
            + '<p><b>Método</b>: problema de autovalores del modelo lineal, K φ = ω² M φ, con K la rigidez de la '
              'estructura y M la masa de peso propio. Periodo T = 2π / ω.</p>'
            + '<p><b>Masa</b> (estados con PESO PROPIO = SI):</p><ul>'
              f'<li>Barras: masa del catálogo por perfil (kg/m) × longitud, la mitad de cada barra a cada extremo: '
              f'{_v(peso_barras, 1)} kgf.</li>'
              f'<li>Cargas de peso en nudos (hoja CARGAS, FZ negativa): {_v(peso_nudos, 1)} kgf.</li>'
              f'<li>Peso total {_v(peso, 1)} kgf. Masa M = peso / g, con g = 981 cm/s². Masa solo de traslación en '
              'cada nudo; los giros no tienen masa.</li></ul>'
            + f'<p><b>Periodo fundamental</b>: T1 = {t1["T (s)"]:.4f} s, f1 = {t1["f (Hz)"]:.4f} Hz. El modo 1 es '
              f'predominante en la dirección {eje_t1[0]} ({eje_t1[1]:.2f} % de la masa).</p>'
            + '<table><tr><th>Modo</th><th>T (s)</th><th>f (Hz)</th><th>Masa efectiva X (%)</th>'
              '<th>Masa efectiva Y (%)</th><th>Masa efectiva Z (%)</th></tr>' + filas + '</table>'
            + '<p class="nota">Masa efectiva: porcentaje de la masa total que se mueve en cada modo y dirección. '
              f'Suma de los {len(tabla)} modos calculados: X {suma["X"]:.2f} %, Y {suma["Y"]:.2f} %, '
              f'Z {suma["Z"]:.2f} %.</p>')


def _encabezado_doc(proyecto, dib):
    meta = [('Proyecto', proyecto.get('nombre', '(completar)')),
            ('Elemento / estructura', proyecto.get('elemento', '(completar)')),
            ('Planilla de datos', proyecto.get('archivo', 'planilla_con_diseno.xlsx')),
            ('Fecha', proyecto.get('fecha', '')),
            ('Versión', proyecto.get('version', '(completar)')),
            ('Modelo', f'{len(dib.nodos)} nodos y {len(dib.barras)} barras'),
            ('Método', 'Diseño ASD, ANSI/AISC 360-22: resistencia y esbeltez local (B4.1). KL/r ≤ 200 según IMCA cap. E.'),
            ('Unidades', 'fuerzas kgf; momentos kgf·cm; longitudes cm; esfuerzos kgf/cm²')]
    filas = ''.join(f'<tr><td><b>{a}</b></td><td>{html.escape(str(b))}</td></tr>' for a, b in meta)
    revision = [('Elaboró', 'elaboro'), ('Revisó', 'reviso'), ('Aprobó', 'aprobo')]
    rev = ''.join(f'<tr><td>{etq}</td><td>{html.escape(str(proyecto.get(clave, "")))}</td><td></td><td></td></tr>'
                  for etq, clave in revision)
    return (f'<table class="meta">{filas}</table>'
            f'<table><tr><th>Cuadro de revisión</th><th>Nombre</th><th>Firma</th><th>Fecha</th></tr>{rev}</table>')


def _criterios_html():
    items = [
        'Diseño de resistencia: AISC 360-22 (ASD). Factores Ω: tracción 1.67 (fluencia) y 2.00 (fractura) (D2); '
        'compresión y flexión 1.67 (E1, F1); cortante 1.67, o 1.50 en I laminada (G1, G2.1).',
        'Demandas: combinaciones de servicio de COMBINACIONES (ASD), sin factores adicionales. Análisis lineal de '
        'primer orden: no incluye efectos P-Δ. Cada barra se revisa con todas sus combinaciones.',
        'Una sola sección por grupo (COLUMNA, VIGA, ARRIOSTRE, DIAGONAL): todas las barras de un grupo usan el mismo '
        'perfil. Cada barra se revisa con sus propias demandas.',
        'Criterio de aceptación: FU ≤ 1.0 en todas las verificaciones; λ ≤ λr (AISC B4.1); KL/r ≤ 200 (IMCA cap. E, '
        'aplicado como límite del proyecto) solo en miembros comprimidos. Las vigas (elementos a flexión) no se '
        'verifican con KL/r (decisión del proyecto).',
        'Elementos esbeltos en compresión: anchos efectivos de AISC E7. Elementos con λ &gt; λr en flexión quedan fuera '
        'de la lista de perfiles.',
        'Perfiles macizos (CS, OS, SOL) eliminados de la base; LM no se incluye.',
        'Fu: de la hoja MATERIALES de la planilla.',
        f'Ángulos (LI): E5 solo si LONGITUDES marca las cuatro condiciones ({REF["E5"]}). Si no, K·L/rz y H2 '
        f'({REF["H2"]}). Tracción con Ae = U·Ag, U de D3 ({REF["D3"]}): una pata U = 1 − x̄/l; dos patas U = 1.0.',
        'Espesor de diseño de HSS (AISC 360-22 B4.2): t = 0.93·t nominal para HSS salvo ASTM A1065/A1085. Las '
        'propiedades de diseño se obtienen del catálogo por la razón de espesores; el análisis (OpenSees) usa el mismo espesor de diseño.',
        'Estimaciones: IR con Zx, Zy o Cw faltantes se estiman por geometría; LI con propiedades geométricas. Cada '
        'barra lista sus supuestos.',
        f'Interacción: H1-1 para I y canal ({REF["H1"]}); H2-1 para ángulos ({REF["H2"]}), con el momento resultante '
        'sobre cada eje principal (criterio conservador).',
    ]
    return '<ul>' + ''.join(f'<li>{t}</li>' for t in items) + '</ul>'


def _orden_calculo_html():
    """Orden del calculo por barra (seccion 1). Los mismos seis pasos aparecen en el detalle de la seccion 7."""
    pasos = [
        ('Datos y propiedades', 'material, longitudes y sección de la base. En HSS, espesor de diseño '
         't = 0.93·t nominal (AISC 360-22 B4.2) y propiedades de diseño (ver sección 2).'),
        ('Demandas', 'Pr, Mr, Vr y torsión de cada combinación de servicio ASD (hoja COMBINACIONES). Cada '
         'verificación toma la combinación que la controla.'),
        ('Esbeltez', 'clasificación de elementos (AISC B4.1: tabla B4.1a en compresión y B4.1b en flexión) y '
         'KL/r ≤ 200 para miembros comprimidos (IMCA cap. E). Las vigas no se verifican con KL/r.'),
        ('Resistencias', 'tracción (D), compresión (E, con ancho efectivo de E7), flexión (F), cortante (G) y '
         'torsión (H3).'),
        ('Interacción', 'H1 para I, canal y HSS; H2 para ángulos; H3 cuando la torsión es significativa '
         '(Tr > 0.2·Tc).'),
        ('Resultado', 'FU máximo = máx(FU de esfuerzos; FU de esbeltez). La barra cumple si FU ≤ 1.0 en todos los pasos.'),
    ]
    items = ''.join(f'<li><b>Paso {i}. {nombre}</b>: {texto}</li>' for i, (nombre, texto) in enumerate(pasos, 1))
    return f'<h3>Orden del cálculo por barra</h3><ol>{items}</ol>'


def _parametros_html(cf):
    """3.1 Parametros de diseno y de norma usados por el calculo, con su referencia (hojas PARAMETROS y NORMA)."""
    filas_p = ''.join(
        f'<tr><td>{html.escape(str(c))}</td><td>{html.escape(str(k))}</td><td class="num">{html.escape(str(v))}</td>'
        f'<td>{html.escape(str(u))}</td><td>{html.escape(str(r))}</td></tr>'
        for (c, k, v, u, r) in cf.get('par_filas', []))
    filas_n = ''.join(
        f'<tr><td>{html.escape(str(k))}</td><td class="num">{v:g}</td><td>{html.escape(str(u))}</td>'
        f'<td>{html.escape(str(r))}</td></tr>'
        for (k, v, u, r) in cf.get('nor_filas', []))
    resultantes = (
        '<table><tr><th>Valor resultante</th><th>Valor</th><th>Cómo se obtiene</th></tr>'
        f'<tr><td>Límite de flecha de vigas</td><td class="num">L/{cf["flecha_divisor"]:g}</td><td>AISC 360-22, Comentario L2 (pisos: L/360)</td></tr>'
        f'<tr><td>Límite KL/r en compresión</td><td class="num">{cf["klr_limite"]:g}</td><td>IMCA 5ta ed., cap. E, pág. II-89 (aplicado como límite)</td></tr>'
        f'<tr><td>Kz (pandeo torsional)</td><td class="num">{cf["kz"]:g}</td><td>AISC 360-22, E4: elegido en PARAMETROS</td></tr>'
        f'<tr><td>Viento en el diseño</td><td>{html.escape(cf["viento"])}</td><td>Esta versión no considera viento</td></tr>'
        '</table>')
    return ('<h3>3.1 Parámetros de diseño y de norma</h3>'
            '<p>Valores que usa el cálculo. Los elige usted en la hoja PARAMETROS del Excel (listas desplegables e '
            'ingresos); los valores de norma están en la hoja NORMA, con su referencia. El código no trae valores de norma '
            'ni supuestos.</p>'
            '<h4>Elecciones e ingresos (PARAMETROS)</h4>'
            '<table><tr><th>Concepto</th><th>Clave</th><th>Valor elegido</th><th>Unidad</th><th>Referencia</th></tr>'
            + filas_p + '</table>'
            '<h4>Valores de norma (NORMA)</h4>'
            '<table><tr><th>Clave</th><th>Valor</th><th>Unidad</th><th>Referencia</th></tr>' + filas_n + '</table>'
            '<h4>Valores resultantes</h4>' + resultantes)


def _datos_entrada_html(dib, materiales_filas, id_barra, lon, mat, equilibrio):
    filas_mat = []
    for f in materiales_filas:
        fu = f[3] if len(f) > 3 else None
        fu_txt = 'sin Fu en MATERIALES' if fu is None or (isinstance(fu, float) and math.isnan(fu)) \
            else f'{_v(fu, 0)} kgf/cm²'
        filas_mat.append(f'<tr><td>{html.escape(str(f[0]))}</td><td class="num">{_v(f[2], 0)} kgf/cm²</td>'
                         f'<td class="num">{fu_txt}</td><td class="num">{_v(f[4], 0)} kgf/cm²</td>'
                         f'<td class="num">{_v(f[5], 2)}</td></tr>')
    materiales = ('<table><tr><th>Material</th><th>Fy</th><th>Fu</th><th>E</th><th>ν</th></tr>'
                  + ''.join(filas_mat) + '</table>')
    filas_g = []
    for g in DA.GRUPOS_ELEMENTO:
        idx = [i for i, b in enumerate(dib.barras) if b['elemento'] == g]
        if not idx:
            continue
        ents = [DA._entrada_barra(dib, i, id_barra, lon, mat) for i in idx]
        perfiles = sorted({dib.barras[i]['perfil'] for i in idx})
        mats = sorted({str(dib.barras[i].get('material') or '') for i in idx})
        filas_g.append(
            f'<tr><td>{g}</td><td>{len(idx)}</td><td>{html.escape(", ".join(perfiles))}</td>'
            f'<td>{html.escape(", ".join(mats))}</td>'
            f'<td class="num">{_v(max(e["lx"] for e in ents) * 100, 1)}</td>'
            f'<td class="num">{_v(max(e["ly"] for e in ents) * 100, 1)}</td>'
            f'<td class="num">{_v(max(e["lb"] for e in ents) * 100, 1)}</td>'
            f'<td class="num">{_v(max(e["kx"] for e in ents), 2)} / {_v(max(e["ky"] for e in ents), 2)}</td>'
            f'<td class="num">{_v(max(e["cb"] for e in ents), 2)}</td></tr>')
    grupos = ('<table><tr><th>Grupo</th><th>Barras</th><th>Perfil (una sección)</th><th>Material</th>'
              '<th>LX máx (cm)</th><th>LY máx (cm)</th><th>LB máx (cm)</th><th>KX / KY</th><th>Cb</th>'
              '</tr>' + ''.join(filas_g) + '</table>')
    combs = getattr(dib, 'combinaciones', {}) or {}
    cls = getattr(dib, 'clase_combinacion', {}) or {}
    filas_c = ''.join(
        f'<tr><td>{html.escape(str(n))}</td><td>' + ' + '.join(f'{fac:g}·{html.escape(str(e))}'
                                                               for e, fac in fac_d.items()) + '</td></tr>'
        for n, fac_d in combs.items() if cls.get(n) != 'viento')
    combinaciones = ('<table><tr><th>Combinación</th><th>Factores sobre los estados de carga</th></tr>'
                     + (filas_c or '<tr><td colspan="2">Sin definición de combinaciones en la planilla.</td></tr>')
                     + '</table>')
    en_diseno = [str(n) for n in combs if cls.get(n) != 'viento']
    combinaciones += ('<p class="nota"><b>Combinaciones del diseño</b>: ' + (', '.join(en_diseno) or 'ninguna')
                      + '. El viento no se considera en esta versión.</p>')
    estados = ', '.join(html.escape(str(n)) for n, _ in (equilibrio or []))
    return (f'<h3>Materiales</h3>{materiales}'
            f'<h3>Perfil y longitudes por grupo</h3>{grupos}'
            f'<h3>Combinaciones de servicio (ASD)</h3>{combinaciones}'
            f'<h3>Estados de carga</h3><p>{estados or "—"}</p>')


def _modelo_html(dib, equilibrio):
    filas = ''.join(f'<tr><td>{html.escape(str(n))}</td><td class="num">{r:.3g}</td>'
                    f'<td>≈ 0 (equilibrio)</td></tr>' for n, r in (equilibrio or []))
    tabla = ('<table><tr><th>Estado de carga</th><th>Residuo de fuerzas (kgf)</th><th>Criterio</th></tr>'
             + (filas or '<tr><td colspan="3">Sin datos de equilibrio.</td></tr>') + '</table>')
    return (f'<p>El modelo tiene {len(dib.nodos)} nodos y {len(dib.barras)} barras. Se resuelve con OpenSees '
            f'(openseespy) como marco 3D de elementos elásticos lineales (elasticBeamColumn). Cada estado de carga se '
            f'resuelve por separado y las combinaciones de servicio se obtienen por superposición lineal de los '
            f'estados. El peso propio de la sección se aplica cuando ESTADOS lo indica (masa Gerdau). Apoyos y rótulas '
            f'según NODOS y CONEXIONES. Es un análisis de primer orden: no incluye efectos de segundo orden.</p>'
            f'<h3>Verificación de equilibrio</h3>{tabla}'
            f'<p class="nota">El residuo de equilibrio por estado debe ser prácticamente cero; si no lo es, revise la '
            f'planilla antes de usar el diseño.</p>')


def _simbologia_html():
    filas = [('Fy, Fu', 'Esfuerzo de fluencia y de ruptura del acero (kgf/cm²)'),
             ('Ag, Ae, An', 'Área total, efectiva y neta (cm²)'),
             ('U', 'Factor de rezago por cortante diferido (AISC D3)'),
             ('Ωt, Ωc, Ωb, Ωv', 'Factores de seguridad ASD: tracción, compresión, flexión y cortante'),
             ('KL/r', 'Relación de esbeltez (K: factor de longitud efectiva; L: longitud; r: radio de giro)'),
             ('Fe, Fn', 'Esfuerzo de pandeo elástico y nominal (AISC E3)'),
             ('Mp, My, Mn, Mcr', 'Momento plástico, de fluencia, nominal y de pandeo lateral-torsional'),
             ('Zx, Zy, Sx, Sy', 'Módulos plástico y elástico de la sección'),
             ('Cb', 'Factor de gradiente de momento (AISC F1)'),
             ('λ, λr, λp, λpl', 'Relación ancho/grueso del elemento y sus límites (AISC Tablas B4.1a y B4.1b)'),
             ('Pr, Mr, Vr', 'Demandas ASD: carga axial, momento y cortante de la combinación'),
             ('FU', 'Factor de utilización: demanda / capacidad (cumple si FU ≤ 1.0)')]
    cuerpo = ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in filas)
    return f'<table><tr><th>Símbolo</th><th>Significado</th></tr>{cuerpo}</table>'


def _vp(x, dec=2):
    """Valor de la memoria de placas base: '—' si falta; 'fuera de la placa' si el valor es infinito."""
    if x is None:
        return '—'
    if isinstance(x, float) and not math.isfinite(x):
        return 'fuera de la placa'
    return _v(x, dec)


def _kg(x, unidad, dec=1):
    """Resultado con unidad para la memoria de placas base."""
    if x is None:
        return '—'
    if isinstance(x, float) and not math.isfinite(x):
        return 'fuera de la placa'
    return f'{_v(x, dec)} {unidad}'


_MPA_POR_KGCM2 = 0.0980665


def _pasos_base(v, r):
    """Pasos ordenados de una verificacion de placa base para el caso que la controla.
    Devuelve [(paso, ecuacion, calculo sustituido, resultado)]. El FU se agrega aparte."""
    c, k, d = v['combo'], r['ctx'], r['datos']
    N, B, n, ct = d['pl_n'], d['pl_b'], d['n'], d['c_t']
    Pc, Pt = c.get('Pc', 0.0), c.get('Pt', 0.0)
    mx, my = c.get('mx', 0.0), c.get('my', 0.0)
    fx, fy, V = c.get('fx', 0.0), c.get('fy', 0.0), c.get('V', 0.0)
    ex, ey = c.get('ex', 0.0), c.get('ey', 0.0)
    cl = v['clave']
    out = []
    if cl == 'ap':
        if Pc <= 0:
            return [('Sin compresión', 'F_Z ≤ 0: no hay apoyo sobre el dado en esta combinación', '—', 'no aplica')]
        out.append(('Área de la placa', 'A1 = N · B', f'{N:g} · {B:g}', _kg(k['A1'], 'cm²', 0)))
        out.append(('Área de apoyo del dado', 'A2 = N_d · B_d', f'{d["dado_n"]:g} · {d["dado_b"]:g}',
                    _kg(k['A2'], 'cm²', 0)))
        out.append(('Resistencia nominal de aplastamiento',
                    'P_p = mín[0.85 · f′c · A1 · √(A2/A1) ; 1.7 · f′c · A1]   (IMCA J8-1 y J8-2)',
                    f'mín[0.85 · {d["fc"]:g} · {k["A1"]:.0f} · √({k["A2"] / k["A1"]:.3f}) ; 1.7 · {d["fc"]:g} · {k["A1"]:.0f}]',
                    _kg(k['Pp'], 'kgf', 0)))
        out.append(('Resistencia admisible de aplastamiento', f'f_adm = P_p / (Ω_c · A1),  Ω_c = {k["Oc"]:g}',
                    f'{k["Pp"]:.0f} / ({k["Oc"]:g} · {k["A1"]:.0f})', _kg(k['f_adm'], 'kgf/cm²', 1)))
        out.append(('Carga y excentricidades de la combinación', 'P = F_Z ;  e_x = |M_y| / P ;  e_y = |M_x| / P',
                    f'P = {Pc:.0f} kgf ;  e_x = {ex:.2f} cm ;  e_y = {ey:.2f} cm', f'{Pc:.0f} kgf'))
        for eje, L, e, W, dd in [('X', N, ex, B, c['dx']), ('Y', B, ey, N, c['dy'])]:
            minus = eje.lower()
            if not dd['grande']:
                if e <= L / 6.0:
                    out.append((f'Dirección {eje}: compresión lineal (e ≤ L/6)',
                                f'f_{minus} = P / (N · B) · (1 + 6 · e_{minus} / {"N" if eje == "X" else "B"})',
                                f'{Pc:.0f} / ({N:g} · {B:g}) · (1 + 6 · {e:.2f} / {L:g})', _kg(dd['f'], 'kgf/cm²', 1)))
                else:
                    out.append((f'Dirección {eje}: compresión triangular (L/6 < e ≤ e_crit)',
                                f'Y = 3 · (L/2 − e_{minus}) ;  f_{minus} = 2P / (W · Y)',
                                f'Y = 3 · ({L / 2:.2f} − {e:.2f}) = {3 * (L / 2 - e):.2f} cm ;  '
                                f'f = 2 · {Pc:.0f} / ({W:g} · {3 * (L / 2 - e):.2f})', _kg(dd['f'], 'kgf/cm²', 1)))
            else:
                q = dd['q']
                out.append((f'Dirección {eje}: e_crit (momento grande)',
                            'e_crit = L/2 − P / (2 · q) ;  q = f_adm · W',
                            f'{L / 2:.2f} − {Pc:.0f} / (2 · {q:.0f}) ;  e = {e:.2f} cm',
                            f'e_crit = {dd["ecrit"]:.2f} cm: e > e_crit, pernos en tracción'))
                if dd['ok']:
                    out.append((f'Dirección {eje}: bloque de compresión Y',
                                'f_b = L/2 − c ;  x_T = L/2 + f_b ;  Y = x_T − √(x_T² − 2 · P · (e + f_b) / q)',
                                f'f_b = {dd["f_b"]:.2f} cm ;  x_T = {dd["xT"]:.2f} cm ;  q = {q:.0f} kgf/cm',
                                f'Y = {dd["Y"]:.3f} cm'))
                    out.append((f'Dirección {eje}: tracción total de la fila de pernos', 'T = q · Y − P',
                                f'{q:.0f} · {dd["Y"]:.3f} − {Pc:.0f}', _kg(dd['Ta'], 'kgf', 1)))
                else:
                    out.append((f'Dirección {eje}: sin solución', 'x_T² − 2 · P · (e + f_b) / q < 0 o Y > L',
                                '—', 'aumentar la placa'))
        out.append(('Utilización de aplastamiento',
                    'FU_ap = máx(f / f_adm) en compresión; con momento grande la presión de diseño es f_adm (equilibrio)',
                    f'máx(f_X ; f_Y) / f_adm = {c["fu"]["ap"]:.3f}' if math.isfinite(c['fu']['ap']) else 'sin solución',
                    f'{c["fu"]["ap"]:.3f}' if math.isfinite(c['fu']['ap']) else 'inf'))
        return out
    if cl == 'pl':
        if 'treq' not in c:
            return [('Sin compresión', 'F_Z ≤ 0: sin compresión; no hay flexión de aplastamiento', '—', 'no aplica')]
        if not math.isfinite(c['treq']):
            return [('Presión inexistente', 'la resultante queda fuera de la placa: no hay presión que transmitir',
                     '—', 'fuera de la placa')]
        Wx, Wy, X, lam = k['Wx'], k['Wy'], c['X'], c['lam']
        out.append(('Voladizo m (dirección N)', 'm = (N − 0.95 · W_x) / 2', f'({N:g} − 0.95 · {Wx:.2f}) / 2',
                    _kg(c['m'], 'cm', 2)))
        out.append(('Voladizo n (dirección B)', 'n = (B − 0.8 · W_y) / 2', f'({B:g} − 0.8 · {Wy:.2f}) / 2',
                    _kg(c['n'], 'cm', 2)))
        out.append(('Voladizo n′', 'n′ = √(W_x · W_y) / 4', f'√({Wx:.2f} · {Wy:.2f}) / 4', _kg(c['np'], 'cm', 2)))
        out.append(('Parámetro X', 'X = 4 · W_x · W_y / (W_x + W_y)² · Ω_c · P / P_p',
                    f'4 · {Wx:.2f} · {Wy:.2f} / ({Wx:.2f} + {Wy:.2f})² · {k["Oc"]:g} · {Pc:.0f} / {k["Pp"]:.0f}',
                    f'{X:.4f}'))
        out.append(('Factor λ', 'λ = 2√X / (1 + √(1 − X))   (λ = 1 si X ≥ 1)',
                    f'2 · √{X:.4f} / (1 + √(1 − {X:.4f}))', f'{lam:.4f}'))
        out.append(('Voladizo crítico', 'l = máx(m ; n ; λ · n′)',
                    f'máx({c["m"]:.2f} ; {c["n"]:.2f} ; {lam:.4f} · {c["np"]:.2f})', _kg(c['l'], 'cm', 2)))
        f_peq = [dd['f'] for dd in (c['dx'], c['dy']) if not dd['grande']]
        if f_peq:
            fmax_peq = max(f_peq)
            out.append(('Espesor, caso de momento pequeño', f't = l · √(2 · Ω_pl · f / F_y),  Ω_pl = {k["Opl"]:.2f}',
                        f'{c["l"]:.2f} · √(2 · {k["Opl"]:.2f} · {fmax_peq:.2f} / {d["fy"]:g})',
                        _kg(c['l'] * math.sqrt(2 * k['Opl'] * fmax_peq / d['fy']), 'cm', 3)))
        for eje, dd in (('X', c['dx']), ('Y', c['dy'])):
            if not (dd['grande'] and dd.get('ok')):
                continue
            cant = c['l']
            W = B if eje == 'X' else N
            out.append((f'Espesor por compresión, dirección {eje} (momento grande)',
                        f't_comp = 2.58 · √(f_adm · Y · (l − Y/2) / F_y),  l = máx(m ; n ; λ · n′)  (DG1)',
                        f'2.58 · √({k["f_adm"]:.1f} · {dd["Y"]:.3f} · ({cant:.2f} − {dd["Y"] / 2:.3f}) / {d["fy"]:g})',
                        _kg(dd['t_comp'], 'cm', 3)))
            out.append((f'Espesor por tracción del voladizo del perno, dirección {eje}',
                        f't_anc = 2.58 · √(T · x / (W · F_y)),  x = f_b − mín(W_x ; W_y)/2',
                        f'2.58 · √({dd["Ta"]:.0f} · {dd["x"]:.2f} / ({W:g} · {d["fy"]:g}))', _kg(dd['t_anc'], 'cm', 3)))
        out.append(('Espesor requerido: máximo de todos los casos', 't_req = máx(casos de espesor)',
                    'máx(casos anteriores) de la combinación', _kg(c['treq'], 'cm', 3)))
        return out
    if cl in ('T', 'cono'):
        if 'Ta' not in c:
            return [('Sin equilibrio', 'la presión admisible no se alcanza dentro de la placa (Y > N)', '—',
                     'fuera de la placa')]
    if cl == 'T':
        Tside = c['Tside']
        grandes_t = [(eje, dd) for eje, dd in (('X', c['dx']), ('Y', c['dy'])) if dd['grande'] and dd.get('ok')]
        if grandes_t:
            for eje, dd in grandes_t:
                out.append((f'Equilibrio con pernos en tracción (dirección {eje})',
                            'C = q · Y ;  C · (x_T − Y/2) = P · (e + f_b)  →  Y ;  T = C − P',
                            f'q = {dd["q"]:.0f} kgf/cm ;  x_T = {dd["xT"]:.2f} cm ;  Y = {dd["Y"]:.3f} cm',
                            f'T = {dd["Ta"]:.0f} kgf'))
            out.append(('Tracción total del lado de pernos', 'T = máx(T_X ; T_Y)',
                        f'máx({c["dx"].get("Ta") or 0:.0f} ; {c["dy"].get("Ta") or 0:.0f}) kgf', _kg(Tside, 'kgf', 1)))
        elif Pt > 0:
            out.append(('Tracción total del lado de pernos (levantamiento)', 'T = P_t / 2 + |M_y| / (N − 2 · c_anclas)',
                        f'{Pt:.0f} / 2 + {abs(my):.0f} / ({N:g} − 2 · {ct:g})', _kg(Tside, 'kgf', 1)))
        else:
            out.append(('Tracción en pernos', 'sin tracción: compresión dentro del núcleo, T = 0', '—', _kg(0.0, 'kgf', 1)))
        nx_, ny_ = int(d['nx']), int(d['ny'])
        out.append(('Disposición de pernos (dato de entrada)',
                    'n = N_x · N_y ;  N_x = pernos por fila en X ;  N_y = pernos por fila en Y',
                    f'{nx_} · {ny_} = {nx_ * ny_}', f'n = {n:g}'))
        out.append(('Tracción por perno, fila en X', 'T_p,X = T_X / N_y',
                    f'{c.get("Ta_x") or 0:.1f} / {ny_}', _kg(c.get('Tp_x') or 0.0, 'kgf', 1)))
        out.append(('Tracción por perno, fila en Y', 'T_p,Y = T_Y / N_x',
                    f'{c.get("Ta_y") or 0:.1f} / {nx_}', _kg(c.get('Tp_y') or 0.0, 'kgf', 1)))
        out.append(('Área de tensión de la rosca', 'A_t = π/4 · (D − 0.9743 / n_h)² · 6.4516   (ASME B1.1)',
                    f'π/4 · ({d["diam"]:g} − 0.9743 / {d["hilos"]:g})² · 6.4516', _kg(k['At'], 'cm²', 3)))
        out.append(('Área bruta del perno', 'A_b = π/4 · D² · 6.4516',
                    f'π/4 · {d["diam"]:g}² · 6.4516', _kg(k['Ab'], 'cm²', 3)))
        out.append(('Corte por perno', 'V_p = V / n ;  f_rv = V_p / A_b',
                    f'{V:.1f} / {n:g} = {c.get("Va", 0.0):.2f} kgf ;  f_rv = {c.get("Va", 0.0):.2f} / {k["Ab"]:.3f}',
                    _kg(c.get('fv') or 0.0, 'kgf/cm²', 2)))
        Fnt_nom = k['Fnt'] * d['fu']
        Fnv_nom = k['Fv'] * d['fu']
        out.append(('Tensión admisible con corte (AISC 360-22 J3-3b, ASD)',
                    f"F′nt / Ω = mín[1.3 · F_nt / Ω − (F_nt / F_nv) · f_rv ; F_nt / Ω],  F_nt = {k['Fnt']:g} · F_u,  F_nv = {k['Fv']:g} · F_u,  Ω = {k['OT']:.2f}",
                    f'mín[1.3 · {Fnt_nom:.0f} / {k["OT"]:.2f} − {Fnt_nom:.0f} / {Fnv_nom:.0f} · {c.get("fv") or 0:.2f} ; {Fnt_nom:.0f} / {k["OT"]:.2f}]',
                    _kg(c.get('Fnt_p') or 0.0, 'kgf/cm²', 1)))
        out.append(('Resistencia admisible a tracción con corte', 'T_all = (F′nt / Ω) · A_t',
                    f'{c.get("Fnt_p") or 0.0:.1f} · {k["At"]:.3f}', _kg(c.get('T_all') or 0.0, 'kgf', 0)))
        out.append(('Utilización a tracción', 'FU_T = T_p / T_all  (máximo de las dos filas)',
                    f'{c.get("Ta") or 0.0:.1f} / {c.get("T_all") or 0.0:.0f}', f'{c["fu"]["T"]:.3f}'))
        return out
    if cl == 'cono':
        out.append(('Resistencia nominal del cono de concreto',
                    'N_b = k · λ · √f′c · h_ef^1.5   (ACI 318-02 Ap. D, ec. D-7, SI)',
                    f'{k["Kc"]:g} · {k["Lam"]:g} · √({d["fc"] * _MPA_POR_KGCM2:.2f} MPa) · ({d["hef"] * 10:g} mm)^1.5 / 9.81',
                    _kg(k['Nb'], 'kgf', 0)))
        out.append(('Resistencia admisible del cono', f'φ · N_b / 1.5 = N_b / Ω_cono,  φ = 0.70,  Ω_cono = {k["Ocono"]:.2f}',
                    f'{k["Nb"]:,.0f} / {k["Ocono"]:.2f}', _kg(k['allow_cono'], 'kgf', 0)))
        out.append(('Tracción del grupo de pernos de un lado', 'T (lado de pernos, de la verificación de tracción)',
                    f'{c["Tside"]:.1f} kgf', _kg(c['Tside'], 'kgf', 1)))
        return out
    if cl == 'V':
        out.append(('Cortante total en la base', 'V = √(F_X² + F_Y²)', f'√({fx:.1f}² + {fy:.1f}²)', _kg(V, 'kgf', 1)))
        out.append(('Cortante por perno', f'V_a = V / n,  n = {n:g}', f'{V:.1f} / {n:g}', _kg(c['Va'], 'kgf', 1)))
        out.append(('Resistencia nominal a cortante (roscas incluidas)', f'R_n = F_v · F_u · A_b,  F_v = {k["Fv"]:g}  (DG1 pág. 42)',
                    f'{k["Fv"]:g} · {d["fu"]:g} · {k["Ab"]:.3f}', _kg(k['Fv'] * d['fu'] * k['Ab'], 'kgf', 0)))
        out.append(('Resistencia admisible a cortante', f'R_n / Ω_V,  Ω_V = {k["OV"]:.2f}',
                    f'{k["Fv"] * d["fu"] * k["Ab"]:,.0f} / {k["OV"]:.2f}', _kg(k['allow_V'], 'kgf', 0)))
        return out
    if cl == 'w':
        Wx, Wy = k['Wx'], k['Wy']
        out.append(('Tracción transferida a la soldadura', 'T_w = P_t + máx(|M_x| / W_y ; |M_y| / W_x)   (conservador)',
                    f'{Pt:.0f} + máx({abs(mx):.0f} / {Wy:.2f} ; {abs(my):.0f} / {Wx:.2f})', _kg(c['Tw'], 'kgf', 1)))
        out.append(('Resultante en la soldadura', 'R_w = √(T_w² + V²)', f'√({c["Tw"]:.1f}² + {V:.1f}²)',
                    _kg(c['Rw'], 'kgf', 1)))
        out.append(('Fuerza por longitud de soldadura', 'R_w / L', f'{c["Rw"]:.1f} / {d["sold_l"]:g}',
                    _kg(c['Rw_L'], 'kgf/cm', 2)))
        out.append(('Resistencia admisible por longitud',
                    f'0.6 · F_EXX · 0.707 · w / Ω_s,  F_EXX = {k["fexx"]:,.0f} kgf/cm²,  Ω_s = {k["Osol"]:.2f}  (DG1 pág. 42)',
                    f'0.6 · {k["fexx"]:,.0f} · 0.707 · {d["sold_w"]:g} / {k["Osol"]:.2f}', _kg(k['allow_w'], 'kgf/cm', 1)))
        return out
    return out


_REF_FACTOR = {'BASE_J8_085': 'BASE_J8', 'BASE_J8_LIM': 'BASE_J8', 'BASE_OMEGA_C': 'BASE_J8',
               'BASE_FACTOR_ASD': 'BASE_CONV', 'BASE_PHI_PL': 'BASE_DG1_PL', 'BASE_PHI_ANCLA_T': 'BASE_DG1_T',
               'BASE_FNT': 'BASE_DG1_T', 'BASE_PHI_ANCLA_V': 'BASE_DG1_V', 'BASE_FV': 'BASE_DG1_V',
               'BASE_PHI_CONO': 'BASE_CONO', 'BASE_KC_CONO': 'BASE_CONO', 'BASE_LAMBDA': 'BASE_CONO',
               'BASE_PHI_SOLD': 'BASE_SOLD', 'BASE_SOLD_FRAC': 'BASE_SOLD', 'BASE_FEXX_KSI': 'BASE_SOLD'}
_REF_CORTA = {'BASE_J8': 'DG1 2.ª ed., pág. 14 (pdf 21)', 'BASE_CONV': 'Conversión LRFD a ASD',
              'BASE_DG1_PL': 'DG1 §3.1.2', 'BASE_DG1_T': 'DG1 pág. 19 (pdf 26); §3.2.1',
              'BASE_DG1_V': 'DG1 pág. 42 (pdf 49)', 'BASE_CONO': 'ACI 318-02 Ap. D (D-7); DG1 págs. 19 y 42',
              'BASE_SOLD': 'DG1 pág. 42 (pdf 49)'}
_USO_FACTOR = {'BASE_J8_085': 'P_p = 0.85 f′c A1 √(A2/A1)', 'BASE_J8_LIM': 'límite P_p ≤ 1.7 f′c A1',
               'BASE_OMEGA_C': 'Ω_c del aplastamiento', 'BASE_FACTOR_ASD': 'Ω = 1.5/φ (conversión a ASD)',
               'BASE_PHI_PL': 'Ω_pl = 1.5/φ (flexión de la placa)', 'BASE_PHI_ANCLA_T': 'Ω_T = 1.5/φ (tracción)',
               'BASE_FNT': 'R_n = F_nt · F_u · A_t', 'BASE_PHI_ANCLA_V': 'Ω_V = 1.5/φ (cortante)',
               'BASE_FV': 'R_n = F_v · F_u · A_b', 'BASE_PHI_CONO': 'Ω_cono = 1.5/φ (cono)',
               'BASE_KC_CONO': 'k del cono (SI)', 'BASE_LAMBDA': 'λ del concreto',
               'BASE_PHI_SOLD': 'Ω_s = 1.5/φ (soldadura)', 'BASE_SOLD_FRAC': 'F_w = 0.6 · F_EXX',
               'BASE_FEXX_KSI': 'F_EXX del electrodo (ksi)'}


def _factores_placa_html(resultados):
    """Tabla de factores de NORMA usados en placas base, con su referencia."""
    nrm = next((r['ctx']['nrm'] for r in resultados if r.get('ctx')), None)
    if nrm is None:
        return ''
    filas = ''.join(f'<tr><td>{clave}</td><td class="num">{nrm[clave]:g}</td><td>{_USO_FACTOR[clave]}</td>'
                    f'<td>{_REF_CORTA[_REF_FACTOR[clave]]}</td></tr>'
                    for clave in _REF_FACTOR if clave in nrm)
    return ('<h4>8.0 Factores de placas base usados (hoja NORMA)</h4>'
            '<table><tr><th>Clave NORMA</th><th>Valor</th><th>Uso</th><th>Referencia</th></tr>'
            + filas + '</table>')


def _datos_placa_html(r):
    """8.i.1 Datos de entrada y propiedades calculadas, con su fuente."""
    d, k = r['datos'], r['ctx']
    filas = [
        ('Perfil de la columna (base Gerdau)', f'{r["perfil"]}  ·  H = {k["p"]["H"]:g} cm ; B = {k["p"]["B"]:g} cm',
         '—', 'Base Gerdau'),
        ('Dirección del peralte (EJE_FUERTE)', f'({k["eje"][0]:.3f} ; {k["eje"][1]:.3f} ; {k["eje"][2]:.3f})', '—', 'hoja BARRAS'),
        ('Envolvente en planta W_x ; W_y', f'{k["Wx"]:.2f} ; {k["Wy"]:.2f}', 'cm',
         'W_x = H·|u_x| + B·|u_y| ;  W_y = H·|u_y| + B·|u_x|  (u = peralte en planta)'),
        ('Resistencia del concreto f′c', _v(d['fc'], 0), 'kgf/cm²', 'hoja BASES'),
        ('Dado N_d × B_d  →  A2', f'{d["dado_n"]:g} × {d["dado_b"]:g}  →  {_v(k["A2"], 0)}', 'cm ; cm²', 'hoja BASES'),
        ('Placa N × B × t  →  A1', f'{d["pl_n"]:g} × {d["pl_b"]:g} × {d["pl_t"]:g}  →  {_v(k["A1"], 0)}', 'cm ; cm²', 'hoja BASES'),
        ('Fluencia de la placa F_y', _v(d['fy'], 0), 'kgf/cm²', 'hoja BASES'),
        ('Pernos: Nx ; Ny ; n total ; distancia c_anclas', f'{d["nx"]:g} ; {d["ny"]:g} ; {d["n"]:g} ; {d["c_t"]:g}', '— ; cm', 'hoja BASES'),
        ('Pernos: diámetro D ; hilos por pulgada n_h', f'{d["diam"]:g} pulg ({d["diam"] * 25.4:.1f} mm) ; {d["hilos"]:g}',
         '—', 'hoja BASES'),
        ('Pernos: F_u', _v(d['fu'], 0), 'kgf/cm²', 'hoja BASES'),
        ('Pernos: longitud de embebido h_ef', _v(d['hef'], 1), 'cm', 'hoja BASES'),
        ('Soldadura: tamaño w ; longitud L', f'{d["sold_w"]:g} ; {d["sold_l"]:g}', 'cm', 'hoja BASES'),
        ('Presión admisible de aplastamiento f_adm', _v(k['f_adm'], 1), 'kgf/cm²', 'calculado (8.i.4)'),
    ]
    cuerpo = ''.join(f'<tr><td>{html.escape(a)}</td><td class="num">{html.escape(str(b))}</td>'
                     f'<td>{html.escape(u)}</td><td>{html.escape(f)}</td></tr>' for a, b, u, f in filas)
    return ('<h4>8.{i}.1 Datos de entrada y propiedades</h4>'
            '<table><tr><th>Concepto</th><th>Valor</th><th>Unidad</th><th>Fuente / ecuación</th></tr>'
            + cuerpo + '</table>')


def _combos_placa_html(r):
    """8.i.2 Combinaciones de servicio y FU de cada verificacion, por combinacion."""
    cab = ('<tr><th>Combinación</th><th>F_Z (kgf)</th><th>P_t (kgf)</th><th>M_x (kgf·cm)</th><th>M_y (kgf·cm)</th>'
           '<th>V (kgf)</th><th>FU aplast.</th><th>FU espesor</th><th>FU tracción</th><th>FU cono</th>'
           '<th>FU cortante</th><th>FU soldadura</th></tr>')
    filas = []
    for c in r['combos']:
        celdas = [f'<td>{html.escape(c["caso"])}</td>', f'<td class="num">{_v(c["fz"], 1)}</td>',
                  f'<td class="num">{_v(c["Pt"], 1)}</td>', f'<td class="num">{_v(c["mx"], 0)}</td>',
                  f'<td class="num">{_v(c["my"], 0)}</td>', f'<td class="num">{_v(c["V"], 1)}</td>']
        celdas += [f'<td class="num">{_fu(c["fu"].get(cl, 0.0))}</td>' for cl in ['ap', 'pl', 'T', 'cono', 'V', 'w']]
        filas.append('<tr>' + ''.join(celdas) + '</tr>')
    return ('<h4>8.{i}.2 Combinaciones de servicio ASD (REACCIONES) y FU por verificación</h4>'
            '<p class="nota">FU = demanda / capacidad; cumple si FU ≤ 1.0. El FU que controla cada verificación es el máximo de la columna.</p>'
            '<table>' + cab + ''.join(filas) + '</table>')


def _resumen_placa_html(r):
    """8.i.3 Resumen: verificacion que controla, caso, demanda, capacidad y FU."""
    filas = []
    for v in r['verif']:
        cc, k, d = v['combo'], r['ctx'], r['datos']
        dem = {'ap': cc.get('f'), 'pl': cc.get('treq'), 'T': cc.get('Ta'), 'cono': cc.get('Tside'),
               'V': cc.get('Va'), 'w': cc.get('Rw_L')}[v['clave']]
        cap = {'ap': k['f_adm'], 'pl': d['pl_t'], 'T': k['allow_T'], 'cono': k['allow_cono'],
               'V': k['allow_V'], 'w': k['allow_w']}[v['clave']]
        unidad = {'ap': 'kgf/cm²', 'pl': 'cm', 'T': 'kgf por perno', 'cono': 'kgf (grupo de un lado)',
                  'V': 'kgf por perno', 'w': 'kgf/cm'}[v['clave']]
        estado = 'CUMPLE' if v['fu'] <= 1.0 else 'NO CUMPLE'
        clase = 'cumple' if estado == 'CUMPLE' else 'nocumple'
        filas.append(f'<tr><td>{html.escape(v["nombre"])}</td><td>{html.escape(v["caso"])}</td>'
                     f'<td class="num">{_vp(dem, 2)} {unidad}</td><td class="num">{_vp(cap, 2)} {unidad}</td>'
                     f'<td class="num">{_fu(v["fu"])}</td><td class="{clase}">{estado}</td></tr>')
    alt = ''
    combos_s = [c for c in r['combos'] if c.get('treq_s') is not None]
    if combos_s:
        cs = max(combos_s, key=lambda c: c['treq_s'])
        t_s = cs['treq_s']
        fu_s = cs['fu'].get('pl_s', math.inf)
        t_0 = max((c.get('treq') or 0.0) for c in r['combos'])
        pl_t = r['datos']['pl_t']
        alt = ('<h4>8.{i}.3b Alternativa con un atiezador a mitad del voladizo (aproximación)</h4>'
               '<table><tr><th>Concepto</th><th>Sin atiezador</th><th>Con atiezador</th></tr>'
               f'<tr><td>Voladizo que gobierna l (cm)</td><td class="num">{_vp(cs["l"], 2)}</td>'
               f'<td class="num">{_vp(cs["l_s"], 2)}</td></tr>'
               f'<tr><td>Espesor requerido (cm)</td><td class="num">{_vp(t_0, 3)}</td>'
               f'<td class="num">{_vp(t_s, 3)}</td></tr>'
               f'<tr><td>Espesor de la placa (cm)</td><td class="num">{_vp(pl_t, 2)}</td>'
               f'<td class="num">{_vp(pl_t, 2)}</td></tr>'
               f'<tr><td>FU de espesor</td><td class="num">{_fu((t_0 / pl_t) ** 2)}</td>'
               f'<td class="num">{_fu(fu_s)}</td></tr></table>'
               '<p class="nota">Aproximación: el voladizo que gobierna se toma a la mitad (atiezador a media distancia '
               'entre el patín y el borde). Caso que controla: ' + html.escape(cs['caso']) + '.</p>')
    return ('<h4>8.{i}.3 Resumen de verificaciones</h4>'
            '<table><tr><th>Verificación</th><th>Caso que controla</th><th>Demanda</th><th>Capacidad</th>'
            '<th>FU</th><th>Estado</th></tr>' + ''.join(filas) + '</table>' + alt)


def _detalle_placa_html(r):
    """8.i.4 Detalle paso a paso de cada verificacion (caso que la controla), con su referencia."""
    bloques = []
    for j, v in enumerate(r['verif'], 1):
        pasos = _pasos_base(v, r)
        filas = ''.join(f'<tr><td>{html.escape(p)}</td><td class="ec">{html.escape(e)}</td>'
                        f'<td class="ec">{html.escape(c)}</td><td class="num">{html.escape(res)}</td></tr>'
                        for p, e, c, res in pasos)
        filas += (f'<tr><td><b>FU</b></td><td class="ec">FU = demanda / capacidad (cumple si ≤ 1.0)</td>'
                  f'<td class="ec">caso: {html.escape(v["caso"])}</td><td class="num">{_fu(v["fu"])}</td></tr>')
        bloques.append(f'<h4>8.{{i}}.4.{j} {html.escape(v["nombre"])}{_ref_html(v["ref"])}</h4>'
                       '<table><tr><th>Paso</th><th>Ecuación</th><th>Cálculo sustituido</th><th>Resultado</th></tr>'
                       + filas + '</table>')
    return ''.join(bloques)


def _figura_placa(r):
    """Esquemas del nodo: planta (pernos Nx x Ny, zona de compresion Y, voladizos) y secciones X e Y, para la
    combinacion que gobierna el FU del nodo. Cotas en cm; fuerzas en kgf. Devuelve un bloque <figure> con PNG."""
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.patches import Rectangle, Polygon
    d = r['datos']
    N, B = float(d['pl_n']), float(d['pl_b'])
    N1, B1 = float(d['dado_n']), float(d['dado_b'])
    c = float(d['c_t'])
    nx, ny = int(d['nx']), int(d['ny'])
    Wx, Wy = float(r['ctx']['Wx']), float(r['ctx']['Wy'])
    fp = float(r['ctx']['f_adm'])
    comb = max(r['combos'], key=lambda q: max(q['fu'].values()) if q['fu'] else 0.0)
    P = float(comb.get('Pc', 0.0))
    ex, ey = float(comb.get('ex', 0.0)), float(comb.get('ey', 0.0))
    dx, dy = comb.get('dx', {}), comb.get('dy', {})
    fig = Figure(figsize=(11.0, 4.9), dpi=110)
    FigureCanvasAgg(fig)
    ax0, ax1, ax2 = fig.add_subplot(1, 3, 1), fig.add_subplot(1, 3, 2), fig.add_subplot(1, 3, 3)
    # Planta
    ax = ax0
    ax.add_patch(Rectangle((0, 0), N, B, fill=False, lw=1.6, ec='#1f4e79'))
    ax.add_patch(Rectangle((N / 2 - N1 / 2, B / 2 - B1 / 2), N1, B1, fill=False, ls='--', ec='#7f7f7f', lw=1.0))
    ax.add_patch(Rectangle((N / 2 - Wx / 2, B / 2 - Wy / 2), Wx, Wy, fc='#d9d9d9', ec='k', lw=0.8))
    xs = np.linspace(c, N - c, nx) if nx > 1 else [N / 2]
    ys = np.linspace(c, B - c, ny) if ny > 1 else [B / 2]
    for xb in xs:
        for yb in ys:
            ax.plot(xb, yb, 'o', color='#c00000', ms=5)
    if dx.get('grande') and dx.get('ok') and dx.get('Y'):
        ax.add_patch(Rectangle((0, 0), dx['Y'], B, fill=False, hatch='///', ec='#2e7d32', lw=0.6))
        ax.plot([N - c, N - c], [0, B], ls=':', color='#c00000', lw=0.8)
    if dy.get('grande') and dy.get('ok') and dy.get('Y'):
        ax.add_patch(Rectangle((0, 0), N, dy['Y'], fill=False, hatch='xxx', ec='#2e7d32', lw=0.6))
        ax.plot([0, N], [B - c, B - c], ls=':', color='#c00000', lw=0.8)
    xP, yP = N / 2 - ex, B / 2 - ey
    xPd = min(max(xP, -0.08 * N), 1.08 * N)
    yPd = min(max(yP, -0.08 * B), 1.08 * B)
    if P > 0:
        ax.plot(xPd, yPd, 'x', color='#000', ms=9, mew=2)
        txt = f'P = {P:.0f}' + (f'\nx_P = {xP:.1f} (fuera de la placa)' if (xP < 0 or xP > N) else '')
        ax.annotate(txt, (xPd, yPd), xytext=(-62, 14), textcoords='offset points', fontsize=7,
                    arrowprops=dict(arrowstyle='-', lw=0.5))
    ax.annotate('', xy=(N, -0.06 * B), xytext=(N - c, -0.06 * B), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.text(N - c / 2, -0.12 * B, f'c = {c:g}', ha='center', fontsize=7)
    ax.annotate('', xy=(0, B + 0.06 * B), xytext=(N, B + 0.06 * B), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.text(N / 2, B + 0.1 * B, f'N = {N:g}', ha='center', fontsize=7)
    ax.set_xlim(-0.2 * N, 1.2 * N)
    ax.set_ylim(-0.2 * B, 1.25 * B)
    ax.set_aspect('equal')
    ax.set_title(f'Planta: Nx = {nx}, Ny = {ny} pernos (zona Y: rayado)', fontsize=8)
    ax.axis('off')

    def seccion(ax, L, Wd, info, e, Pc, Lo, titulo, tiene):
        """Seccion a lo largo de L (N o B): placa, columna, bloque de compresion o distribucion, perno en traccion."""
        tdr = 0.04 * L
        xT, xPp = L - c, L / 2 - e
        ax.add_patch(Rectangle((-0.15 * L, -0.10 * L), 1.30 * L, 0.10 * L, fc='#eeeeee', ec='#999999'))
        ax.add_patch(Rectangle((0, 0), L, tdr, fc='#bdd7ee', ec='#1f4e79'))
        ax.add_patch(Rectangle((L / 2 - Wd / 2, tdr), Wd, 0.30 * L, fc='#d9d9d9', ec='k', lw=0.6))
        if info.get('grande') and info.get('ok'):
            ax.plot([xT, xT], [-0.10 * L, 0.0], color='#c00000', lw=2)
            Y = info['Y']
            ax.add_patch(Rectangle((0, -0.05 * L), Y, 0.05 * L, fc='#c6efce', ec='#2e7d32'))
            ax.annotate(f'T = {info["Ta"]:.0f}', xy=(xT, tdr), xytext=(xT, 0.14 * L), ha='center', fontsize=7,
                        color='#c00000', arrowprops=dict(arrowstyle='-|>', color='#c00000', lw=1.2))
            resumen = (f'Y = {Y:.3f} cm ;  C = qY = {info["q"] * Y:.0f} kgf (q = {info["q"]:.0f} kgf/cm)\n'
                       f'T = {info["Ta"]:.0f} kgf ;  x_T = {xT:.2f} cm ;  x_P = {xPp:.2f} cm')
        else:
            f0 = float(info.get('f', 0.0))
            h0 = 0.05 * L * (f0 / fp) if fp > 0 else 0.0
            if e <= L / 6.0:
                h1 = h0 * (1 - 6 * e / L) / (1 + 6 * e / L) if (1 + 6 * e / L) > 0 else 0.0
                ax.add_patch(Polygon([(0, 0), (0, -h0), (L, -h1), (L, 0)], closed=True, fc='#c6efce', ec='#2e7d32'))
            else:
                Y0 = min(3 * xPp, L) if xPp > 0 else L
                ax.add_patch(Polygon([(0, 0), (0, -h0), (Y0, 0)], closed=True, fc='#c6efce', ec='#2e7d32'))
            resumen = (f'compresión sin tracción: f = {f0:.1f} kgf/cm² (fpmax = {fp:.1f})\n'
                       f'e = {e:.2f} cm ;  x_P = {xPp:.2f} cm')
        if Pc > 0:
            xd = min(max(xPp, -0.1 * L), 1.1 * L)
            txt = f'P = {Pc:.0f}' + (' (fuera)' if (xPp < 0 or xPp > L) else '')
            ax.annotate(txt, xy=(xd, tdr), xytext=(xd, 0.45 * L), ha='center', fontsize=7,
                        arrowprops=dict(arrowstyle='-|>', lw=1.4))
        ax.annotate('', xy=(L, -0.03 * L), xytext=(xT, -0.03 * L), arrowprops=dict(arrowstyle='<->', lw=0.7))
        ax.text(L - c / 2, -0.03 * L + 0.02 * L, f'c = {c:g}', ha='center', fontsize=6)
        ax.set_xlim(-0.2 * L, 1.2 * L)
        ax.set_ylim(-0.25 * L, 0.6 * L)
        ax.set_aspect('equal')
        ax.set_title(titulo, fontsize=8)
        ax.text(-0.2 * L, -0.27 * L, resumen, fontsize=6.2, va='top')
        ax.axis('off')

    seccion(ax1, N, Wx, dx, ex, P, None, f'Seccion X (a lo largo de N = {N:g})', True)
    seccion(ax2, B, Wy, dy, ey, P, None, f'Seccion Y (a lo largo de B = {B:g})', True)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    etiq = f'{html.escape(str(comb.get("caso", "")))}'
    return (f'<figure class="esquema"><img alt="Esquemas placa base nodo {r["id"]}" '
            f'src="data:image/png;base64,{b64}" style="max-width:100%">'
            f'<figcaption class="nota">Esquemas del nodo {r["id"]}: planta y secciones X e Y. Combinación que '
            f'gobierna el FU: {etiq}. Cotas en cm; fuerzas en kgf. Rojo: pernos en tracción. Verde: bloque de compresión.</figcaption></figure>')


def _seccion_placas(resultados):
    """Seccion 8: placas base, ordenada por nodo. Por nodo: 8.i.1 datos, 8.i.2 combinaciones, 8.i.3 resumen,
    8.i.4 detalle paso a paso con referencia."""
    if resultados is None:
        return ('<p class="nota">No se ingresaron datos de placas base (hoja BASES vacía o la planilla no la tiene). '
                'Este apartado no contiene cálculos de placa base.</p>')
    if not resultados:
        return '<p class="nota">La hoja BASES no tiene filas con datos.</p>'
    bloques = [_factores_placa_html(resultados)]
    for i, r in enumerate(resultados, 1):
        estado = r['estado']
        if estado in ('CUMPLE', 'NO CUMPLE', 'NO REVISADO'):
            estado = 'CUMPLE' if (r['fu_max'] is not None and r['fu_max'] <= 1.0) else 'NO CUMPLE'
        clase = {'CUMPLE': 'cumple'}.get(estado, 'nocumple')
        perfil = html.escape(str(r['perfil'] or '—'))
        bloques.append(f'<h3>8.{i} Nodo {r["id"]} · perfil {perfil} · <span class="{clase}">{estado}</span></h3>')
        if estado not in ('CUMPLE', 'NO CUMPLE'):
            motivo = ', '.join(r['faltan'] + r['norma']) or '; '.join(r['notas'])
            bloques.append(f'<p class="nota">Datos del nodo incompletos o inválidos: {html.escape(motivo)}.</p>')
            continue
        bloques.append(_datos_placa_html(r).replace('{i}', str(i)))
        bloques.append(_figura_placa(r))
        bloques.append(_combos_placa_html(r).replace('{i}', str(i)))
        bloques.append(_resumen_placa_html(r).replace('{i}', str(i)))
        bloques.append(_detalle_placa_html(r).replace('{i}', str(i)))
    return ''.join(bloques)


def memoria_html(dib, materiales_filas, longitudes_df, demandas, id_barra, ruta_salida, proyecto=None,
                 casos=None, id_de_indice=None, equilibrio=None, bases=None, desplazamientos=None,
                 periodo=None):
    """Escribe la memoria de calculo completa (HTML imprimible) del diseno de todas las barras del modelo."""
    proyecto = dict(proyecto or {})
    if not proyecto.get('conf'):
        raise DA.ErrorAsd('falta la configuracion de PARAMETROS y NORMA: no se genera la memoria')
    DA.perfil_por_grupo(dib)                           # una sola seccion por grupo (error si no)
    mat, lon, comb = DA._preparar_entradas(materiales_filas, longitudes_df, demandas)
    evals = [_evaluar(dib, i, id_barra, lon, mat, comb) for i in range(len(dib.barras))]
    contar = {}
    for v in evals:
        contar[v['estado']] = contar.get(v['estado'], 0) + 1
    bloques_grupo = []
    for g in DA.GRUPOS_ELEMENTO:
        sub = [v for v in evals if v['grupo'] == g]
        if sub:
            df_g = pd.DataFrame([_fila_grupo(v) for v in sub], columns=COLS_GRUPO).fillna('—')
            bloques_grupo.append(f'<h3>{g}</h3>' + df_g.to_html(index=False, na_rep='—', border=0))
    resumen_html = ''.join(bloques_grupo)
    criticas = []
    for g in DA.GRUPOS_ELEMENTO:
        sub = [v for v in evals if v['grupo'] == g and v.get('fu_res')]
        if sub:
            criticas.append(max(sub, key=lambda v: v['fu_res']['FU MAXIMO']))
    desp_html = (_seccion_desplazamientos(dib, casos, id_de_indice, id_barra,
                                          getattr(dib, 'clase_combinacion', {}) or {}, proyecto)
                 if casos is not None else '<p>Sin resultados de desplazamientos.</p>')
    if casos is not None:
        desp_html += _seccion_desplazamientos_sismicos(dib, casos, desplazamientos)
    resumen_txt = ' · '.join(f'{k}: {n}' for k, n in sorted(contar.items()))
    cuerpo = f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Memoria de cálculo</title><style>{CSS}</style></head><body>
<h1>Memoria de cálculo: diseño de soportes de acero</h1>
{_encabezado_doc(proyecto, dib)}
{_nota_normativa()}
<h2>1. Cómo leer esta memoria</h2>
<p>Esta memoria documenta, para cada verificación, la referencia del documento (apartado y página), la ecuación, los
valores sustituidos, la capacidad admisible, la demanda de la combinación que controla y el FU. FU = demanda /
capacidad: cumple si FU ≤ 1.0. El resumen por grupo presenta el FU de interacción flexocompresión y las esbelteces;
el detalle completo de cada elemento está en diseno_asd.xlsx (RESULTADOS).</p>
{_orden_calculo_html()}
<h2>2. Criterios de diseño adoptados</h2>{_criterios_html()}
<h2>3. Datos de entrada</h2>{_parametros_html(proyecto['conf'])}{_datos_entrada_html(dib, materiales_filas, id_barra, lon, mat, equilibrio)}
<h2>4. Modelo de análisis</h2>{_modelo_html(dib, equilibrio)}
<h2>5. Resultados por grupo</h2>
<p class="nota">Por grupo: FU de esfuerzos (resistencia, incluida la interacción H1/H2 y la torsión H3) y FU de esbeltez (local y KL/r) por separado, con sus valores calculado y límite; la verificación que gobierna y el estado global (todas las verificaciones).</p>
{('<p>' + resumen_txt + '</p>') if resumen_txt else ''}
{resumen_html}
<h2>6. Desplazamientos máximos por combinación</h2>
{desp_html}
{_seccion_periodo(periodo)}
<h2>7. Detalle de barras críticas (FU máximo de cada grupo)</h2>
<p class="nota">Se detalla solo la barra que controla cada grupo, con los pasos 1 a 6 de la sección 1. Las demás barras de cada grupo están en la tabla por
grupo (sección 5) y en diseno_asd.xlsx (RESULTADOS).</p>
{"".join(_bloque_barra(v) for v in criticas)}
<h2>8. Placas base</h2>
<p class="nota">Placas base con las combinaciones de servicio ASD (REACCIONES). Aplastamiento: AISC DG1 2.ª ed. (Ω = 2.50). Interacción tracción–corte en pernos: AISC 360-22 J3-3b.
Espesor, pernos, cono de concreto y soldadura: AISC Design Guide 1, 2.ª ed., y ACI 318-02 Ap. D, en ASD (Ω = 1.5/φ).
Los datos (placa, dado, pernos, soldadura) son entradas de la hoja BASES.</p>
{_seccion_placas(bases)}
<h2>Anexo. Simbología</h2>{_simbologia_html()}
</body></html>'''
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(cuerpo)
    return ruta_salida
