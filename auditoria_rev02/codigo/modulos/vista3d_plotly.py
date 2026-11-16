"""
FIGURA 3D INTERACTIVA (plotly): gira, acerca y muestra datos al pasar el cursor. Funciona en Kaggle porque
plotly embebe su propio motor en la salida; no requiere widgets de matplotlib.

Contenido:
  - barras por tipo de elemento (color), con ID, perfil, conexiones y eje fuerte al pasar el cursor
  - seccion envolvente de cada perfil (caja de d x bf) en la barra, ampliada ESCALA_SECCION
  - flecha = eje fuerte (direccion del peralte) en el punto medio de cada barra
  - circulo abierto = extremo rotulado; cuadrado = apoyo empotrado; rombo = apoyo rotulado
"""
import numpy as np
import plotly.graph_objects as go
from orientacion_gerdau import contorno, ejes_locales, dimensiones
from dibujo_directo import marca_apoyo

COLOR_ELEMENTO = {'COLUMNA': '#1f77b4', 'VIGA': '#2ca02c', 'ARRIOSTRE': '#d62728', 'DIAGONAL': '#ff7f0e'}


def _flecha(fig, origen, vec, color, nombre, tam_cono):
    """Flecha 3D: linea con etiqueta y cono en la punta."""
    tip = origen + vec
    fig.add_trace(go.Scatter3d(x=[origen[0], tip[0]], y=[origen[1], tip[1]], z=[origen[2], tip[2]],
                               mode='lines+text', line=dict(color=color, width=7), text=['', nombre],
                               textposition='top center', textfont=dict(color=color, size=12),
                               name=nombre, hoverinfo='skip'))
    fig.add_trace(go.Cone(x=[tip[0]], y=[tip[1]], z=[tip[2]], u=[vec[0]], v=[vec[1]], w=[vec[2]],
                          anchor='tip', sizemode='absolute', sizeref=tam_cono,
                          colorscale=[[0, color], [1, color]], showscale=False, hoverinfo='skip',
                          showlegend=False))


def figura_3d(dib, id_de_indice, escala_seccion=2.5, titulo=None, ejes=True, barra_ejemplo=None):
    """Devuelve una go.Figure 3D del modelo. escala_seccion solo amplia la seccion dibujada, no el calculo."""
    fig = go.Figure()
    nodos = np.array(dib.nodos, float)
    id_barra = getattr(dib, 'id_barra_de_indice', {}) or {}

    def rotulada(b):
        return b['conexion_i'] == 'rotulado' or b['conexion_j'] == 'rotulado'

    def texto_barra(i, b):
        return (f"Barra ID {id_barra.get(i, i)} (nodos N{id_de_indice.get(b['n1'], '?')}-N{id_de_indice.get(b['n2'], '?')})"
                f"<br>{b['elemento']} {b['perfil']}"
                f"<br>conexion I: {b['conexion_i']}, J: {b['conexion_j']}"
                f"<br>eje fuerte: {'por defecto' if b['eje_fuerte'] is None else np.round(b['eje_fuerte'], 3).tolist()}")

    # --- barras con extremo rotulado: linea discontinua morada (se ven distintas de las continuas) ---
    xs, ys, zs, textos = [], [], [], []
    for i, b in enumerate(dib.barras):
        if not rotulada(b):
            continue
        p1, p2 = nodos[b['n1']], nodos[b['n2']]
        info = texto_barra(i, b)
        xs += [p1[0], p2[0], None]; ys += [p1[1], p2[1], None]; zs += [p1[2], p2[2], None]
        textos += [info, info, None]
    if xs:
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines',
                                   line=dict(color='#6a1b9a', width=9, dash='dash'),
                                   name='barra con extremo rotulado (linea discontinua)',
                                   text=textos, hoverinfo='text'))

    # --- barras continuas por tipo de elemento (una traza por tipo, con huecos entre barras) ---
    for elem, color in COLOR_ELEMENTO.items():
        xs, ys, zs, textos = [], [], [], []
        for i, b in enumerate(dib.barras):
            if b['elemento'] != elem or rotulada(b):
                continue
            p1, p2 = nodos[b['n1']], nodos[b['n2']]
            info = texto_barra(i, b)
            xs += [p1[0], p2[0], None]; ys += [p1[1], p2[1], None]; zs += [p1[2], p2[2], None]
            textos += [info, info, None]
        if xs:
            fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines', line=dict(color=color, width=7),
                                       name=elem, text=textos, hoverinfo='text'))

    # --- secciones envolventes (caja d x bf en ambos extremos) y eje fuerte ---
    for i, b in enumerate(dib.barras):
        caja = contorno(dib, i, escala_seccion)
        if not caja:
            continue
        p1, p2 = nodos[b['n1']], nodos[b['n2']]
        x_loc, y_loc, z_loc = ejes_locales(dib, i)
        d, bf = dimensiones(b['perfil'])
        d *= escala_seccion; bf *= escala_seccion
        vertices = []
        for p in (p1, p2):
            for sy, sz in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
                q = p + sy * (d / 2) * y_loc + sz * (bf / 2) * z_loc
                vertices.append(q)
        vertices = np.array(vertices)
        fig.add_trace(go.Mesh3d(x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2], alphahull=0,
                                color=COLOR_ELEMENTO[b['elemento']], opacity=0.12 if rotulada(b) else 0.35, flatshading=True,
                                name=f'seccion {b["perfil"]}', showlegend=False, hoverinfo='skip'))
        pm = (p1 + p2) / 2
        largo = 0.6 * d
        tip = pm + y_loc * largo
        fig.add_trace(go.Scatter3d(x=[pm[0], tip[0]], y=[pm[1], tip[1]], z=[pm[2], tip[2]], mode='lines',
                                   line=dict(color='black', width=4), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Cone(x=[tip[0]], y=[tip[1]], z=[tip[2]], u=[y_loc[0]], v=[y_loc[1]], w=[y_loc[2]],
                              anchor='tip', sizemode='absolute', sizeref=0.12,
                              colorscale=[[0, 'black'], [1, 'black']], showscale=False, hoverinfo='skip',
                              showlegend=False))

    # --- extremos rotulados (circulo abierto) ---
    xr, yr, zr = [], [], []
    for b in dib.barras:
        for idx, c in [(b['n1'], b['conexion_i']), (b['n2'], b['conexion_j'])]:
            if c == 'rotulado':
                xr.append(nodos[idx][0]); yr.append(nodos[idx][1]); zr.append(nodos[idx][2])
    if xr:
        fig.add_trace(go.Scatter3d(x=xr, y=yr, z=zr, mode='markers',
                                   marker=dict(symbol='circle-open', size=9, color='black', line=dict(width=3)),
                                   name='extremo rotulado (circulo abierto)', hoverinfo='skip'))

    # --- nodos con IDs y apoyos ---
    nodos_id = [(i, nodos[i]) for i in range(len(nodos))]
    # IDs de barra (B) en el punto medio de cada barra; se pueden ocultar desde la leyenda
    mx = [(nodos[b['n1']][0] + nodos[b['n2']][0]) / 2 for b in dib.barras]
    my = [(nodos[b['n1']][1] + nodos[b['n2']][1]) / 2 for b in dib.barras]
    mz = [(nodos[b['n1']][2] + nodos[b['n2']][2]) / 2 for b in dib.barras]
    fig.add_trace(go.Scatter3d(x=mx, y=my, z=mz, mode='text',
                               text=[f"B{id_barra.get(i, i)}" for i in range(len(dib.barras))],
                               textfont=dict(size=12, color='#6a1b9a'), name='ID de barra (B)',
                               hoverinfo='skip'))
    fig.add_trace(go.Scatter3d(x=nodos[:, 0], y=nodos[:, 1], z=nodos[:, 2], mode='markers+text',
                               marker=dict(size=3, color='black'),
                               text=[f"N{id_de_indice.get(i, i)}" for i in range(len(nodos))],
                               textposition='top center', textfont=dict(size=12, color='black'),
                               name='ID de nodo (N)', hoverinfo='text',
                               hovertext=[f'nodo ID {id_de_indice.get(i, i)}<br>X {p[0]:g}  Y {p[1]:g}  Z {p[2]:g}'
                                          for i, p in nodos_id]))
    fig.add_trace(go.Scatter3d(x=[None], y=[None], z=[None], mode='lines', line=dict(color='black', width=4),
                               name='eje fuerte (flecha)', hoverinfo='skip'))
    for tipo, simbolo, color, nombre in [('empotrado', 'square', '#e67e22', 'apoyo empotrado (cuadrado)'),
                                         ('rotulado', 'diamond', '#e67e22', 'apoyo rotulado (rombo)')]:
        idx = [i for i, t in dib.apoyos.items() if marca_apoyo(t) == tipo or (tipo == 'rotulado' and marca_apoyo(t) == 'giro')]
        if idx:
            fig.add_trace(go.Scatter3d(x=nodos[idx, 0], y=nodos[idx, 1], z=nodos[idx, 2], mode='markers',
                                       marker=dict(symbol=simbolo, size=7, color=color), name=nombre,
                                       hoverinfo='skip'))

    # --- ejes globales X, Y, Z y ejes locales de una barra de ejemplo (x = de I a J, y = eje fuerte, z) ---
    if ejes and len(nodos):
        lo, hi = nodos.min(axis=0), nodos.max(axis=0)
        tam = max(float(np.max(hi - lo)), 1.0)
        o = lo - 0.15 * tam
        for vec, nombre in [((1, 0, 0), 'X global'), ((0, 1, 0), 'Y global'), ((0, 0, 1), 'Z global')]:
            _flecha(fig, o, np.array(vec, float) * 0.25 * tam, '#555555', nombre, 0.06 * tam)
        if barra_ejemplo is None:
            vigas = [i for i, b in enumerate(dib.barras) if b['elemento'] == 'VIGA']
            barra_ejemplo = vigas[0] if vigas else 0
        if dib.barras:
            b = dib.barras[barra_ejemplo]
            p1, p2 = nodos[b['n1']], nodos[b['n2']]
            x_loc, y_loc, z_loc = ejes_locales(dib, barra_ejemplo)
            c = (p1 + p2) / 2
            l = 0.2 * tam
            _flecha(fig, c, x_loc * l, '#d62728', 'x local (I a J)', 0.06 * tam)
            _flecha(fig, c, y_loc * l, '#2ca02c', 'y local (eje fuerte)', 0.06 * tam)
            _flecha(fig, c, z_loc * l, '#1f77b4', 'z local (eje debil)', 0.06 * tam)
            for pt, etiqueta in [(p1, 'I'), (p2, 'J')]:
                fig.add_trace(go.Scatter3d(x=[pt[0]], y=[pt[1]], z=[pt[2]], mode='text', text=[etiqueta],
                                           textfont=dict(size=14, color='black'), hoverinfo='skip',
                                           showlegend=False))

    fig.update_layout(
        title=titulo or f'Modelo 3D: secciones x{escala_seccion:g}; flecha = eje fuerte (ver leyenda)',
        scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data',
                   camera=dict(eye=dict(x=1.5, y=-1.7, z=0.9))),
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(itemsizing='constant', title=dict(text='Leyenda'), orientation='h',
                    yanchor='top', y=-0.02, xanchor='left', x=0, font=dict(size=11)),
        height=760,
    )
    return fig
