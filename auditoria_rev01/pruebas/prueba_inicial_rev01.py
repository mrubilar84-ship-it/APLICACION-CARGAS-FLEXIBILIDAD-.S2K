import ast
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / 'codigo/modulos'))
from orientacion_gerdau import ejes_locales
import diseno_asd as DA

src = root / 'codigo/modulos/analisis_opensees.py'
tree = ast.parse(src.read_text(encoding='utf-8'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_deflexion_viga')
ns = {'np': np, 'ejes_locales': ejes_locales, 'GRAVEDAD': np.array([0., 0., -1.])}
exec(compile(ast.Module(body=[fn], type_ignores=[]), str(src), 'exec'), ns)
dib = SimpleNamespace(nodos=[(0., 0., 0.), (6., 0., 0.)],
    barras=[{'n1': 0, 'n2': 1, 'elemento': 'VIGA', 'eje_fuerte': None}])
props = [{'masa': 20., 'E': 2.04e6, 'Iy': 200., 'Iz': 2000.}]
ui = np.array([0., 0., 0., 0., 1/600, 0.])
uj = np.array([0., 0., -1., 0., 1/600, 0.])
y = ns['_deflexion_viga'](dib, props, 0, {'extremos': {0: (ui, uj)}}, 0., np.array([.25, .5, .75]))
print('H-02 flecha relativa a cuerda, cm:', y.tolist(), '; esperado: [0,0,0]')
fila = {f'{e} {ext} ({u})': 0. for e, u in [('N', 'kgf'), ('Mz', 'kgf·m'), ('My', 'kgf·m'), ('Vy', 'kgf'), ('Vz', 'kgf')] for ext in ['I', 'J']}
fila['Vy I (kgf)'] = fila['Vy J (kgf)'] = 60.
fila['MZ MAX EN EL TRAMO (kgf·m)'] = 90.
fila['MY MAX EN EL TRAMO (kgf·m)'] = 0.
print('H-01 demanda Mr_x que recibe el diseno, kgf cm:', DA._demanda_fila(fila)['Mr_x'], '; esperado: 9000')
print('H-01 momento interior por equilibrio q*L^2/8, kgf cm:', .2 * 600**2 / 8)
