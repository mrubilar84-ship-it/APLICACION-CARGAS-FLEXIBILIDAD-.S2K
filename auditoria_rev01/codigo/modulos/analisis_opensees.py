"""
ANALISIS LINEAL 3D CON OPENSEES (openseespy) A PARTIR DE LA PLANILLA. El Excel manda:
  - E y nu por calidad: hoja MATERIALES (columnas E y NU).
  - Seccion (A, Ix fuerte, Iy debil, J, masa): base Gerdau rev04 (no ICHA).
  - Apoyos: NODOS (UX, UY, UZ, RX, RY, RZ = SI restringe ese grado) y rotulas de extremo: BARRAS (CONEXION_I/J).
  - Cargas por nodo y estado: hoja CARGAS (kgf, kgf·m).
  - Peso propio: hoja ESTADOS (PESO PROPIO = SI), calculado con la masa Gerdau (kgf/m).
  - Combinaciones: hoja COMBINACIONES (superposicion lineal de los estados).
  - Que reportar: columna REPORTAR (SI) en NODOS y BARRAS.

Unidades internas: cm, kgf, kgf·cm. Salida: kgf, kgf·m, mm, rad.

Convencion de ejes (verificada en OpenSees 3.8 con una viga de prueba):
  x = del nodo I al J; y = vecxz x x (peralte del eje fuerte); z = x x y.
  El eje fuerte es el local y: Iz (OpenSees) = Ix Gerdau; Iy = Iy Gerdau.
  Cortante fuerte = Vy; momento fuerte = Mz; cortante debil = Vz; momento debil = My.
"""
import math
import os
import numpy as np
import pandas as pd
import openseespy.opensees as ops
from orientacion_gerdau import vecxz_de_barra, ejes_locales
import perfiles_gerdau as G
from dibujo_directo import etiqueta_restricciones

GRAVEDAD = np.array([0.0, 0.0, -1.0])        # el peso propio actua hacia -Z global
ETIQUETA = ['N', 'Vy', 'Vz', 'T', 'My', 'Mz']


class ErrorAnalisis(Exception):
    pass


def _num(v):
    """Numero o None (vacio, NaN o texto no numerico)."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _marcado(v):
    """True si la celda REPORTAR dice SI."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return False
    return str(v).strip().upper() == 'SI'


def materiales_desde_filas(filas):
    """{nombre: {'E', 'nu'}} desde las filas de MATERIALES (NOMBRE, TIPO, FY, FU, E, NU, FUENTE)."""
    out = {}
    for f in filas:
        nombre = str(f[0]).strip()
        out[nombre] = {'E': _num(f[4]) if len(f) > 4 else None, 'nu': _num(f[5]) if len(f) > 5 else None}
    return out


def estados_desde_df(df):
    """[(nombre, peso_propio)] en el orden de la hoja ESTADOS. PESO PROPIO debe ser SI o NO."""
    salida = []
    for _, r in df.iterrows():
        nombre = str(r['NOMBRE']).strip()
        v = r.get('PESO PROPIO')
        v = None if v is None or (isinstance(v, float) and math.isnan(v)) else str(v).strip().upper()
        if v not in ('SI', 'NO'):
            raise ErrorAnalisis(f"ESTADOS, estado '{nombre}': PESO PROPIO debe ser SI o NO "
                                f"(si la columna no existe, use la plantilla nueva del bloque 6)")
        salida.append((nombre, v == 'SI'))
    return salida


def propiedades_barras(dib, materiales, id_barra):
    """Propiedades de cada barra: seccion desde la base Gerdau y E, nu desde MATERIALES. Lanza ErrorAnalisis
    con la lista completa de datos faltantes (no sustituye valores por cero)."""
    props, faltas = [], []
    for i, b in enumerate(dib.barras):
        etiqueta = f"barra {id_barra.get(i, i)} ({b['perfil']})"
        p = G.obtener_perfil(b['perfil']) or {}
        falta = [nombre for nombre, clave in [('area A', 'A'), ('Ix', 'Ix'), ('Iy', 'Iy'), ('J', 'J'),
                                               ('masa', 'masa')] if p.get(clave) is None]
        m = materiales.get(b.get('material'))
        if m is None:
            falta.append('material en MATERIALES')
        else:
            if m['E'] is None:
                falta.append(f"E del material {b.get('material')}")
            if m['nu'] is None:
                falta.append(f"NU del material {b.get('material')}")
        if falta:
            faltas.append(f"{etiqueta}: falta {', '.join(falta)}")
            props.append(None)
            continue
        props.append({'A': p['A'], 'Iz': p['Ix'], 'Iy': p['Iy'], 'J': p['J'], 'masa': p['masa'],
                      'E': m['E'], 'nu': m['nu']})
    if faltas:
        raise ErrorAnalisis('Datos incompletos para el analisis (no se sustituye ningun valor):\n  '
                            + '\n  '.join(faltas))
    return props


def _verificar_conectividad(dib):
    usados = set()
    for b in dib.barras:
        usados.update((b['n1'], b['n2']))
    sueltos = [i for i in range(len(dib.nodos)) if i not in usados]
    if sueltos:
        raise ErrorAnalisis(f'nodos sin barras (no forman parte del modelo): {sueltos}. '
                            'Quitelos de NODOS o conectelos.')


def _modelo(dib, props, cargas_nodales, pp):
    """Construye el modelo OpenSees del caso: nodos, apoyos, barras (con rotulas), cargas nodales y peso propio."""
    ops.wipe()
    # DECISION D12 (abierta): analisis lineal de primer orden (sin P-Delta).
    ops.model('basic', '-ndm', 3, '-ndf', 6)
    coords = [tuple(float(c) * 100.0 for c in p) for p in dib.nodos]          # m -> cm
    for i, (x, y, z) in enumerate(coords):
        ops.node(i + 1, x, y, z)
    for i, restr in dib.apoyos.items():            # restr = (UX, UY, UZ, RX, RY, RZ) de la hoja NODOS
        ops.fix(i + 1, *[int(v) for v in restr])
    siguiente = len(coords) + 1
    reac_aux = {}          # nodo de la planilla -> etiquetas de extremos articulados apoyados en ese nodo

    def extremo_rotulado(nodo_orig):
        """Extremo de barra articulado: nodo auxiliar con los giros libres. Las traslaciones restringidas del nodo
        se aplican al auxiliar (su reaccion se suma a la del nodo); las libres siguen al nodo."""
        nonlocal siguiente
        ops.node(siguiente, *coords[nodo_orig])
        tr = dib.apoyos[nodo_orig][:3] if nodo_orig in dib.apoyos else (False, False, False)
        libres = [d + 1 for d in range(3) if not tr[d]]          # traslaciones que siguen al nodo
        if libres:
            ops.equalDOF(nodo_orig + 1, siguiente, *libres)
        if any(tr):                                              # traslaciones restringidas: apoyo directo
            ops.fix(siguiente, *[int(v) for v in tr], 0, 0, 0)
            reac_aux.setdefault(nodo_orig, []).append(siguiente)
        siguiente += 1
        return siguiente - 1

    for i, b in enumerate(dib.barras):
        ni, nj = b['n1'] + 1, b['n2'] + 1
        if b.get('conexion_i') == 'rotulado':
            ni = extremo_rotulado(b['n1'])
        if b.get('conexion_j') == 'rotulado':
            nj = extremo_rotulado(b['n2'])
        p = props[i]
        G_mod = p['E'] / (2.0 * (1.0 + p['nu']))
        ops.geomTransf('Linear', i + 1, *vecxz_de_barra(dib.nodos, b))
        ops.element('elasticBeamColumn', i + 1, ni, nj, float(p['A']), float(p['E']), float(G_mod),
                    float(p['J']), float(p['Iy']), float(p['Iz']), i + 1)
    ops.timeSeries('Constant', 1)
    ops.pattern('Plain', 1, 1)
    for idx, v in cargas_nodales.items():
        ops.load(idx + 1, *[float(c) for c in v])
    if pp:
        for i, b in enumerate(dib.barras):
            x_loc, y_loc, z_loc = ejes_locales(dib, i)
            w = props[i]['masa'] / 100.0 * GRAVEDAD                 # kgf/m -> kgf/cm, hacia -Z
            # componentes del peso en ejes locales: Wy, Wz (transversal) y Wx (axial: columnas verticales)
            ops.eleLoad('-ele', i + 1, '-type', '-beamUniform',
                        float(w @ y_loc), float(w @ z_loc), float(w @ x_loc))
    return reac_aux


def _resolver(dib, props, cargas_nodales, pp):
    """Un caso (estado): desplazamientos de nodos, fuerzas en extremos de barras y reacciones (cm, kgf)."""
    reac_aux = _modelo(dib, props, cargas_nodales, pp)
    ops.system('BandGeneral')
    ops.numberer('RCM')
    ops.constraints('Transformation')
    ops.integrator('LoadControl', 1.0)
    ops.algorithm('Linear')
    ops.analysis('Static')
    if ops.analyze(1) != 0:
        ops.wipe()
        raise ErrorAnalisis('OpenSees no pudo resolver el caso. Revise apoyos y rotulas (un mecanismo no se resuelve).')
    ops.reactions()
    reac = {}
    for i in dib.apoyos:
        r = np.array(ops.nodeReaction(i + 1), float)
        for tag in reac_aux.get(i, []):                 # extremos articulados apoyados en este nodo
            r = r + np.array(ops.nodeReaction(tag), float)
        reac[i] = r
    res = {'nodos': {i: np.array(ops.nodeDisp(i + 1), float) for i in range(len(dib.nodos))},
           'barras': {i: np.array(ops.eleResponse(i + 1, 'localForces'), float) for i in range(len(dib.barras))},
           'reac': reac}
    res['extremos'] = {}
    for i in range(len(dib.barras)):
        ni, nj = ops.eleNodes(i + 1)
        res['extremos'][i] = (np.array(ops.nodeDisp(ni), float), np.array(ops.nodeDisp(nj), float))
    ops.wipe()
    for grupo in res.values():
        for v in grupo.values():
            if not np.all(np.isfinite(v)):
                raise ErrorAnalisis('resultado no finito: revise el modelo (mecanismo o nodo mal apoyado)')
    return res


def _combinar(partes):
    """Superposicion lineal: partes = [(factor, resultado)]."""
    out = {'nodos': {}, 'barras': {}, 'reac': {}, 'extremos': {}}
    for f, res in partes:
        for clave in ('nodos', 'barras', 'reac'):
            for i, v in res[clave].items():
                out[clave][i] = out[clave].get(i, 0.0) + f * v
        for i, (ui, uj) in res['extremos'].items():
            a, b = out['extremos'].get(i, (0.0, 0.0))
            out['extremos'][i] = (a + f * ui, b + f * uj)
    return out


def _residuo(dib, props, cargas_nodales, pp, res):
    """Equilibrio global de fuerzas: suma de reacciones + cargas aplicadas + peso propio (debe ser ~0)."""
    F = np.zeros(3)
    for v in cargas_nodales.values():
        F += np.array(v[:3], float)
    if pp:
        L = [np.linalg.norm(np.array(dib.nodos[b['n2']]) - np.array(dib.nodos[b['n1']])) * 100.0
             for b in dib.barras]
        F += sum(props[i]['masa'] / 100.0 * L[i] for i in range(len(L))) * GRAVEDAD
    R = np.zeros(3)
    for v in res['reac'].values():
        R += v[:3]
    return float(np.linalg.norm(R + F))


def _fuerzas_extremo(f):
    """Fuerzas de un extremo en unidades de salida: kgf y kgf·m."""
    return [f[0], f[1], f[2], f[3] / 100.0, f[4] / 100.0, f[5] / 100.0]


def _tablas(dib, casos, rep_barras, rep_nodos, id_barra, id_de_indice, props=None, fpp=None):
    filas_b, filas_n, filas_r = [], [], []
    for nombre, tipo, res in casos:
        for i in sorted(rep_barras):
            b = dib.barras[i]
            f = res['barras'][i]
            fila = [nombre, tipo, id_barra.get(i, i), id_de_indice[b['n1']], id_de_indice[b['n2']],
                    b['elemento'], b['perfil']] + _fuerzas_extremo(f[:6]) + _fuerzas_extremo(f[6:])
            if props is not None:
                mz, my = momentos_maximos_viga(dib, props, i, res, fpp[nombre])
                fila += [mz / 100.0, my / 100.0]                       # kgf cm -> kgf m
            filas_b.append(fila)
        for i in sorted(rep_nodos):
            d = res['nodos'][i]
            filas_n.append([nombre, tipo, id_de_indice[i], d[0] * 10, d[1] * 10, d[2] * 10,
                            d[3], d[4], d[5]])
            if i in dib.apoyos:
                r = res['reac'][i]
                filas_r.append([nombre, tipo, id_de_indice[i], etiqueta_restricciones(dib.apoyos[i]), r[0], r[1], r[2],
                                r[3] / 100.0, r[4] / 100.0, r[5] / 100.0])
    cab_b = ['CASO', 'TIPO', 'BARRA', 'NODO I', 'NODO J', 'ELEMENTO', 'PERFIL'] + \
            [f'{e} I ({u})' for e, u in zip(ETIQUETA, ['kgf', 'kgf', 'kgf', 'kgf·m', 'kgf·m', 'kgf·m'])] + \
            [f'{e} J ({u})' for e, u in zip(ETIQUETA, ['kgf', 'kgf', 'kgf', 'kgf·m', 'kgf·m', 'kgf·m'])] + \
            (['MZ MAX EN EL TRAMO (kgf·m)', 'MY MAX EN EL TRAMO (kgf·m)'] if props is not None else [])
    cab_n = ['CASO', 'TIPO', 'NODO', 'UX (mm)', 'UY (mm)', 'UZ (mm)', 'RX (rad)', 'RY (rad)', 'RZ (rad)']
    cab_r = ['CASO', 'TIPO', 'NODO', 'APOYO', 'FX (kgf)', 'FY (kgf)', 'FZ (kgf)', 'MX (kgf·m)', 'MY (kgf·m)',
             'MZ (kgf·m)']
    return (pd.DataFrame(filas_b, columns=cab_b), pd.DataFrame(filas_n, columns=cab_n),
            pd.DataFrame(filas_r, columns=cab_r))


UNIDAD_ESF = dict(zip(ETIQUETA, ['kgf', 'kgf', 'kgf', 'kgf·m', 'kgf·m', 'kgf·m']))


def tabla_maximos(barras):
    """Maximo y minimo de cada esfuerzo entre los extremos I y J, por barra y caso (solo barras REPORTAR = SI)."""
    cab = ['CASO', 'TIPO', 'BARRA', 'ELEMENTO', 'PERFIL']
    for e in ETIQUETA:
        cab += [f'{e} MAX ({UNIDAD_ESF[e]})', f'{e} MIN ({UNIDAD_ESF[e]})']
    filas = []
    for _, r in barras.iterrows():
        fila = [r['CASO'], r['TIPO'], r['BARRA'], r['ELEMENTO'], r['PERFIL']]
        for e in ETIQUETA:
            v = [r[f'{e} I ({UNIDAD_ESF[e]})'], r[f'{e} J ({UNIDAD_ESF[e]})']]
            fila += [max(v), min(v)]
        filas.append(fila)
    return pd.DataFrame(filas, columns=cab)


def tabla_deformada(dib, casos, id_de_indice):
    """Coordenadas de todos los nodos por caso: original, desplazamientos (mm, rad) y posicion deformada (m)."""
    cab = ['CASO', 'TIPO', 'NODO', 'X (m)', 'Y (m)', 'Z (m)', 'UX (mm)', 'UY (mm)', 'UZ (mm)',
           'RX (rad)', 'RY (rad)', 'RZ (rad)', 'X def (m)', 'Y def (m)', 'Z def (m)']
    filas = []
    for nombre, tipo, res in casos:
        for i, p in enumerate(dib.nodos):
            d = res['nodos'][i]
            filas.append([nombre, tipo, id_de_indice[i], p[0], p[1], p[2],
                          d[0] * 10, d[1] * 10, d[2] * 10, d[3], d[4], d[5],
                          p[0] + d[0] / 100, p[1] + d[1] / 100, p[2] + d[2] / 100])
    return pd.DataFrame(filas, columns=cab)


def _arco(ax, centro, a, b, r, color, texto):
    """Arco de momento: positivo alrededor de a x b (regla de la mano derecha)."""
    th = np.linspace(0.3, 2.4, 40)
    pts = centro + r * (np.outer(np.cos(th), a) + np.outer(np.sin(th), b))
    ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=color, lw=2.2)
    ax.quiver(*pts[-2], *(pts[-1] - pts[-2]), color=color, arrow_length_ratio=0.6, lw=2.2)
    ax.text(*(centro + 1.45 * r * (a + b) / 2), texto, color=color, fontsize=9)


def figura_ejes_locales(ruta):
    """PNG: ejes locales de una barra de ejemplo (viga a lo largo de X con peralte vertical), fuerzas en los
    extremos I y J y signos. Sirve de referencia para leer la hoja BARRAS."""
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(13, 5.8))
    ax = fig.add_axes([0.0, 0.0, 0.56, 1.0], projection='3d')
    txt = fig.add_axes([0.58, 0.02, 0.42, 0.96]); txt.axis('off')
    I, J = np.array([0.0, 0.0, 0.0]), np.array([2.0, 0.0, 0.0])
    x_loc, y_loc, z_loc = np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), np.array([0, -1.0, 0])
    ax.plot(*zip(I, J), color='#9e9e9e', lw=9, solid_capstyle='round')
    ax.text(-0.15, 0.0, -0.3, 'I', fontsize=13, weight='bold')
    ax.text(2.15, 0.0, -0.3, 'J', fontsize=13, weight='bold')
    L = 0.75
    for vec, color, texto in [(x_loc, '#d62728', 'x local'), (y_loc, '#2ca02c', 'y local (eje fuerte)'),
                              (z_loc, '#1f77b4', 'z local (eje debil)')]:
        ax.quiver(*I, *vec * L, color=color, lw=2.6, arrow_length_ratio=0.18)
        pos = I + vec * (L + 0.1) + (np.array([-0.45, 0.0, -0.22]) if vec[2] < 0 else
                                      (np.array([0.0, 0.0, 0.12]) if vec[1] > 0 else np.array([0.12, -0.2, 0.0])))
        ax.text(*pos, texto, color=color, fontsize=10, weight='bold')
    O = np.array([-1.9, -1.0, -0.95])
    for vec, texto in [((1, 0, 0), 'X'), ((0, 1, 0), 'Y'), ((0, 0, 1), 'Z')]:
        ax.quiver(*O, *(np.array(vec) * 0.6), color='#555555', lw=1.8, arrow_length_ratio=0.2)
        ax.text(*(O + np.array(vec) * 0.7), texto + ' global', color='#555555', fontsize=10)
    # fuerzas en los extremos (flecha = sentido positivo del eje local)
    ax.quiver(*I, 0.45, 0, 0, color='#444444', lw=1.4, arrow_length_ratio=0.3)
    ax.text(0.2, 0.0, 0.22, 'N(I)', fontsize=9, color='#444444')
    ax.quiver(*J, 0.45, 0, 0, color='#444444', lw=1.4, arrow_length_ratio=0.3)
    ax.text(2.62, 0.0, 0.28, 'N(J)', fontsize=9, color='#444444')
    ax.quiver(*J, 0, 0.45, 0, color='#444444', lw=1.4, arrow_length_ratio=0.3)
    ax.text(2.1, 0.5, 0.0, 'Vy(J)', fontsize=9, color='#444444')
    # momentos a mitad de la barra: Mz alrededor de z (fuerte), My alrededor de y (debil)
    M = np.array([1.0, 0.0, 0.0])
    _arco(ax, M, x_loc, y_loc, 0.3, '#6a1b9a', 'Mz (fuerte)')
    _arco(ax, M, z_loc, x_loc, 0.3, '#ef6c00', 'My (debil)')
    ax.set_xlim(-1.5, 3.1); ax.set_ylim(-1.0, 0.9); ax.set_zlim(-0.8, 1.1)
    ax.set_box_aspect((4.6, 1.9, 1.9)); ax.set_axis_off(); ax.view_init(elev=28, azim=-38)
    lineas = [
        ('EJES LOCALES Y SIGNOS (hoja BARRAS)', True),
        ('x: eje de la barra, de I a J.', False),
        ('y: eje fuerte (peralte del perfil): cortante fuerte Vy, momento fuerte Mz.', False),
        ('z: eje debil: cortante debil Vz, momento debil My.', False),
        ('T: torsion, alrededor de x.     N: axial.', False),
        ('', False),
        ('SIGNOS DE LOS EXTREMOS I y J', True),
        ('Un valor positivo es la fuerza o el momento que el nudo ejerce sobre la barra', False),
        ('en ese extremo, en el sentido del eje local (momentos: regla de la mano derecha).', False),
        ('', False),
        ('N(I) positivo = compresion.     N(J) positivo = traccion.', True),
        ('Barra traccionada: N(I) < 0 y N(J) > 0.', False),
        ('', False),
        ('Ejes globales X, Y, Z (gris). Los desplazamientos van en ejes globales.', False),
    ]
    for k, (linea, negrita) in enumerate(lineas):
        txt.text(0.0, 0.95 - k * 0.068, linea, fontsize=10.5 if negrita else 10,
                 weight='bold' if negrita else 'normal', transform=txt.transAxes)
    fig.savefig(ruta, dpi=110)
    plt.close(fig)
    return ruta


def _lineas(barras, P):
    xs, ys, zs = [], [], []
    for b in barras:
        a, c = P[b['n1']], P[b['n2']]
        xs += [a[0], c[0], None]; ys += [a[1], c[1], None]; zs += [a[2], c[2], None]
    return xs, ys, zs


def figura_deformada(dib, casos, id_de_indice, escala=None):
    """Figura 3D interactiva: deformada por estado y combinacion (botones). Sin escala dada, la escala hace que el
    mayor desplazamiento mida el 10 % de la dimension del modelo. Las barras se dibujan entre extremos deformados."""
    import plotly.graph_objects as go
    P0 = np.array(dib.nodos, float)
    tam = max(max(float(np.ptp(P0[:, k])) for k in range(3)), 1.0)
    U = {nombre: np.array([res['nodos'][i][:3] for i in range(len(P0))], float) / 100.0 for nombre, _, res in casos}
    dmax = max((float(np.max(np.linalg.norm(u, axis=1))) for u in U.values()), default=0.0)
    if escala is None:
        escala = 0.1 * tam / dmax if dmax > 0 else 1.0
    fig = go.Figure()
    xs, ys, zs = _lineas(dib.barras, P0)
    fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='#bbbbbb', width=3, dash='dash'),
                               name='sin carga (original)', hoverinfo='skip'))
    n = len(casos)
    for k, (nombre, tipo, _) in enumerate(casos):
        P = P0 + escala * U[nombre]
        xs, ys, zs = _lineas(dib.barras, P)
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color='#1f77b4', width=6),
                                   name=f'{nombre} ({tipo})', visible=(k == 0), hoverinfo='skip'))
        fig.add_trace(go.Scatter3d(x=P[:, 0], y=P[:, 1], z=P[:, 2], mode='markers+text',
                                   marker=dict(size=3, color='black'),
                                   text=[f'N{id_de_indice[i]}' for i in range(len(P))], textposition='top center',
                                   hovertext=[f'nodo {id_de_indice[i]}' for i in range(len(P))], hoverinfo='text',
                                   name=f'nodos {nombre}', visible=(k == 0)))
    botones = []
    for k, (nombre, tipo, _) in enumerate(casos):
        vis = [True] + [(t // 2) == k for t in range(2 * n)]
        botones.append(dict(label=nombre, method='update',
                            args=[{'visible': vis},
                                  {'title': f'Deformada: {nombre} ({tipo}), escala x{escala:.3g}'}]))
    titulo = (f'Deformada: {casos[0][0]} ({casos[0][1]}), escala x{escala:.3g}' if casos
              else 'Sin casos para mostrar')
    fig.update_layout(title=titulo,
                      updatemenus=[dict(buttons=botones, direction='down', x=0.0, xanchor='left', y=1.14,
                                        yanchor='top')],
                      scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'),
                      margin=dict(l=0, r=0, t=70, b=0), height=760)
    return fig


def _escribir(ruta, bloques, resumen_filas, png):
    from openpyxl.drawing.image import Image as XLImage
    with pd.ExcelWriter(ruta, engine='openpyxl') as w:
        pd.DataFrame(resumen_filas, columns=['DATO', 'VALOR']).to_excel(w, sheet_name='RESUMEN', index=False)
        for nombre in ['BARRAS', 'NODOS', 'REACCIONES', 'MAXIMOS_BARRAS', 'DEFORMADA']:
            bloques[nombre].to_excel(w, sheet_name=nombre, index=False)
        hoja_res = w.book['RESUMEN']
        if png and os.path.exists(png):
            img = XLImage(png)
            img.width, img.height = 1040, 448
            hoja_res.add_image(img, 'D2')
        for hoja in w.book.worksheets:
            for col in hoja.columns:
                largo = max(len(str(c.value)) if c.value is not None else 0 for c in col)
                hoja.column_dimensions[col[0].column_letter].width = min(max(10, largo + 2), 40)
            hoja.freeze_panes = 'A2'
            if hoja.title == 'RESUMEN':
                hoja.column_dimensions['A'].width = 48
                hoja.column_dimensions['B'].width = 90


def clase_combinacion(nombre, combinaciones, tipos):
    """Clase de una combinacion segun el TIPO (hoja ESTADOS) de sus estados con factor no nulo: 'viento' si incluye W
    (no entra al diseno: para el diseno solo aplica el sismo), 'sismo' si incluye E, 'gravitacional' si solo D y L,
    'otra' si algun estado no tiene un TIPO reconocido."""
    t = [tipos.get(e) for e, f in combinaciones.get(nombre, {}).items() if f != 0]
    if 'W' in t:
        return 'viento'
    if 'E' in t:
        return 'sismo'
    if t and all(x in ('D', 'L') for x in t):
        return 'gravitacional'
    return 'otra'


def _deflexion_viga(dib, props, i, res, fpp, xi):
    """Desviacion vertical (Z global, cm) de la viga i a lo largo de su eje (xi = 0 a 1), respecto a la cuerda entre
    extremos. Euler-Bernoulli exacto entre extremos: giros de extremo del elemento (res['extremos']) mas la carga propia
    uniforme, con factor fpp (suma de factores de los estados con PESO PROPIO = SI en la combinacion)."""
    p1 = np.array(dib.nodos[dib.barras[i]['n1']], float)
    p2 = np.array(dib.nodos[dib.barras[i]['n2']], float)
    L = float(np.linalg.norm(p2 - p1)) * 100.0
    _, yl, zl = ejes_locales(dib, i)
    w = props[i]['masa'] / 100.0 * GRAVEDAD                       # kgf/cm, igual que en _modelo
    E, Iy, Iz = props[i]['E'], props[i]['Iy'], props[i]['Iz']
    h1 = xi - 2.0 * xi ** 2 + xi ** 3                              # forma de Hermite: giro en el extremo i
    h2 = -xi ** 2 + xi ** 3                                        # forma de Hermite: giro en el extremo j
    burbuja = xi ** 2 * (1.0 - xi) ** 2                            # solucion particular de la carga uniforme
    ui, uj = res['extremos'][i]
    ti, tj = ui[3:6], uj[3:6]
    # plano local x-y (v): giro theta_z = dv/dx, rigidez E*Iz.  plano local x-z (w): theta_y = -dw/dx, rigidez E*Iy
    # Hermite: el termino de traslacion de los extremos no es lineal. Respecto a la cuerda queda g(xi)*(v_i - v_j),
    # con g = xi - 3 xi^2 + 2 xi^3 (corrige H-02: antes solo se usaban los giros).
    g = xi - 3.0 * xi ** 2 + 2.0 * xi ** 3
    v_ext = (ui[:3] @ yl) - (uj[:3] @ yl)
    w_ext = (ui[:3] @ zl) - (uj[:3] @ zl)
    v = L * ((ti @ zl) * h1 + (tj @ zl) * h2) + g * v_ext + fpp * (w @ yl) * L ** 4 * burbuja / (24.0 * E * Iz)
    wz = L * (-(ti @ yl) * h1 - (tj @ yl) * h2) + g * w_ext + fpp * (w @ zl) * L ** 4 * burbuja / (24.0 * E * Iy)
    return v * yl[2] + wz * zl[2]


def _curvatura_max(v_i, v_j, s_i, s_j, q, EI, L):
    """Maximo |M| = EI * v'' a lo largo de una viga (Euler-Bernoulli exacto entre extremos, malla de 401 puntos).
    v_i, v_j: desplazamientos transversales de los extremos (cm); s_i, s_j: pendientes dv/dx; q: carga uniforme (kgf/cm)
    en el mismo plano; EI en kgf cm2. Devuelve kgf cm."""
    xi = np.linspace(0.0, 1.0, 401)
    x = xi * L
    vpp = ((-6.0 + 12.0 * xi) * v_i + (6.0 - 12.0 * xi) * v_j) / L ** 2 \
        + s_i * (-4.0 + 6.0 * xi) / L + s_j * (-2.0 + 6.0 * xi) / L \
        + q * (12.0 * x ** 2 - 12.0 * L * x + 2.0 * L ** 2) / (24.0 * EI)
    return float(np.max(np.abs(EI * vpp)))


def momentos_maximos_viga(dib, props, i, res, fpp):
    """Momento maximo en el tramo (no solo en los extremos) de la barra i para una combinacion (corrige H-01).
    Devuelve (Mz_max, My_max) en kgf cm, con el peso propio de la combinacion (factor fpp)."""
    p1 = np.array(dib.nodos[dib.barras[i]['n1']], float)
    p2 = np.array(dib.nodos[dib.barras[i]['n2']], float)
    L = float(np.linalg.norm(p2 - p1)) * 100.0
    _, yl, zl = ejes_locales(dib, i)
    w = props[i]['masa'] / 100.0 * GRAVEDAD
    E, Iy, Iz = props[i]['E'], props[i]['Iy'], props[i]['Iz']
    ui, uj = res['extremos'][i]
    ti, tj = ui[3:6], uj[3:6]
    # plano x-y: flexion Mz con EI = E Iz; v = u.yl, pendiente dv/dx = theta_z = t.zl
    Mz = _curvatura_max(ui[:3] @ yl, uj[:3] @ yl, ti @ zl, tj @ zl, fpp * (w @ yl), E * Iz, L)
    # plano x-z: flexion My con EI = E Iy; w = u.zl, pendiente dw/dx = -theta_y = -(t.yl)
    My = _curvatura_max(ui[:3] @ zl, uj[:3] @ zl, -(ti @ yl), -(tj @ yl), fpp * (w @ zl), E * Iy, L)
    return Mz, My


def flechas_vigas(dib, props, casos, combinaciones, estados_pp, clase):
    """Flecha vertical maxima de cada viga horizontal (desviacion respecto a la cuerda entre sus extremos) sobre las
    combinaciones gravitacionales. Devuelve {barra: {'L_cm', 'max_mm', 'comb', 'xi'}}; xi = posicion del maximo (0 a 1)."""
    xi = np.linspace(0.0, 1.0, 401)
    out = {}
    for i, b in enumerate(dib.barras):
        p1 = np.array(dib.nodos[b['n1']], float)
        p2 = np.array(dib.nodos[b['n2']], float)
        L = float(np.linalg.norm(p2 - p1)) * 100.0
        if abs(p2[2] - p1[2]) * 100.0 > 0.1 * L:
            continue                                               # columnas y elementos inclinados: no es viga
        mejor = None
        for nombre, tipo, res in casos:
            # DECISION D2 (abierta): la flecha se evalua solo en combinaciones gravitacionales (D y L, total). Alternativa: solo carga viva.
            if tipo != 'COMBINACION' or clase.get(nombre) != 'gravitacional':
                continue
            fpp = sum(f for e, f in combinaciones[nombre].items() if estados_pp.get(e))
            d = np.abs(_deflexion_viga(dib, props, i, res, fpp, xi))
            k = int(np.argmax(d))
            if mejor is None or d[k] > mejor[0]:
                mejor = (float(d[k]), nombre, float(xi[k]))
        if mejor is not None:
            out[i] = {'L_cm': L, 'max_mm': mejor[0] * 10.0, 'comb': mejor[1], 'xi': mejor[2]}
    return out


def correr(dib, materiales, estados, rep_barras, rep_nodos, id_barra, id_de_indice, ruta_salida):
    """Resuelve todos los estados y combinaciones y escribe el Excel de resultados.
    materiales: {nombre: {'E', 'nu'}}; estados: [(nombre, peso_propio)]; rep_barras / rep_nodos: indices a reportar.
    Devuelve (bloques, equilibrio, casos): tablas, residuo de equilibrio por estado (kgf) y resultados por caso
    (todos los nodos, para la deformada)."""
    _verificar_conectividad(dib)
    props = propiedades_barras(dib, materiales, id_barra)
    cargas = getattr(dib, 'cargas', {}) or {}
    combinaciones = getattr(dib, 'combinaciones', {}) or {}
    tipos = getattr(dib, 'estados_tipo', {}) or {}
    # DECISION D13 (abierta): viento fuera de esta version: se omiten los estados W y las combinaciones que lo incluyen.
    estados = [(n, pp) for n, pp in estados if tipos.get(n) != 'W']
    clase_todas = {n: clase_combinacion(n, combinaciones, tipos) for n in combinaciones}
    combinaciones = {n: f for n, f in combinaciones.items() if clase_todas[n] != 'viento'}
    resultados, equilibrio, casos, resumen = {}, [], [], []
    for nombre, pp in estados:
        cn = cargas.get(nombre, {})
        resultados[nombre] = _resolver(dib, props, cn, pp)
        equilibrio.append((nombre, _residuo(dib, props, cn, pp, resultados[nombre])))
        casos.append((nombre, 'ESTADO', resultados[nombre]))
        resumen.append([f'Estado {nombre}', f'peso propio {"SI" if pp else "NO"}; cargas en {len(cn)} nodos'])
    for nombre, factores in combinaciones.items():
        partes = [(f, resultados[e]) for e, f in factores.items() if e in resultados]
        if not partes:
            continue
        casos.append((nombre, 'COMBINACION', _combinar(partes)))
        resumen.append([f'Combinacion {nombre}', ' + '.join(f'{f:g}·{e}' for e, f in factores.items())])
    clase = {nombre: clase_combinacion(nombre, combinaciones, tipos) for nombre in combinaciones}
    dib.clase_combinacion = clase_todas                 # clase de TODAS las combinaciones (la memoria excluye las de viento)
    # DECISION D11 (abierta): el diseno usa las combinaciones de servicio ASD definidas por el usuario (sin viento); E entra si esta definido.
    casos_diseno = [c for c in casos if not (c[1] == 'COMBINACION' and clase.get(c[0]) == 'viento')]
    dib.flechas = flechas_vigas(dib, props, casos, combinaciones, dict(estados), clase)
    pp_map = dict(estados)
    fpp_caso = {n: (1.0 if pp_map.get(n) else 0.0) for n, _ in estados}
    fpp_caso.update({n: sum(f for e, f in combinaciones[n].items() if pp_map.get(e)) for n in combinaciones})
    cab_b, cab_n, cab_r = _tablas(dib, casos, rep_barras, rep_nodos, id_barra, id_de_indice, props, fpp_caso)
    bloques = {'BARRAS': cab_b, 'NODOS': cab_n, 'REACCIONES': cab_r,
               'MAXIMOS_BARRAS': tabla_maximos(cab_b),
               'DEFORMADA': tabla_deformada(dib, casos, id_de_indice)}
    cabecera = [
        ['Unidades', 'fuerzas kgf; momentos kgf·m; desplazamientos mm; giros rad'],
        ['Barras', 'N axial; Vy cortante fuerte; Vz cortante debil; T torsion; My momento debil; '
                   'Mz momento fuerte. Ejes locales y signos: figura a la derecha'],
        ['Signos', 'fuerzas que el nudo ejerce sobre la barra en cada extremo, ejes locales (OpenSees localForces). '
                   'Barra traccionada: N en I < 0 y N en J > 0'],
        ['Reacciones', 'fuerzas que recibe el apoyo desde la estructura (FZ positivo hacia arriba)'],
        ['MAXIMOS_BARRAS', 'maximo y minimo de cada esfuerzo entre los extremos I y J, por barra y caso'],
        ['DEFORMADA', 'coordenadas de todos los nodos por caso: original, desplazamientos y posicion deformada'],
        ['Barras y nodos reportados', f'{len(rep_barras)} barras y {len(rep_nodos)} nodos marcados REPORTAR = SI'],
        ['Viento', 'no se considera en esta version: se omiten los estados y combinaciones con W'],
    ]
    for nombre, residuo in equilibrio:
        cabecera.append([f'Equilibrio estado {nombre}', f'residuo de fuerzas {residuo:.3g} kgf'])
    bloques['DISENO_BARRAS'] = _tablas(dib, casos_diseno, set(range(len(dib.barras))), set(), id_barra, id_de_indice,
                                       props, fpp_caso)[0]
    png = figura_ejes_locales('ejes_locales.png')
    _escribir(ruta_salida, bloques, cabecera + resumen, png)
    return bloques, equilibrio, casos


def correr_desde_planilla(dib, materiales_filas, estados_df, nodos, barras, id_barra, id_de_indice, ruta_salida):
    """Punto de entrada del notebook: toma los datos de la planilla ya leida y valida (bloque 7).
    materiales_filas es None si la planilla no tiene la hoja MATERIALES (no se usan valores de ejemplo)."""
    if materiales_filas is None:
        raise ErrorAnalisis('la planilla no tiene la hoja MATERIALES con las columnas E y NU: '
                            'use la plantilla nueva (bloque 6) y vuelva a llenarla.')
    materiales = materiales_desde_filas(materiales_filas)
    estados = estados_desde_df(estados_df)
    marcados_b = {int(float(r['ID'])) for _, r in barras.iterrows() if _marcado(r.get('REPORTAR'))}
    marcados_n = {int(float(r['ID'])) for _, r in nodos.iterrows() if _marcado(r.get('REPORTAR'))}
    rep_barras = {i for i, id_ in id_barra.items() if id_ in marcados_b}
    rep_nodos = {i for i, id_ in id_de_indice.items() if id_ in marcados_n}
    dib.estados_tipo = {str(r['NOMBRE']).strip(): str(r['TIPO']).strip().upper()
                        for _, r in estados_df.iterrows()
                        if isinstance(r['NOMBRE'], str) and isinstance(r['TIPO'], str)}
    return correr(dib, materiales, estados, rep_barras, rep_nodos, id_barra, id_de_indice, ruta_salida)
