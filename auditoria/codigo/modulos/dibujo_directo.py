"""
MODULO DE DIBUJO DIRECTO (reemplaza la lectura de DXF).

Permite construir el modelo estructural dentro del notebook: nodos (puntos x, y, z en m),
barras (polilineas entre nodos), apoyos y ejes fuertes. Produce EXACTAMENTE el mismo
diccionario que entrega lector_validador.leer_dxf(), para que el motor de analisis
(motor_analisis.construir_y_resolver) y el validador funcionen sin cambios.

Formato de salida (igual al DXF):
  {'NODOS': [(x,y,z) en m], 'BARRAS': [{'n1','n2','elemento','perfil','capa','eje_fuerte'}],
   'NODOS_APOYO': [indices], 'ruta': str}

Unidades: metros (la conversion a cm la hace el motor).
"""
import json
import numpy as np

TOL_NODO = 1e-3                 # m: nodos a menos de esta distancia son el mismo nodo
ELEMENTOS = ['COLUMNA', 'VIGA', 'ARRIOSTRE', 'DIAGONAL']
TIPOS_APOYO = ['empotrado', 'rotulado']   # atajo para apoyo(nodo, tipo): empotrado = 6 GDL; rotulado = UX, UY, UZ
GRADOS = ['UX', 'UY', 'UZ', 'RX', 'RY', 'RZ']   # grados de libertad restringidos en un nodo (columnas de NODOS)
TIPOS_CONEXION = ['empotrado', 'rotulado']  # extremo de barra: empotrado = momento transmitido; rotulado = momento liberado


def restricciones_de(tipo_o_lista):
    """(UX, UY, UZ, RX, RY, RZ) como 6 bools. Acepta 'empotrado', 'rotulado' o una lista de 6 valores."""
    if isinstance(tipo_o_lista, str):
        if tipo_o_lista == 'empotrado':
            return (True,) * 6
        if tipo_o_lista == 'rotulado':
            return (True, True, True, False, False, False)
        raise ValueError(f'tipo de apoyo {tipo_o_lista!r} no reconocido (use empotrado, rotulado o 6 valores)')
    valores = tuple(bool(v) for v in tipo_o_lista)
    if len(valores) != 6:
        raise ValueError('un apoyo tiene 6 grados: UX, UY, UZ, RX, RY, RZ')
    return valores


def marca_apoyo(restr):
    """'empotrado' si restringe los 6 GDL; 'rotulado' si restringe alguna traslacion; 'giro' si solo giros."""
    r = restricciones_de(restr)
    if all(r):
        return 'empotrado'
    if any(r[:3]):
        return 'rotulado'
    return 'giro'


def etiqueta_restricciones(restr):
    r = restricciones_de(restr)
    if all(r):
        return 'todos (6 GDL)'
    return ', '.join(g for g, on in zip(GRADOS, r) if on) or 'ninguno'


class DibujoModelo:
    def __init__(self, tol=TOL_NODO, ruta='dibujo_directo'):
        self.nodos = []         # lista de tuplas (x, y, z)
        self.barras = []        # lista de dicts con el mismo formato que el DXF
        self.apoyos = {}        # {indice_nodo: tipo}
        self.tol = tol
        self.ruta = ruta

    # ---------- nodos ----------
    def nodo(self, x, y, z):
        """Agrega un nodo (o devuelve el existente a menos de la tolerancia). Devuelve su indice."""
        p = (round(float(x), 4), round(float(y), 4), round(float(z), 4))
        for i, q in enumerate(self.nodos):
            if all(abs(p[k] - q[k]) < self.tol for k in range(3)):
                return i
        self.nodos.append(p)
        return len(self.nodos) - 1

    # ---------- barras ----------
    def _existe(self, n1, n2):
        return any({b['n1'], b['n2']} == {n1, n2} for b in self.barras)

    def barra(self, n1, n2, elemento, perfil, conexion_i='empotrado', conexion_j='empotrado', material=None):
        """Agrega una barra entre dos nodos (indices). Si ya existe, no la duplica. Devuelve su indice o None.
        conexion_i / conexion_j: 'empotrado' o 'rotulado' en cada extremo de la barra."""
        if n1 == n2:
            raise ValueError(f'barra degenerada en el nodo {n1}')
        if self._existe(n1, n2):
            return None
        elemento = str(elemento).upper()
        if elemento not in ELEMENTOS:
            raise ValueError(f'elemento {elemento!r} no reconocido; usar {ELEMENTOS}')
        for nombre, c in [('conexion_i', conexion_i), ('conexion_j', conexion_j)]:
            if c not in TIPOS_CONEXION:
                raise ValueError(f'{nombre} {c!r} no reconocida; usar {TIPOS_CONEXION}')
        self.barras.append({'n1': n1, 'n2': n2, 'elemento': elemento, 'perfil': perfil,
                            'capa': f'{elemento}-{perfil}', 'eje_fuerte': None,
                            'conexion_i': conexion_i, 'conexion_j': conexion_j, 'material': material})
        return len(self.barras) - 1

    def polilinea(self, puntos, elemento, perfil):
        """Une una secuencia de puntos con barras consecutivas (estilo 'dibujar con lineas').
        puntos: lista de indices de nodo o de coordenadas (x, y, z). Devuelve indices de barras creadas."""
        ids = [p if isinstance(p, (int, np.integer)) else self.nodo(*p) for p in puntos]
        creadas = []
        for a, b in zip(ids[:-1], ids[1:]):
            r = self.barra(a, b, elemento, perfil)
            if r is not None:
                creadas.append(r)
        return creadas

    def eje_fuerte(self, indice_barra, direccion):
        """Fija la direccion del eje fuerte de una barra (vector en coordenadas globales)."""
        d = np.array(direccion, float)
        n = np.linalg.norm(d)
        if n < 1e-9:
            raise ValueError('direccion nula')
        self.barras[indice_barra]['eje_fuerte'] = tuple(float(v) for v in d / n)

    # ---------- apoyos ----------
    def apoyo(self, nodo_idx, restr='empotrado'):
        """Apoyo de un nodo: 6 bools (UX, UY, UZ, RX, RY, RZ) o 'empotrado' / 'rotulado'."""
        r = restricciones_de(restr)
        if not any(r):
            self.apoyos.pop(int(nodo_idx), None)
            return
        self.apoyos[int(nodo_idx)] = r

    # ---------- generadores ----------
    def marco_grilla(self, xs, ys, zs, perfil_columna, perfil_viga_x, perfil_viga_y, eje_fuerte_columna=None):
        """Marco ortogonal a partir de ejes: nodos en todas las intersecciones (x, y, z).
        Columnas en cada (x, y) entre niveles consecutivos; vigas X y vigas Y en cada nivel superior.
        eje_fuerte_columna: direccion del eje fuerte para las columnas (opcional, ej. (1,0,0))."""
        xs, ys, zs = sorted(xs), sorted(ys), sorted(zs)
        idx = {}
        for x in xs:
            for y in ys:
                for z in zs:
                    idx[(x, y, z)] = self.nodo(x, y, z)
        for x in xs:
            for y in ys:
                for za, zb in zip(zs[:-1], zs[1:]):
                    i = self.barra(idx[(x, y, za)], idx[(x, y, zb)], 'COLUMNA', perfil_columna)
                    if i is not None and eje_fuerte_columna is not None:
                        self.eje_fuerte(i, eje_fuerte_columna)
        for y in ys:
            for z in zs[1:]:
                for xa, xb in zip(xs[:-1], xs[1:]):
                    self.barra(idx[(xa, y, z)], idx[(xb, y, z)], 'VIGA', perfil_viga_x)
        for x in xs:
            for z in zs[1:]:
                for ya, yb in zip(ys[:-1], ys[1:]):
                    self.barra(idx[(x, ya, z)], idx[(x, yb, z)], 'VIGA', perfil_viga_y)
        return idx

    # ---------- salida y persistencia ----------
    def a_modelo(self):
        """Diccionario con el formato de leer_dxf(): listo para motor_analisis y validar_modelo."""
        return {'NODOS': list(self.nodos), 'BARRAS': [dict(b) for b in self.barras],
                'NODOS_APOYO': sorted(self.apoyos.keys()), 'TIPO_APOYO': dict(self.apoyos), 'ruta': self.ruta}

    def guardar_json(self, ruta):
        datos = {'nodos': self.nodos, 'barras': self.barras,
                 'apoyos': {str(k): v for k, v in self.apoyos.items()}}
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)

    @classmethod
    def cargar_json(cls, ruta):
        with open(ruta, encoding='utf-8') as f:
            datos = json.load(f)
        m = cls()
        m.nodos = [tuple(p) for p in datos['nodos']]
        m.barras = datos['barras']
        m.apoyos = {int(k): restricciones_de(v) for k, v in datos['apoyos'].items()}
        return m


def comparar_modelos(m1, m2, tol=1e-3):
    """Compara dos modelos (formato leer_dxf) sin depender del orden de nodos ni barras.
    Devuelve (ok, lista_de_diferencias)."""
    def claves_nodos(m):
        return {tuple(round(c, 3) for c in p) for p in m['NODOS']}

    def claves_barras(m):
        out = []
        for b in m['BARRAS']:
            p1 = tuple(round(c, 3) for c in m['NODOS'][b['n1']])
            p2 = tuple(round(c, 3) for c in m['NODOS'][b['n2']])
            ext = tuple(sorted([p1, p2]))
            ef = None if b['eje_fuerte'] is None else tuple(round(c, 3) for c in b['eje_fuerte'])
            out.append((ext, b['elemento'], b['perfil'], ef))
        return sorted(out, key=str)

    def claves_apoyos(m):
        return sorted(tuple(round(c, 3) for c in m['NODOS'][i]) for i in m['NODOS_APOYO'])

    dif = []
    if claves_nodos(m1) != claves_nodos(m2):
        dif.append(f"nodos distintos: {len(claves_nodos(m1))} vs {len(claves_nodos(m2))}")
    b1, b2 = claves_barras(m1), claves_barras(m2)
    if b1 != b2:
        s1, s2 = set(map(str, b1)), set(map(str, b2))
        dif.append(f"barras distintas: {len(b1)} vs {len(b2)} | solo en 1: {len(s1 - s2)} | solo en 2: {len(s2 - s1)}")
    if claves_apoyos(m1) != claves_apoyos(m2):
        dif.append("apoyos distintos")
    return (len(dif) == 0), dif
