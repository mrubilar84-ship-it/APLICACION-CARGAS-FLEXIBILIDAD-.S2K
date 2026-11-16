# Dibujo de revision (planta, alzado, 3D con secciones y ejes fuertes) y planilla regenerada con la vista
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from orientacion_gerdau import contorno, ejes_locales, dimensiones
from dibujo_directo import marca_apoyo
from vista3d_plotly import figura_3d

COLOR = {'COLUMNA': '#1f77b4', 'VIGA': '#2ca02c', 'ARRIOSTRE': '#d62728', 'DIAGONAL': '#ff7f0e'}
ESCALA_SECCION = 2.5    # las secciones se dibujan ampliadas en la figura (no cambia el calculo)


def plano_con_mas_barras(dib, planta):
    """Nivel Z (planta) o cota Y (alzado) con mas barras en el plano."""
    from collections import Counter
    cuenta = Counter()
    for b in dib.barras:
        p1, p2 = dib.nodos[b['n1']], dib.nodos[b['n2']]
        if planta and abs(p1[2] - p2[2]) < 1e-9:
            cuenta[round(p1[2], 6)] += 1
        if not planta and abs(p1[1] - p2[1]) < 1e-9:
            cuenta[round(p1[1], 6)] += 1
    return cuenta.most_common(1)[0][0] if cuenta else min(p[2] if planta else p[1] for p in dib.nodos)


def dibujar_vista(ax, dib, id_de_indice, vista='planta', plano=None):
    planta = vista == 'planta'
    if plano is None:
        plano = plano_con_mas_barras(dib, planta)

    def en_plano(p):
        return abs(p[2] - plano) < 1e-9 if planta else abs(p[1] - plano) < 1e-9

    def coord(p):
        return (p[0], p[1]) if planta else (p[0], p[2])

    for b in dib.barras:
        p1, p2 = dib.nodos[b['n1']], dib.nodos[b['n2']]
        if not (en_plano(p1) and en_plano(p2)):
            continue
        (x1, y1), (x2, y2) = coord(p1), coord(p2)
        ax.plot([x1, x2], [y1, y2], color=COLOR[b['elemento']], lw=3.5, zorder=2, solid_capstyle='round')
        for p, c in [(p1, b['conexion_i']), (p2, b['conexion_j'])]:
            if c == 'rotulado':
                ax.plot(*coord(p), 'o', mfc='white', mec='k', ms=7, zorder=4)
    for i, q in enumerate(dib.nodos):
        if en_plano(q):
            ax.plot(*coord(q), 'ko', ms=4, zorder=5)
            ax.text(coord(q)[0], coord(q)[1], f' {id_de_indice[i]}', fontsize=8, zorder=6)
            if i in dib.apoyos:
                marca = 's' if marca_apoyo(dib.apoyos[i]) == 'empotrado' else '^'
                ax.plot(*coord(q), marca, color='#e67e22', ms=10, zorder=5)
    ax.set_aspect('equal'); ax.margins(0.12); ax.grid(True, color='#dddddd', lw=0.6)
    ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)' if planta else 'Z (m)')
    ax.set_title(f"{'Planta' if planta else 'Alzado'} en {'Z' if planta else 'Y'} = {plano:g} m", fontsize=10)


def dibujar_3d(ax, dib, id_de_indice):
    for i, b in enumerate(dib.barras):
        p1, p2 = dib.nodos[b['n1']], dib.nodos[b['n2']]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color=COLOR[b['elemento']], lw=2.5)
        for p, c in [(p1, b['conexion_i']), (p2, b['conexion_j'])]:
            if c == 'rotulado':
                ax.scatter(*p, s=40, facecolors='white', edgecolors='k', zorder=5)
        # seccion (envolvente del perfil) en el punto medio, y eje fuerte = eje local y (peralte)
        caja = contorno(dib, i, ESCALA_SECCION)
        if caja:
            ax.add_collection3d(Poly3DCollection([caja], facecolor=COLOR[b['elemento']], alpha=0.35,
                                                 edgecolor='k', linewidths=0.4))
            pm = [(p1[k] + p2[k]) / 2 for k in range(3)]
            d = dimensiones(b['perfil'])[0] * ESCALA_SECCION
            _, ey, _ = ejes_locales(dib, i)
            ax.quiver(*pm, *(ey * 0.6 * d), color='k', arrow_length_ratio=0.3, linewidth=1.2)
    for i, q in enumerate(dib.nodos):
        ax.text(q[0], q[1], q[2], f' {id_de_indice[i]}', fontsize=7)
        if i in dib.apoyos:
            ax.scatter(*q, s=60, marker='s' if marca_apoyo(dib.apoyos[i]) == 'empotrado' else '^', color='#e67e22', zorder=6)
        else:
            ax.scatter(*q, s=8, color='k', zorder=6)
    rangos = [max(max(p[k] for p in dib.nodos) - min(p[k] for p in dib.nodos), 1.0) for k in range(3)]
    ax.set_box_aspect(rangos)
    from matplotlib.ticker import MaxNLocator
    for eje in (ax.xaxis, ax.yaxis, ax.zaxis):
        eje.set_major_locator(MaxNLocator(4))
    ax.view_init(elev=22, azim=-60)
    ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)'); ax.set_zlabel('Z (m)')
    ax.set_title(f'3D: secciones x{ESCALA_SECCION:g}, flecha = eje fuerte, circulo blanco = extremo rotulado, '
                 'cuadrado = empotrado, triangulo = apoyo rotulado', fontsize=8)


if dib is None:
    print('Sin modelo para dibujar: corrija la planilla (bloque 7).')
else:
    fig = plt.figure(figsize=(16, 5.8))
    dibujar_vista(fig.add_subplot(1, 3, 1), dib, id_de_indice, 'planta')
    dibujar_vista(fig.add_subplot(1, 3, 2), dib, id_de_indice, 'alzado')
    dibujar_3d(fig.add_subplot(1, 3, 3, projection='3d'), dib, id_de_indice)
    fig.tight_layout()
    plt.show()

    # 3D interactiva (gira con el mouse; al pasar el cursor muestra ID, perfil y eje fuerte de cada barra)
    figura_3d(dib, id_de_indice, escala_seccion=2.5).show(renderer='iframe')

    # Planilla regenerada con sus datos (las hojas de calculo y graficos se rehacen)
    escribir_planilla('planilla_con_vista.xlsx', _filas(nodos, NODOS_COLS), _filas(barras, BARRAS_COLS),
                      filas_cargas=filas_cargas_para_excel(cargas), materiales=materiales_filas,
                      combinaciones=comb_crudas,
                      longitudes=filas_longitudes_para_excel(longitudes_df),
                      estados=[[None if _vacio(v) else v for v in f] for f in estados_df.values.tolist()])
    guardar_con_valores('planilla_con_vista.xlsx')
    print('Planilla regenerada: planilla_con_vista.xlsx (hoja VISTA_VIVA)')
