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
table { border-collapse: collapse; width: 100%; margin: 4px 0 8px 0; font-size: 9pt; }
th, td { border: 1px solid #b9c7d6; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #DDEBF7; }
td.num { text-align: right; white-space: nowrap; }
.meta td { border: none; padding: 1px 6px 1px 0; }
.cumple { color: #1e6b33; font-weight: bold; }
.nocumple { color: #a61b1b; font-weight: bold; }
.nota { color: #555; font-size: 8.5pt; }
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
        out.update(estado='FUERA DE ALCANCE', motivo=f'familia {familia}: no se disena (solo IR, CE y LI)')
        return out
    e = DA._entrada_barra(dib, i, id_barra, lon, mat)
    m = e['m']
    out.update(L=e['L'], lx=e['lx'], ly=e['ly'], lb=e['lb'], kx=e['kx'], ky=e['ky'], cb=e['cb'],
               nivel=e['nivel'], e5=e['e5'], conexion=e['conexion'], l_li=e['l_li'])
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
                      e['lb'] * 100.0, e['kx'], e['ky'], b['elemento'], e['nivel'], dem, cb=e['cb'],
                      e5=e5_b, u_t=u_b)
    if ev['motivo'] and any(d['Pr_c'] > 0 for d in dem):
        out.update(estado='NO REVISADO', motivo='NO REVISADO: ' + ev['motivo'])
        return out
    out.update(ev=ev, res=ev['res'], klr=ev['klr'])
    if not dem:
        out.update(estado='SIN COMBINACIONES', fu_res=None)
        return out
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
    if any('estimado' in s for s in v.get('supuestos', [])):
        body += '<tr><td colspan="3" class="nota">Valores marcados como estimados en supuestos (geometría).</td></tr>'
    return f'<table><tr><th>Propiedad</th><th>Valor</th><th>Unidad</th></tr>{body}</table>'


def _verificaciones(v):
    """Filas de la tabla de verificaciones: (verificacion, ecuacion, calculo sustituido, capacidad, demanda, FU)."""
    res, fu, p, familia = v['res'], v['fu_res'], v['p'], v['familia']
    fy, fuu, U, A = v['fy'], v['fu'], v['U'], p['A']
    d = v.get('dem') or {}
    filas = []
    # Traccion
    calc_t = f'Fy·Ag/Ωt = {_v(fy, 1)}·{_v(A, 3)}/1.67 = {_v(res["Pa_t_fluencia"], 1)}'
    if fuu:
        calc_t += (f'; Fu·U·Ag/Ωt = {_v(fuu, 1)}·{_v(U, 3)}·{_v(A, 3)}/2.00 = {_v(res["Pa_t_fractura"], 1)}')
    filas.append(('Tracción', '§D2: D2-1 Pn = Fy·Ag (Ωt = 1.67); D2-2 Pn = Fu·Ae (Ωt = 2.00). §D3 Tabla D3.1: Ae = U·Ag (ángulos)' if familia == 'LI' else '§D2: D2-1 Pn = Fy·Ag (Ωt = 1.67); D2-2 Pn = Fu·Ae (Ωt = 2.00), Ae = Ag',
                  calc_t + f'; Pa = mín = {_v(res["Pa_t"], 1)}', res['Pa_t'], d.get('Pr_t'), fu and fu['FU TRACCION']))
    # Compresion
    dc = res['detalle_c']
    if familia == 'LI':
        klr_txt = f'λz = {_v(dc["lam_z"], 1)} (eje z), λu = {_v(dc["lam_u"], 1)} (eje u)'
        ecu_c = '§E3: E3-4 Fe = π²E/(KL/r)², E3-2/E3-3 Fn. §E5: E5-1/E5-2 (Lc/rz) si se verifica. §E7: Ae con patas. Ωc = 1.67'
    else:
        klr_txt = f'KL/rx = {_v(res["KLr_fuerte"], 1)}; KL/ry = {_v(res["KLr_debil"], 1)}'
        ecu_c = '§E3: E3-4 Fe, E3-2/E3-3 Fn. §E4: E4-2, E4-3 (Fex), E4-7. §E7: Ae = Ag − Σ(b − be)·t. Ωc = 1.67'
    calc_c = (f'{klr_txt}; gobierna {html.escape(str(dc.get("gobierna")))}; '
              + (f'Fe = {_v(dc["Fe"], 1)} kgf/cm²; ' if 'Fe' in dc else '') +
              f'Fn = {_v(dc["Fn"], 1)} kgf/cm²; Ae = {_v(dc["Ae"], 3)} cm²; '
              f'Pn = Fn·Ae = {_v(dc["Fn"] * dc["Ae"], 0)}')
    if fu and fu['FU COMPRESION'] == 0.0:
        calc_c += '; sin compresión en las combinaciones'
    filas.append(('Compresión', ecu_c, calc_c, res['Pa_c'], d.get('Pr_c'), fu and fu['FU COMPRESION']))
    # Flexion eje mayor
    dx = res['detalle_x']
    if familia == 'LI':
        calc_x = (f'My = Fy·Su = {_v(dx["My"], 1)}; Mcr (F10-4) = {_v(dx["Mcr"], 1)}; LTB (F10-2/3) = {_v(dx["LTB"], 1)}; '
                  f'Mn = {_v(dx["Mn"], 1)}')
        ecu_x = '§F10: F10-1 Mn = 1.5·My; F10-2/F10-3 LTB; F10-4 Mcr (βw = 0). §F10.3: F10-6 a F10-8 (pata). Ωb = 1.67'
        mr = math.hypot(d.get('Mr_x', 0.0), d.get('Mr_y', 0.0)) if d else None
    else:
        calc_x = (f'Mp = Fy·Zx = {_v(dx["Mp"], 1)}; LTB (F2) = {_v(dx["LTB"], 1)}; patín (F3) = {_v(dx.get("LFB"), 1)}; '
                  f'Mn = {_v(min(dx["LTB"], dx.get("LFB", dx["LTB"])), 1)}')
        ecu_x = '§F2: F2-1 Mn = Mp; F2-2 LTB inelástico; F2-3 LTB elástico (F2-4 a F2-8). §F3: F3-1, F3-2 (patín). Ωb = 1.67'
        mr = d.get('Mr_x') if d else None
    filas.append(('Flexión eje mayor', ecu_x, calc_x + f'; Ma = Mn/1.67 = {_v(res["Ma_x"], 1)}',
                  res['Ma_x'], mr, fu and fu['FU FLEXION EJE MAYOR']))
    # Flexion eje menor
    dy = res['detalle_y']
    if familia == 'LI':
        calc_y = f'My = Fy·Sv = {_v(dy["My"], 1)}; Mn = mín(1.5My; LLB) = {_v(dy["Mn"], 1)}'
        ecu_y = '§F10: F10-1 Mn = 1.5·My. §F10.3: F10-6 a F10-8 (pata, eje v). Ωb = 1.67'
        mr_y = mr
    else:
        calc_y = (f'Mp = mín(Fy·Zy; 1.6·Fy·Sy) = {_v(dy["Mp"], 1)}; My = Fy·Sy = {_v(dy["My"], 1)}')
        ecu_y = '§F6: F6-1 Mp = mín(Fy·Zy; 1.6·Fy·Sy); F6-2, F6-3 (patín y alma). Ωb = 1.67'
        mr_y = d.get('Mr_y') if d else None
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
    filas.append(('Cortante eje mayor', ecu_vx, calc_vx + f'; Va = {_v(res["Va_x"], 1)}', res['Va_x'],
                  d.get('Vr_x') if d else None, fu and fu['FU CORTANTE EJE MAYOR']))
    filas.append(('Cortante eje menor', ecu_vy, calc_vy + f'; Va = {_v(res["Va_y"], 1)}', res['Va_y'],
                  d.get('Vr_y') if d else None, fu and fu['FU CORTANTE EJE MENOR']))
    # Interaccion
    if familia == 'LI':
        ecu_i = '§H2: H2-1 fra/Fca + frbw/Fcbw + frbz/Fcbz ≤ 1 (Mr = momento resultante sobre cada eje principal)'
        calc_i = (f'Pa compresión = {_v(res["Pa_c"], 1)} kgf; Pa tracción = {_v(res["Pa_t"], 1)} kgf; '
                  f'Mau = {_v(res["Ma_x"], 1)} kgf·cm; Mav = {_v(res["Ma_y"], 1)} kgf·cm')
    else:
        ecu_i = '§H1.1: H1-1a Pr/Pc + 8/9·(Mrx/Mcx + Mry/Mcy) ≤ 1 (Pr/Pc ≥ 0.2); H1-1b Pr/(2Pc) + (Mrx/Mcx + Mry/Mcy) ≤ 1 (Pr/Pc < 0.2)'
        calc_i = f'Pc = {_v(res["Pa_c"], 1)} (compresión) o Pt = {_v(res["Pa_t"], 1)} (tracción)'
    filas.append(('Interacción', ecu_i, calc_i, None, None, fu and fu['FU INTERACCION (H1/H2)']))
    return filas


def _estado_txt(ok):
    if ok is None:
        return '—'
    return f'<span class="{"cumple" if ok else "nocumple"}">{"CUMPLE" if ok else "NO CUMPLE"}</span>'


def _tabla_verif(v):
    filas = _verificaciones(v)
    cuerpo = []
    for nombre, ecu, calc, cap, dem, fu in filas:
        cuerpo.append(f'<tr><td>{nombre}{_refs_verif(nombre, v["familia"])}</td><td class="ec">{html.escape(ecu)}</td>'
                      f'<td class="ec">{calc}</td><td class="num">{_v(cap, 1) if cap is not None else "—"}</td>'
                      f'<td class="num">{_v(dem, 1) if dem is not None else "—"}</td>'
                      f'<td class="num">{_fu(fu)}</td></tr>')
    ev = v['ev']
    for nombre, (lam, lr) in ev['el_det'].items():
        cuerpo.append(f'<tr><td>Esbeltez local: {html.escape(nombre)}{_ref_local(v)}</td>'
                      f'<td class="ec">NTC Tabla 3.2.1 (compresión) / Tabla 3.2.2 (flexión): λ ≤ λr</td>'
                      f'<td class="ec">λ = {_v(lam, 2)}; λr = {_v(lr, 2)}</td>'
                      f'<td class="num">{_v(lr, 2)}</td><td class="num">{_v(lam, 2)}</td>'
                      f'<td class="num">{_estado_txt(lam <= lr)}</td></tr>')
    if v['grupo'] in DA.COMPRESION_GRUPOS:
        lim = 60.0 if (v['grupo'] == 'COLUMNA' and v['nivel'] in ('ALTA', 'MEDIA')) else 200.0
        ecu_g = 'NTC 2.3.2: KL/r ≤ 200 (§E2 recomienda 200)' + ('; columna dúctil 12.1.3.1: KL/r ≤ 60' if lim == 60.0 else '')
        cuerpo.append(f'<tr><td>Esbeltez global{_ref_html("NTC_2_3_2")}'
                      + (_ref_html('NTC_12_1_3_1') if lim == 60.0 else '') + f'</td><td class="ec">{ecu_g}</td>'
                      f'<td class="ec">KL/r máx = {_v(v["klr"], 1)}</td><td class="num">{_v(lim, 0)}</td>'
                      f'<td class="num">{_v(v["klr"], 1)}</td><td class="num">{_estado_txt(v["klr"] <= lim)}</td></tr>')
    else:
        cuerpo.append('<tr><td>Esbeltez global</td><td class="ec">NTC 2.3.2: KL/r ≤ 200 (§E2)</td>'
                      '<td class="ec">no aplica: elemento sin compresión</td><td class="num">—</td>'
                      '<td class="num">—</td><td class="num">—</td></tr>')
    if (v.get('fu_res') or {}).get('FU TRACCION'):
        lim_t = 300.0 if v['grupo'] in ('ARRIOSTRE', 'DIAGONAL') else 240.0
        lmax = max(v['lx'], v['ly']) * 100.0
        rmin = v['p']['rz'] if v['familia'] == 'LI' else min(v['p']['rx'], v['p']['ry'])
        est_t = ('<span class="cumple">dentro de la referencia</span>' if lmax / rmin <= lim_t
                 else '<span class="nocumple">supera la referencia</span>')
        cuerpo.append(f'<tr><td>Esbeltez en tensión (referencia){_ref_html("NTC_2_3_2")}{_ref_html("NTC_4_4")}</td>'
                      f'<td class="ec">NTC 2.3.2: límite de referencia {lim_t:.0f} ({"miembros principales" if lim_t == 240.0 else "contraventeos y secundarios"}); NTC 4.4: sin límite obligatorio</td>'
                      f'<td class="ec">L/r = {_v(lmax, 1)} / {_v(rmin, 2)}</td><td class="num">{lim_t:.0f}</td>'
                      f'<td class="num">{_v(lmax / rmin, 1)}</td><td class="num">{est_t}</td></tr>')
    dd = ev.get('dd')
    if dd is not None and v['nivel']:
        if v['familia'] == 'LI':
            lam_d, lim_d = dd['lambda'], dd['limite']
        else:
            lam_d = dd['lf']
            lim_d = dd['lda_f'] if v['nivel'] == 'ALTA' else dd['ldm_f']
        cuerpo.append(f'<tr><td>Ductilidad ({v["nivel"]}){_ref_html("NTC_12_1_2")}</td><td class="ec">NTC Tabla 12.1.2: ancho/grueso</td>'
                      f'<td class="ec">b/t = {_v(lam_d, 2)}</td><td class="num">{_v(lim_d, 2)}</td>'
                      f'<td class="num">{_v(lam_d, 2)}</td><td class="num">{_estado_txt(lam_d <= lim_d)}</td></tr>')
    cabecera = ('<tr><th>Verificación</th><th>Ecuación</th><th>Cálculo</th><th>Límite / capacidad</th>'
                '<th>Calculado / demanda</th><th>FU o estado</th></tr>')
    return f'<table>{cabecera}{"".join(cuerpo)}</table>'


COLS_GRUPO = ['ID', 'PERFIL', 'FU INTERACCIÓN (H1/H2)', 'ELEM. LOCAL CRÍTICO', 'CLASIF. NTC (3.2)', 'λ LOCAL CALC',
              'λ LOCAL LÍMITE', 'KL/r CALC', 'KL/r LÍMITE', 'λ DUCT CALC', 'λ DUCT LÍMITE', 'ESTADO', 'NOTA']


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
    """Una fila de la tabla por grupo: FU de interaccion, esbeltez local y global (calculado y limite) y estado."""
    if 'res' not in v or not v.get('fu_res'):
        return [v['id'], v['perfil']] + [None] * 9 + [v['estado'], v.get('motivo', '')]
    ev = v['ev']
    inter = _interaccion(v)
    crit, lam_c, lam_l = max(((n, l, r) for n, (l, r) in ev['el_det'].items()), key=lambda t: t[1] / t[2])
    klr_c = klr_l = None
    if v['grupo'] in DA.COMPRESION_GRUPOS:
        klr_c = round(v['klr'], 2)
        klr_l = 60.0 if (v['grupo'] == 'COLUMNA' and v['nivel'] in ('ALTA', 'MEDIA')) else 200.0
    dd = ev.get('dd')
    lam_d_c = lam_d_l = None
    if dd is not None and v['nivel']:
        lam_d_c = dd['lambda'] if v['familia'] == 'LI' else dd['lf']
        lam_d_l = dd['limite'] if v['familia'] == 'LI' else (dd['lda_f'] if v['nivel'] == 'ALTA' else dd['ldm_f'])
        lam_d_c, lam_d_l = round(lam_d_c, 2), round(lam_d_l, 2)
    nota = []
    if v['familia'] == 'LI' and not v['e5_b'] and v['grupo'] in DA.COMPRESION_GRUPOS:
        nota.append('E5 no verificado: K L/rz y H2')
    if v['grupo'] not in DA.COMPRESION_GRUPOS:
        nota.append('sin compresión: KL/r no aplica')
    clasif = (f'tipo {DA.tipo_seccion_flexion(v["p"], v["familia"], v["fy"], v["E"])}' if v['grupo'] == 'VIGA'
              else DA.clasificacion_compresion(v['p'], v['familia'], v['fy'], v['E']))
    return [v['id'], v['perfil'], round(inter, 3), crit, clasif, round(lam_c, 2), round(lam_l, 2), klr_c, klr_l,
            lam_d_c, lam_d_l, v['estado'], '; '.join(nota)]


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
    ops = []
    for n in catalogo:
        if n not in peor:
            etiqueta = f'{n}  —  sin datos para este grupo'
        elif peor[n] is None:
            etiqueta = f'{n}  —  no revisado en alguna barra'
        else:
            x = peor[n]
            etiqueta = f'{n}  —  {"cumple" if x <= 1.0 else "no cumple"} (FU máx {x:.2f})'
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
    """Detalle de una barra: datos, propiedades, combinaciones y verificaciones con ecuaciones y referencias."""
    if 'res' not in v or not v.get('fu_res'):
        return (f'<section class="barra"><h2>Barra {v["id"]} · {html.escape(v["perfil"])} · {v["grupo"]} · '
                f'{v["estado"]}</h2><p>{html.escape(v.get("motivo", ""))}</p></section>')
    cl = 'cumple' if v['estado'] == 'CUMPLE' else 'nocumple'
    dem = v.get('dem') or {}
    datos = (f'<table class="meta"><tr><td><b>Material</b>: {html.escape(str(v["material"]))} · '
             f'Fy = {_v(v["fy"], 0)} kgf/cm² · Fu = {_v(v["fu"], 0)} kgf/cm² · E = {_v(v["E"], 0)} kgf/cm² · '
             f'ν = {_v(v["nu"], 2)}</td></tr>'
             f'<tr><td><b>Longitudes</b>: L = {_v(v["L"], 1)} cm · LX = {_v(v["lx"] * 100, 1)} cm · '
             f'LY = {_v(v["ly"] * 100, 1)} cm · LB = {_v(v["lb"] * 100, 1)} cm · KX = {_v(v["kx"], 2)} · '
             f'KY = {_v(v["ky"], 2)} · Cb = {_v(v["cb"], 2)} · Ductilidad (BARRAS): '
             f'{html.escape(v["nivel"] or "no marcada")}</td></tr>'
             + ('<tr><td><b>Ángulo</b>: E5 ' + ('verificado (LONGITUDES)' if v['e5_b'] else
                                                  'no verificado: se usa K L/rz y H2')
                + f' · conexión {html.escape(v["conexion"])} · U = {_v(v["U"], 3)} · l = {_v(v["l_li"], 1)} cm</td></tr>'
                if v['familia'] == 'LI' else '')
             + '</table>')
    sup = ''.join(f'<li>{html.escape(s)}</li>' for s in v.get('supuestos', []))
    return (f'<section class="barra" id="barra-{v["id"]}">'
            f'<h2>Barra {v["id"]} · {html.escape(v["perfil"])} · {html.escape(v["grupo"])} · '
            f'<span class="{cl}">{v["estado"]}</span> · FU máximo {_v(fu_max(v), 3)}</h2>'
            f'{datos}'
            f'<h3>Propiedades de la sección</h3>{_props_tabla(v)}'
            f'<h3>Combinaciones de servicio de la barra</h3>'
            f'<p class="nota">Cada combinación se revisa con sus propias demandas. Resaltada: la que controla '
            f'(<b>{html.escape(str(v.get("caso_dem")))}</b>).</p>{_tabla_combinaciones(v)}'
            f'<h3>Verificaciones (AISC 360-22 ASD y NTC), combinación que controla</h3>'
            f'<p class="nota">Capacidad = resistencia admisible; demanda = la de la combinación que controla. '
            f'FU = demanda / capacidad (cumple si FU ≤ 1.0). Las filas de esbeltez comparan λ calculado con λ límite (NTC).</p>'
            f'{_tabla_verif(v)}'
            + (f'<h3>Supuestos de esta barra</h3><ul class="nota">{sup}</ul>' if sup else '')
            + '</section>')


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


# Referencias de las verificaciones: apartado y pagina del documento (NTC-Acero CDMX 2020 y AISC 360-22).
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
    'G6': 'AISC 360-22 §G6 (cortante en eje menor), pág. 16.1-81',
    'H1': 'AISC 360-22 §H1.1, ecs. H1-1a y H1-1b, pág. 16.1-82 y 16.1-83',
    'H2': 'AISC 360-22 §H2 (secciones no cubiertas por H1), ec. H2-1, pág. 16.1-84',
    'NTC_2_3_1': 'NTC-Acero CDMX 2020, §2.3.1 (relación de esbeltez K L/r), pág. 40',
    'NTC_2_3_2': 'NTC-Acero CDMX 2020, §2.3.2 (relaciones de esbeltez máximas), pág. 41',
    'NTC_3_2_1_1': 'NTC-Acero CDMX 2020, §3.2.1.1 y Tabla 3.2.1 (compresión), pág. 56 y 57',
    'NTC_3_2_1_2': 'NTC-Acero CDMX 2020, §3.2.1.2 y Tabla 3.2.2 (flexión), pág. 56 y 58',
    'NTC_3_2_5': 'NTC-Acero CDMX 2020, §3.2.5 (anchos efectivos; no aplicados), pág. 61',
    'NTC_4_4': 'NTC-Acero CDMX 2020, §4.4 (relaciones de esbeltez en tensión), pág. 65 y 66',
    'NTC_12_1_2': 'NTC-Acero CDMX 2020, Tabla 12.1.2 (ancho/grueso, ductilidad), pág. 212',
    'NTC_12_1_3_1': 'NTC-Acero CDMX 2020, §12.1.3.1 (columnas dúctiles, KL/r ≤ 60), pág. 207',
    'NTC_CA_4_1_1': 'NTC Criterios y Acciones CDMX, §4.1.1 b), pág. 8',
    'NTC_CA_4_1_1_A': 'NTC Criterios y Acciones CDMX, §4.1.1 a), pág. 8',
    'NTC_11_4': 'NTC-Acero CDMX 2020, §11.4 (deflexiones: remite a las NTC de Criterios y Acciones), pp. 197 y 198',
    'NTC_11_6': 'NTC-Acero CDMX 2020, §11.6 (desplazamientos laterales: remite al Art. 149 del Reglamento y al Capítulo 1 '
                'de las NTC de Diseño por Sismo), pp. 201 y 202',
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
    return ''.join(_ref_html(k) for k in mapa.get(nombre, []))


def _ref_local(v):
    """Referencia NTC de la esbeltez local: Tabla 3.2.1 en compresion, Tabla 3.2.2 en flexion."""
    return _ref_html('NTC_3_2_1_1' if v['grupo'] in DA.COMPRESION_GRUPOS else 'NTC_3_2_1_2')


def _nota_normativa():
    """Nota de la memoria: el diseno es AISC 360-22 ASD y las esbelteces se verifican con la NTC-Acero CDMX."""
    filas = [
        ('Esbeltez global en compresión (obligatorio)', REF['NTC_2_3_2'], 'KL/r ≤ 200',
         'COLUMNA, ARRIOSTRE, DIAGONAL'),
        ('Columna dúctil', REF['NTC_12_1_3_1'], 'KL/r ≤ 60', 'COLUMNA con DUCTILIDAD ALTA o MEDIA'),
        ('Esbeltez local en compresión: patín', REF['NTC_3_2_1_1'],
         'b/t ≤ 0.56·√(E/Fy) (I y canal); ala de ángulo b/t ≤ 0.45·√(E/Fy)', 'COLUMNA, ARRIOSTRE, DIAGONAL'),
        ('Esbeltez local en compresión: alma', REF['NTC_3_2_1_1'], 'h/t ≤ 1.49·√(E/Fy)',
         'COLUMNA, ARRIOSTRE, DIAGONAL'),
        ('Esbeltez local en flexión: patín', REF['NTC_3_2_1_2'],
         'b/t ≤ 1.00·√(E/Fy) (tipo 3); 0.38 (tipo 2); 0.30 (tipo 1)', 'VIGA'),
        ('Esbeltez local en flexión: alma', REF['NTC_3_2_1_2'],
         'h/t ≤ 5.70·√(E/Fy) (tipo 3); 3.76 (tipo 2); 2.45 (tipo 1)', 'VIGA'),
        ('Esbeltez local en flexión: ala de ángulo', REF['NTC_3_2_1_2'],
         'b/t ≤ 0.91·√(E/Fy) (tipo 3); 0.54 (tipo 2)', 'VIGA (LI)'),
        ('Tipo de sección en flexión', REF['NTC_3_2_1_2'],
         'tipo 1, 2 o 3 si λ ≤ λr; tipo 4 queda fuera del diseño', 'VIGA'),
        ('Límite de esbeltez en tensión', REF['NTC_2_3_2'] + '. Sin límite obligatorio: ' + REF['NTC_4_4'],
         'L/r ≤ 240 en miembros principales; L/r ≤ 300 en contraventeos y secundarios',
         'barras con tensión'),
        ('Ductilidad: patines y alas', REF['NTC_12_1_2'],
         'b/t ≤ 0.30·√(E/Fy) (alta) o 0.38·√(E/Fy) (media)', 'barras con DUCTILIDAD marcada'),
    ]
    cuerpo = ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in filas)
    return ('<h2>Nota normativa: esbelteces con la NTC-Acero CDMX</h2>'
            '<p>Proyecto en México. El diseño de resistencia (tracción, compresión, flexión, cortante e interacción) '
            'se hace con AISC 360-22 (ASD). Las verificaciones de esbeltez local y global se hacen con la '
            'NTC-Acero CDMX (Gaceta Oficial, 7 de julio de 2020), que son obligatorias para este proyecto. Cada límite '
            'indica el apartado y la página del documento.</p>'
            '<table><tr><th>Verificación</th><th>Referencia (documento, apartado y página)</th><th>Límite</th>'
            '<th>Aplica a</th></tr>' + cuerpo + '</table>'
            '<ul class="nota">'
            '<li>Un elemento con λ &gt; λr se considera esbelto (sección tipo 4) y su perfil no se usa. La NTC permite '
            'anchos efectivos (3.2.5); no se aplican, por criterio conservador.</li>'
            '<li>λ = b/t en patines y alas (b = B/2 en patines de I; b = B en canales); h/t en almas, con h = H − 2t.</li>'
            '<li>Tensión: la NTC 4.4 no fija límite obligatorio; los valores 240 y 300 de la NTC 2.3.2 se reportan '
            'como límite de referencia y su cumplimiento es informativo.</li>'
            '</ul>')


_ETIQUETA_CLASE = {'gravitacional': 'Solo D y L', 'sismo': 'Incluye E (sismo)',
                   'viento': 'Incluye W (viento: no aplica al proyecto)', 'otra': 'TIPO no reconocido en ESTADOS'}


def _distorsiones(dib, casos, id_barra):
    """Distorsion horizontal de entrepiso (NTC-CA 4.1.1 b): desplazamiento horizontal relativo entre los extremos de cada
    columna (barra casi vertical) dividido entre su altura. dib.nodos en m; res['nodos'] en cm.
    Devuelve [(combinacion, distorsion_max, columna_que_controla, h_cm, delta_mm)]."""
    cols = []
    for i, b in enumerate(dib.barras):
        p1, p2 = np.array(dib.nodos[b['n1']], float), np.array(dib.nodos[b['n2']], float)
        largo = float(np.linalg.norm(p2 - p1))
        dz = abs(p2[2] - p1[2])
        if largo > 0 and dz >= 0.9 * largo:
            bot, top = (b['n1'], b['n2']) if p1[2] < p2[2] else (b['n2'], b['n1'])
            cols.append((id_barra.get(i, i), bot, top, dz * 100.0))
    filas = []
    for nombre, tipo, res in casos:
        if tipo != 'COMBINACION' or not cols:
            continue
        mejor = None
        for idb, bot, top, h_cm in cols:
            ub = np.array(res['nodos'][bot][:2], float)
            ut = np.array(res['nodos'][top][:2], float)
            d_cm = float(np.linalg.norm(ut - ub))
            if mejor is None or d_cm / h_cm > mejor[1]:
                mejor = (nombre, d_cm / h_cm, idb, h_cm, d_cm * 10.0)
        filas.append(mejor)
    return filas


def _cumple_html(ok):
    return f'<span class="{"cumple" if ok else "nocumple"}">{"CUMPLE" if ok else "NO CUMPLE"}</span>'


def _distorsion_texto(rel):
    return '0' if rel <= 0 else f'1 / {1.0 / rel:,.0f}'


def _columnas(dib, id_barra):
    """Columnas (barras casi verticales): [(id, nodo_inferior, nodo_superior, h_cm)]."""
    cols = []
    for i, b in enumerate(dib.barras):
        p1, p2 = np.array(dib.nodos[b['n1']], float), np.array(dib.nodos[b['n2']], float)
        largo = float(np.linalg.norm(p2 - p1))
        dz = abs(p2[2] - p1[2])
        if largo > 0 and dz >= 0.9 * largo:
            bot, top = (b['n1'], b['n2']) if p1[2] < p2[2] else (b['n2'], b['n1'])
            cols.append((id_barra.get(i, i), bot, top, dz * 100.0))
    return cols


def _rel(res, bot, top):
    """Desplazamiento horizontal relativo (cm, vector XY) entre los nodos superior e inferior de una columna."""
    return np.array(res['nodos'][top][:2], float) - np.array(res['nodos'][bot][:2], float)


def _dcol(dG, dE, fac, h_cm):
    """Desplazamiento de entrepiso / h de una columna: gravedad dG mas +-fac*dE (la accion sismica es reversible)."""
    return max(float(np.linalg.norm(dG + sg * fac * dE)) for sg in (1.0, -1.0)) / h_cm


def _periodo(dib, cargas, estados, sismos, D_estados, g=9.81):
    """Periodo fundamental aproximado, NTC 6.4.1: T = 2*pi*sqrt(sum(W X^2) / (g*sum(F X))), sumando todos los niveles.
    W de cada nivel: carga D nodal mas la mitad del peso de cada barra en sus extremos. F: fuerza horizontal del nivel
    en la direccion de la fuerza horizontal total del estado sismico. X: desplazamiento medio del nivel en esa direccion (m)."""
    z_niv = sorted({round(float(p[2]), 3) for p in dib.nodos})[1:]
    W_nodo = np.zeros(len(dib.nodos))
    for n in D_estados:
        for idx, v in cargas.get(n, {}).items():
            W_nodo[idx] += -float(v[2])
    for b in dib.barras:
        m = (G.obtener_perfil(b['perfil']) or {}).get('masa') or 0.0
        L = float(np.linalg.norm(np.array(dib.nodos[b['n1']], float) - np.array(dib.nodos[b['n2']], float)))
        W_nodo[b['n1']] += m * L / 2.0
        W_nodo[b['n2']] += m * L / 2.0
    resultado = {}
    for e in sismos:
        cg = cargas.get(e, {})
        H = sum((np.array(v[:2], float) for v in cg.values()), np.zeros(2))
        if np.linalg.norm(H) == 0.0:
            resultado[e] = None
            continue
        Hh = H / np.linalg.norm(H)
        num = den = 0.0
        for z in z_niv:
            nodos_nivel = [i for i, p in enumerate(dib.nodos) if round(float(p[2]), 3) == z]
            F_i = sum((float(np.array(cg[i][:2], float) @ Hh) for i in nodos_nivel if i in cg), 0.0)
            X_i = float(np.mean([np.array(estados[e]['nodos'][i][:2], float) @ Hh for i in nodos_nivel])) / 100.0
            num += float(W_nodo[nodos_nivel].sum()) * X_i ** 2
            den += F_i * X_i
        resultado[e] = 2.0 * np.pi * np.sqrt(num / (g * den)) if den > 0 else None
    return resultado


def _seccion_sismo(dib, casos, id_barra, proyecto):
    """6.3 Distorsion por sismo, metodo estatico (NTC Diseno por Sismo 2023). Todos los valores vienen de la
    configuracion de la planilla (hojas PARAMETROS y NORMA, ver 3.1)."""
    cf = proyecto['conf']
    tipos = getattr(dib, 'estados_tipo', {}) or {}
    estados = {n: res for n, t, res in casos if t == 'ESTADO'}
    sismos = [n for n in estados if tipos.get(n) == 'E']
    if not sismos:
        return ('<h3>6.3 Distorsión por sismo</h3><p class="nota">La planilla no tiene estados sísmicos (TIPO E): '
                'no hay distorsión sísmica que revisar.</p>')
    gravedad = [n for n in estados if tipos.get(n) in ('D', 'L')]
    D_estados = [n for n in estados if tipos.get(n) == 'D']
    cargas = getattr(dib, 'cargas', {}) or {}
    cols = _columnas(dib, id_barra)
    periodos = _periodo(dib, cargas, estados, sismos, D_estados, g=cf['g'])
    T_list = [t for t in periodos.values() if t is not None]
    # DECISION D8 (abierta): k2 con el periodo menor de los estados sismicos (conservador); T segun 6.4.1 con las fuerzas del estado.
    T_ctrl = min(T_list) if T_list else None                  # el periodo menor da el k2 mayor (conservador)
    k2 = 0.0 if (T_ctrl is None or T_ctrl >= cf['ta']) else cf['k2_coef'] * (1.0 - (T_ctrl / cf['ta']) ** cf['k2_exp'])
    R = cf['k1'] * cf['R0'] + k2
    # DECISION D5 (abierta): la carga de la planilla se toma como diseno SV reducido por Q'R'. Distorsion elastica = f * planilla.
    f_el = cf['qp'] * R                                       # LDNE y OI
    f_sv = cf['Q'] * R                                        # Seguridad de Vida (multiplicador QR' de 1.7)
    ks, g_ldne, g_oi, g_sv = cf['ks'], cf['gLDNE'], cf['gOI'], cf['gSV']
    filas, drift_piso = [], {}
    for idb, bot, top, h_cm in cols:
        dG = sum((_rel(estados[g], bot, top) for g in gravedad), np.zeros(2))
        mejor = None
        for e in sismos:
            db = _dcol(dG, _rel(estados[e], bot, top), f_el, h_cm)
            if mejor is None or db > mejor[0]:
                mejor = (db, e)
        db, e = mejor
        dl = max(_dcol(dG, _rel(estados[e2], bot, top), ks * f_el, h_cm) for e2 in sismos)
        dsv = max(_dcol(dG, _rel(estados[e2], bot, top), f_sv, h_cm) for e2 in sismos)
        zb = round(float(dib.nodos[bot][2]), 3)
        drift_piso[zb] = max(drift_piso.get(zb, 0.0), db, dsv)
        marca = lambda ok, g: f'{_cumple_html(ok)} <span class="nota">(γ {g:.4f})</span>'
        filas.append(
            f'<tr><td class="num">{idb}</td><td>{html.escape(str(e))}</td><td class="num">{_v(h_cm, 1)}</td>'
            f'<td class="num">{_v(db * h_cm * 10.0, 2)}</td><td class="num">{"0" if db <= 0 else f"1 / {1.0 / db:,.0f}"}</td>'
            f'<td>{marca(ks * db <= g_ldne, g_ldne)}<br><span class="nota">Ks·δ/h = {ks * db:.5f}</span></td>'
            f'<td>{marca(db <= g_oi, g_oi)}</td><td>{marca(dsv <= g_sv, g_sv)}</td></tr>')
    tabla_ldne = ('<table><tr><th>Columna</th><th>Estado sísmico que controla</th><th>h (cm)</th>'
                  '<th>δ elástica (mm)</th><th>δ/h</th><th>LDNE</th><th>Ocupación Inmediata</th>'
                  '<th>Seguridad de Vida</th></tr>' + ''.join(filas) + '</table>')
    filas_t = ''.join(
        f'<tr><td>{html.escape(str(e))}</td><td class="num">{"—" if periodos[e] is None else f"{periodos[e]:.3f}"}</td></tr>'
        for e in sismos)
    tabla_t = ('<table><tr><th>Estado sísmico</th><th>T aproximado (s), §6.4.1</th></tr>' + filas_t + '</table>')

    zs = sorted({round(float(p[2]), 3) for p in dib.nodos})
    filas2 = []
    for k in range(len(zs) - 1):
        zb, zt = zs[k], zs[k + 1]
        arriba = {i for i, p in enumerate(dib.nodos) if round(float(p[2]), 3) >= zt - 1e-6}
        V = max((float(np.linalg.norm(sum((np.array(v[:2], float) for idx, v in cargas.get(e, {}).items()
                                           if idx in arriba), np.zeros(2)))) for e in sismos), default=0.0)
        W = sum(-float(v[2]) for n in D_estados for idx, v in cargas.get(n, {}).items() if idx in arriba)
        for b in dib.barras:
            if b['n1'] in arriba and b['n2'] in arriba:
                pb = np.array(dib.nodos[b['n1']], float) - np.array(dib.nodos[b['n2']], float)
                masa = (G.obtener_perfil(b['perfil']) or {}).get('masa') or 0.0
                W += masa * float(np.linalg.norm(pb))                          # kgf: kg/m por m
        # DECISION D9 (abierta): V = cortante del sismo; W = carga D sin factor mas peso propio encima; se compara con la mayor distorsion elastica o SV.
        lim = cf['seg2'] * V / W if W > 0 else None
        dmax_piso = drift_piso.get(zb)
        if lim is None or dmax_piso is None:
            estado = '<span class="nota">sin datos</span>'
        else:
            estado = ('<span class="cumple">se pueden despreciar</span>' if dmax_piso <= lim
                      else '<span class="nocumple">requiere análisis de segundo orden</span>')
        filas2.append(
            f'<tr><td>{zb:.2f} a {zt:.2f}</td><td class="num">{_v(V, 1)}</td><td class="num">{_v(W, 1)}</td>'
            f'<td class="num">{"—" if lim is None else f"{lim:.4f}"}</td>'
            f'<td class="num">{"—" if dmax_piso is None else f"{dmax_piso:.4f}"}</td><td>{estado}</td></tr>')
    tabla_2 = ('<table><tr><th>Entrepiso z (m)</th><th>V sismo (kgf)</th><th>W encima (kgf, sin factor)</th>'
               f'<th>{cf["seg2"]:g}·V/W</th><th>δ/h máx (elástica o SV)</th><th>Efectos de 2º orden (2.4.1)</th></tr>'
               + ''.join(filas2) + '</table>') if filas2 else ''

    deform = ('elementos no estructurales deformables o separados: límite 0.004'
              if cf['deformables'] else 'elementos no estructurales no deformables: límite 0.002')
    return (f'<h3>6.3 Distorsión por sismo, método estático (NTC Diseño por Sismo, §1.7, §2.4, §3.2, §3.3, §6.3, §6.4)</h3>'
            f'<p><b>Sistema</b>: {html.escape(cf["sistema"])}. Tabla 4.3.2 (pág. 53): Q = {cf["Q"]:g}, γ<sub>SV</sub> = '
            f'{g_sv:.3f}, γ<sub>OI</sub> = {g_oi:.4f}. R<sub>0</sub> = {cf["R0"]:g} (§3.3.1a).</p>'
            f'<p><b>Factor de sobre-resistencia</b>: k<sub>1</sub> = {cf["k1"]:g} (tres o más crujías resistentes en las dos '
            f'direcciones: {"SÍ" if cf["crujias_ambas"] else "NO"}; §3.3.1a). k<sub>2</sub> = 0.5(1 − (T/Ta)²) si T &lt; Ta, '
            f'0 si T ≥ Ta (§3.3.1b) con T = {"—" if T_ctrl is None else f"{T_ctrl:.3f}"} s y Ta = {cf["ta"]:g} s '
            f'→ k<sub>2</sub> = {k2:.4f}. R = k<sub>1</sub>·R<sub>0</sub> + k<sub>2</sub> = {R:.4f}.</p>'
            f'<p><b>Factores de reducción</b>: Q′ = 1 + (Q − 1)/k = 1 + ({cf["Q"]:g} − 1)/{cf["k_sasid"]:g} = {cf["qp"]:.4f} '
            f'(§3.2, eq. 3.2.1, rama Ta–Tb; k del SASID). Para LDNE y OI: f = Q′·R = {f_el:.4f}. Para Seguridad de Vida: '
            f'f = Q·R = {f_sv:.4f} (§1.7).</p>'
            f'<p><b>Sismo de diseño</b>: el estado sísmico de la planilla es la fuerza de diseño V<sub>0</sub> = c·W<sub>0</sub>/(Q′R′) '
            f'(§6.3, eq. 6.3.1) con c = {cf["c_sasid"]:g}. Por eso la distorsión elástica, sin reducir, es f veces la de la '
            f'planilla.</p>'
            f'<p><b>Limitación de Daño No Estructural (LDNE)</b>: §1.7, pág. 26 y tabla 3.1.1. Usa la intensidad frecuente: '
            f'{html.escape(cf["ks_txt"])}, y gravedad D y L con factor 1, sin factores de carga. Límite γ<sub>LDNE</sub> = '
            f'{g_ldne:.3f} ({deform}).</p>'
            f'{tabla_ldne}'
            f'<p><b>Periodo aproximado (§6.4.1)</b>: T = 2π√(ΣW·X²/(g·ΣF·X)), con fuerzas y desplazamientos del estado '
            f'sísmico, g = {cf["g"]:g} m/s². Se usa el periodo menor para k<sub>2</sub>.</p>'
            f'{tabla_t}'
            f'<p><b>Efectos de segundo orden</b>: §2.4, pág. 32. Se pueden despreciar en un entrepiso si la distorsión no '
            f'excede {cf["seg2"]:g}·V<sub>i</sub>/W<sub>pi</sub> (eq. 2.4.1), con V la cortante del sismo y W el peso encima del '
            f'entrepiso sin factor de carga. Se compara con la mayor distorsión elástica o de SV del entrepiso.</p>'
            f'{tabla_2}')


def _seccion_desplazamientos(dib, casos, id_de_indice, id_barra, clase, proyecto):
    """Seccion 6: desplazamientos por combinacion y deformada de la que controla (6.1); distorsion de entrepiso con
    NTC-CA 4.1.1 b (6.2); distorsion por sismo (6.3) y flecha vertical de vigas (6.4). Valores de la hoja PARAMETROS y NORMA."""
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

    # DECISION D3 (abierta): h/250 sin elementos frageles unidos (NTC-CA 4.1.1 b); distorsion por columna que controla; solo gravitacionales.
    lim_h = cf['lim_h']
    if cf['fragiles']:
        criterio = (f'Límite h/{lim_h:g}: hay elementos no estructurales frágiles unidos a la estructura '
                    f'({REF["NTC_CA_4_1_1"]}).')
    else:
        criterio = (f'Límite h/{lim_h:g}: no hay elementos no estructurales frágiles unidos a la estructura, por lo que '
                    f'aplica el caso de "en otros casos" de {REF["NTC_CA_4_1_1"]}.')
    filas_d = []
    for nombre, rel, idb, h_cm, delta_mm in _distorsiones(dib, casos, id_barra):
        k = clase.get(nombre, 'otra')
        if k == 'gravitacional':
            celda = _cumple_html(rel <= 1.0 / lim_h)
        else:
            celda = '<span class="nota">no evaluada (ver 6.3)</span>'
        filas_d.append(
            f'<tr><td>{html.escape(str(nombre))}</td><td>{_ETIQUETA_CLASE.get(k, k)}</td>'
            f'<td class="num">{_distorsion_texto(rel)}</td><td class="num">{idb}</td>'
            f'<td class="num">{_v(h_cm, 1)}</td><td class="num">{_v(delta_mm, 2)}</td>'
            f'<td class="num">{_v(h_cm / lim_h * 10.0, 2)}</td><td>{celda}</td></tr>')
    if filas_d:
        tabla_dist = ('<table><tr><th>Combinación</th><th>Acciones</th><th>Distorsión máx. δ/h</th><th>Columna</th>'
                      '<th>h (cm)</th><th>δ (mm)</th>' f'<th>Límite h/{lim_h:g} (mm)</th><th>Estado</th></tr>'
                      + ''.join(filas_d) + '</table>')
    else:
        tabla_dist = '<p class="nota">No hay columnas verticales en el modelo para revisar la distorsión.</p>'

    # DECISION D1 (abierta): L/300 justificado con AISC 360-22 Comentario L2 (pag. 16.1-543); la NTC no fija numero. Alternativas: L/240, L/360.
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
            f'<h3>6.2 Distorsión horizontal de entrepiso</h3>'
            f'<p>{REF["NTC_CA_4_1_1"]}: el desplazamiento horizontal relativo entre dos niveles sucesivos no debe exceder '
            f'la altura del entrepiso entre 500 (con elementos no estructurales frágiles unidos) o entre 250 (en otros casos). '
            f'Se revisa cada columna: δ es el desplazamiento horizontal relativo entre sus extremos y h su altura; se reporta '
            f'la columna que controla.</p>'
            f'<p><b>Criterio</b>: {criterio}</p>'
            f'{tabla_dist}'
            f'<p class="nota">Solo las combinaciones gravitacionales (D y L) se comparan con este límite. Las combinaciones '
            f'con sismo (E) se revisan en 6.3.</p>'
            f'{_seccion_sismo(dib, casos, id_barra, proyecto)}'
            f'<h3>6.4 Flecha vertical de vigas</h3>'
            f'<p><b>Límite L/{divisor:g}</b>. Justificación: AISC 360-22, Comentario L2 (pág. 16.1-543): la flecha de '
            f'alrededor de 1/300 del claro es visible y puede causar daño arquitectónico; el comentario indica que los límites '
            f'dependen de la estructura (1/360 para pisos y 1/240 para cubiertas son los usuales). La NTC-Acero no fija un '
            f'número: §11.4 (pp. 197 y 198) remite a las NTC de Criterios y Acciones, y {REF["NTC_CA_4_1_1_A"]} remite a las '
            f'normas del material.</p>'
            f'<p>La flecha es la desviación vertical máxima de la viga respecto a la cuerda entre sus extremos, en las '
            f'combinaciones gravitacionales (D y L), sin el movimiento de cuerpo rígido de los apoyos. Se calcula con la '
            f'solución exacta de Euler-Bernoulli entre extremos, a partir de los giros de extremo del modelo y del peso '
            f'propio; no incluye la deformación por cortante.</p>'
            f'{tabla_f}')


def _encabezado_doc(proyecto, dib):
    meta = [('Proyecto', proyecto.get('nombre', '(completar)')),
            ('Elemento / estructura', proyecto.get('elemento', '(completar)')),
            ('Planilla de datos', proyecto.get('archivo', 'planilla_con_diseno.xlsx')),
            ('Fecha', proyecto.get('fecha', '')),
            ('Versión', proyecto.get('version', '(completar)')),
            ('Modelo', f'{len(dib.nodos)} nodos y {len(dib.barras)} barras'),
            ('Método', 'Diseño de resistencia: ASD, ANSI/AISC 360-22. Esbelteces local y global: NTC-Acero CDMX '
                       '(Gaceta Oficial, 7 de julio de 2020).'),
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
        'Criterio de aceptación: FU ≤ 1.0 en todas las verificaciones; λ ≤ λr (NTC 3.2); KL/r ≤ 200 (NTC 2.3.2); '
        'ductilidad si está marcada (NTC 12.1.2).',
        'Elementos con λ &gt; λr (sección tipo 4) quedan fuera de la lista de perfiles. La NTC permite anchos efectivos '
        '(3.2.5); no se aplican, por criterio conservador.',
        'Perfiles CS (barras macizas) y LM quedan fuera del diseño.',
        'Fu: de la hoja MATERIALES de la planilla. Un material sin Fu deja sus barras como NO REVISADO.',
        f'Ángulos (LI): E5 solo si LONGITUDES marca las cuatro condiciones ({REF["E5"]}). Si no, K·L/rz y H2 '
        f'({REF["H2"]}). Tracción con Ae = U·Ag, U de D3 ({REF["D3"]}): una pata U = 1 − x̄/l; dos patas U = 1.0.',
        'Estimaciones: IR con Zx, Zy o Cw faltantes se estiman por geometría; LI con propiedades geométricas. Cada '
        'barra lista sus supuestos.',
        'Ductilidad: marcada por barra en BARRAS (ALTA o MEDIA). Vacío = no se verifica la Tabla 12.1.2 ni KL/r ≤ 60.',
        f'Interacción: H1-1 para I y canal ({REF["H1"]}); H2-1 para ángulos ({REF["H2"]}), con el momento resultante '
        'sobre cada eje principal (criterio conservador).',
    ]
    return '<ul>' + ''.join(f'<li>{t}</li>' for t in items) + '</ul>'


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
        f'<tr><td>Sistema sísmico</td><td>{html.escape(cf["sistema"])}</td><td>NORMA, tabla 4.3.2</td></tr>'
        f'<tr><td>Q</td><td class="num">{cf["Q"]:g}</td><td>Tabla 4.3.2</td></tr>'
        f'<tr><td>R0</td><td class="num">{cf["R0"]:g}</td><td>§3.3.1a (2.0 con Q ≥ 3; 1.75 con Q &lt; 3)</td></tr>'
        f'<tr><td>k1</td><td class="num">{cf["k1"]:g}</td><td>§3.3.1a, según crujías: {"SÍ" if cf["crujias_ambas"] else "NO"}</td></tr>'
        f'<tr><td>Q′</td><td class="num">{cf["qp"]:.4f}</td><td>1 + (Q − 1)/k, con k = {cf["k_sasid"]:g} (SASID)</td></tr>'
        f'<tr><td>Ks (LDNE)</td><td class="num">{cf["ks"]:.4f}</td><td>{html.escape(cf["ks_txt"])}</td></tr>'
        f'<tr><td>γ LDNE</td><td class="num">{cf["gLDNE"]:.3f}</td><td>§1.7: 0.004 con elementos deformables o separados; '
        f'0.002 en otro caso</td></tr>'
        f'<tr><td>Límite de distorsión NTC-CA</td><td class="num">h/{cf["lim_h"]:g}</td><td>§4.1.1 b): 500 con elementos frágiles '
        f'unidos; 250 en otro caso</td></tr>'
        f'<tr><td>Límite de flecha de vigas</td><td class="num">L/{cf["flecha_divisor"]:g}</td><td>AISC 360-22, Comentario L2</td></tr>'
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
        fu_txt = 'sin Fu (barras NO REVISADO)' if fu is None or (isinstance(fu, float) and math.isnan(fu)) \
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
        duct = sorted({e['nivel'] or '—' for e in ents})
        filas_g.append(
            f'<tr><td>{g}</td><td>{len(idx)}</td><td>{html.escape(", ".join(perfiles))}</td>'
            f'<td>{html.escape(", ".join(mats))}</td>'
            f'<td class="num">{_v(max(e["lx"] for e in ents) * 100, 1)}</td>'
            f'<td class="num">{_v(max(e["ly"] for e in ents) * 100, 1)}</td>'
            f'<td class="num">{_v(max(e["lb"] for e in ents) * 100, 1)}</td>'
            f'<td class="num">{_v(max(e["kx"] for e in ents), 2)} / {_v(max(e["ky"] for e in ents), 2)}</td>'
            f'<td class="num">{_v(max(e["cb"] for e in ents), 2)}</td><td>{html.escape(", ".join(duct))}</td></tr>')
    grupos = ('<table><tr><th>Grupo</th><th>Barras</th><th>Perfil (una sección)</th><th>Material</th>'
              '<th>LX máx (cm)</th><th>LY máx (cm)</th><th>LB máx (cm)</th><th>KX / KY</th><th>Cb</th>'
              '<th>Ductilidad</th></tr>' + ''.join(filas_g) + '</table>')
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
            f'<h3>Perfil, longitudes y ductilidad por grupo</h3>{grupos}'
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


def _pendientes_html(evals, materiales_filas, proyecto, dib=None):
    items = []
    no_rev = {}
    for v in evals:
        if v['estado'] == 'NO REVISADO':
            no_rev.setdefault(v.get('motivo', ''), []).append(str(v['id']))
    for motivo, ids in no_rev.items():
        items.append(f'Barras NO REVISADO ({", ".join(ids)}): {html.escape(motivo)}.')
    fuera = [str(v['id']) for v in evals if v['estado'] == 'FUERA DE ALCANCE']
    if fuera:
        items.append(f'Barras fuera del diseño por familia ({", ".join(fuera)}): CS (macizas) y LM.')
    sin_fu = [str(f[0]) for f in materiales_filas
              if len(f) > 3 and (f[3] is None or (isinstance(f[3], float) and math.isnan(f[3])))]
    if sin_fu:
        items.append(f'Material sin Fu en la hoja MATERIALES: {", ".join(sin_fu)}. Cárguelo en la planilla.')
    li_no = [str(v['id']) for v in evals if v.get('familia') == 'LI' and 'res' in v and not v.get('e5_b')]
    if li_no:
        items.append(f'Ángulos sin E5 verificado ({", ".join(li_no)}): se usa K·L/rz y H2. Marque las cuatro '
                     f'condiciones de E5 en LONGITUDES si las cumplen.')
    sin_duct = [str(v['id']) for v in evals if 'res' in v and not v.get('nivel')]
    if sin_duct:
        items.append(f'Barras sin DUCTILIDAD marcada en BARRAS ({len(sin_duct)}): no se verifica la Tabla 12.1.2 '
                     f'de la NTC ni la columna dúctil.')
    if dib is not None and not any(t == 'E' for t in (getattr(dib, 'estados_tipo', {}) or {}).values()):
        items.append('La planilla no tiene estado sísmico (TIPO E): el diseño usa solo combinaciones gravitacionales.')
    items.append("Confirme que el estado sísmico de la planilla se calculó con V<sub>0</sub> = c·W<sub>0</sub>/(Q′R′) "
                 "del método estático (6.3), con el mismo Q, R y c de la sección 3.1.")
    items.append('No se verifican conexiones, placas, soldaduras ni pernos.')
    items.append('Ángulos: el pandeo flexotorsional (E4) no está implementado; si b/t &gt; 0.71·√(E/Fy) la barra queda '
                 'como NO REVISADO.')
    return '<ul>' + ''.join(f'<li>{t}</li>' for t in items) + '</ul>'


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
             ('λ, λr, λp, λpl', 'Relación ancho/grueso del elemento y sus límites (NTC Tablas 3.2.1 y 3.2.2)'),
             ('Pr, Mr, Vr', 'Demandas ASD: carga axial, momento y cortante de la combinación'),
             ('FU', 'Factor de utilización: demanda / capacidad (cumple si FU ≤ 1.0)')]
    cuerpo = ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in filas)
    return f'<table><tr><th>Símbolo</th><th>Significado</th></tr>{cuerpo}</table>'


def memoria_html(dib, materiales_filas, longitudes_df, demandas, id_barra, ruta_salida, proyecto=None,
                 casos=None, id_de_indice=None, equilibrio=None):
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
<h2>2. Criterios de diseño adoptados</h2>{_criterios_html()}
<h2>3. Datos de entrada</h2>{_parametros_html(proyecto['conf'])}{_datos_entrada_html(dib, materiales_filas, id_barra, lon, mat, equilibrio)}
<h2>4. Modelo de análisis</h2>{_modelo_html(dib, equilibrio)}
<h2>5. Resultados por grupo</h2>
<p class="nota">Por grupo: FU de interacción flexocompresión (H1/H2); clasificación NTC; λ calculado y λ límite del elemento
que gobierna (esbeltez local, NTC); KL/r calculado y límite (200; 60 en columna dúctil); ductilidad y estado global
(todas las verificaciones).</p>
{('<p>' + resumen_txt + '</p>') if resumen_txt else ''}
{resumen_html}
<h2>6. Desplazamientos máximos por combinación</h2>
{desp_html}
<h2>7. Detalle de barras críticas (FU máximo de cada grupo)</h2>
<p class="nota">Se detalla solo la barra que controla cada grupo. Las demás barras de cada grupo están en la tabla por
grupo (sección 5) y en diseno_asd.xlsx (RESULTADOS).</p>
{"".join(_bloque_barra(v) for v in criticas)}
<h2>8. Pendientes y limitaciones</h2>{_pendientes_html(evals, materiales_filas, proyecto, dib)}
<h2>Anexo. Simbología</h2>{_simbologia_html()}
</body></html>'''
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(cuerpo)
    return ruta_salida
