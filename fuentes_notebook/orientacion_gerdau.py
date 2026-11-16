"""
ORIENTACION DEL EJE FUERTE (peralte) EN PANTALLA, con la base Gerdau Mexico rev04.

Convencion del motor (copiada de motor_analisis.py del otro chat, sin depender de ese paquete):
  xAxis = (p2 - p1)/L ; yAxis = vecxz x xAxis ; zAxis = xAxis x yAxis.
  El eje fuerte (Iz) es el eje local y => su direccion es el PERALTE d del perfil.

Defaults del motor (sin marca):
  - vigas/diagonales: peralte VERTICAL (eje fuerte resiste gravedad)
  - columnas:         peralte en Y global (vecxz = (1,0,0))
"""
import math
import numpy as np
import perfiles_gerdau as G


def vector_vecxz(p1, p2, elemento):
    """vecxz por defecto segun el tipo de elemento (igual que el motor)."""
    v = np.array(p2, float) - np.array(p1, float)
    L = np.linalg.norm(v)
    x = v / L
    if abs(x[2]) > 0.9:                       # columna (casi vertical)
        return (1.0, 0.0, 0.0)
    vx = np.cross(x, np.array([0.0, 0.0, 1.0]))   # viga/diagonal: yAxis vertical
    n = np.linalg.norm(vx)
    if n < 1e-6:
        return (1.0, 0.0, 0.0)
    vx = vx / n
    return (float(vx[0]), float(vx[1]), float(vx[2]))


def vecxz_desde_direccion(p1, p2, s):
    """vecxz que hace que el eje local y (= peralte) apunte segun s (proyectado perpendicular a la barra)."""
    x = np.array(p2, float) - np.array(p1, float); x = x / np.linalg.norm(x)
    s = np.array(s, float)
    u = s - x * np.dot(s, x)
    nu = np.linalg.norm(u)
    if nu < 1e-6:
        return None
    u = u / nu
    v = np.cross(x, u)
    return (float(v[0]), float(v[1]), float(v[2]))


def vecxz_de_barra(nodos, b):
    """vecxz de una barra: usa 'eje_fuerte' si existe, si no el default por tipo de elemento."""
    p1 = nodos[b['n1']]; p2 = nodos[b['n2']]
    s = b.get('eje_fuerte')
    if s:
        v = vecxz_desde_direccion(p1, p2, s)
        if v is not None:
            return v
    return vector_vecxz(p1, p2, b.get('elemento'))


def ejes_locales(dib, i):
    """Ejes locales (x, y, z) de la barra i."""
    b = dib.barras[i]
    p1, p2 = dib.nodos[b['n1']], dib.nodos[b['n2']]
    vecxz = np.array(vecxz_de_barra(dib.nodos, b), float)
    x = np.array(p2, float) - np.array(p1, float); x = x / np.linalg.norm(x)
    y = np.cross(vecxz, x); y = y / np.linalg.norm(y)
    z = np.cross(x, y)
    return x, y, z


def dimensiones(perfil):
    """(d, bf) en metros desde Gerdau (H = d, B = bf en cm). None si el perfil no existe o no tiene dato."""
    p = G.obtener_perfil(perfil)
    if p is None or p['H'] is None or p['B'] is None:
        return None
    return float(p['H']) / 100.0, float(p['B']) / 100.0


def contorno(dib, i, escala=1.0):
    """4 vertices globales del rectangulo del perfil en el punto medio de la barra i.
    Alto = d a lo largo del eje local y (eje fuerte); ancho = bf a lo largo de z."""
    b = dib.barras[i]
    p1, p2 = np.array(dib.nodos[b['n1']], float), np.array(dib.nodos[b['n2']], float)
    pm = (p1 + p2) / 2
    dims = dimensiones(b['perfil'])
    if dims is None:
        return None
    d, bf = dims[0] * escala, dims[1] * escala
    x, y, z = ejes_locales(dib, i)
    c = [pm + sy * (d / 2) * y + sz * (bf / 2) * z for sy, sz in [(1, 1), (-1, 1), (-1, -1), (1, -1)]]
    return [tuple(float(v) for v in q) for q in c]


PRESETS = {'peralte vertical (Z)': (0.0, 0.0, 1.0),
           'peralte en X': (1.0, 0.0, 0.0),
           'peralte en Y': (0.0, 1.0, 0.0)}


def orientar(dib, i, preset):
    """Fija el peralte (eje fuerte) de la barra i con un preset o un vector. Rechaza direccion paralela a la barra."""
    b = dib.barras[i]
    s = np.array(PRESETS[preset] if isinstance(preset, str) else preset, float)
    p1, p2 = np.array(dib.nodos[b['n1']], float), np.array(dib.nodos[b['n2']], float)
    x = (p2 - p1) / np.linalg.norm(p2 - p1)
    if abs(np.dot(s, x)) > 0.999:
        raise ValueError(f'el peralte no puede ser paralelo a la barra {i}; elija otra direccion')
    dib.eje_fuerte(i, tuple(s))
    return b['eje_fuerte']


def ortogonalidad(dib, i):
    """Angulo (grados) entre el eje fuerte asignado y la barra; 90 = perpendicular (correcto)."""
    b = dib.barras[i]
    if b['eje_fuerte'] is None:
        return None
    p1, p2 = np.array(dib.nodos[b['n1']], float), np.array(dib.nodos[b['n2']], float)
    x = (p2 - p1) / np.linalg.norm(p2 - p1)
    s = np.array(b['eje_fuerte'], float)
    return math.degrees(math.acos(max(-1.0, min(1.0, abs(np.dot(s, x))))))
