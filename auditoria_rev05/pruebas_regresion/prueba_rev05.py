"""Pruebas de regresion de la revision 05 (respuesta a R04-01 a R04-18). Expectativas escritas a mano aqui.

Uso: DIBUJO=<carpeta con los modulos del notebook (fuentes + perfiles_gerdau.py y gerdau_datos.py)> python3 prueba_rev05.py
Sale con codigo 1 si alguna comprobacion falla. Requiere numpy, pandas, openpyxl.
"""
import math, os, sys, types

DIB = os.environ.get('DIBUJO')
if not DIB:
    sys.exit('Defina DIBUJO=<carpeta con los modulos del notebook>')
sys.path.insert(0, DIB)
import diseno_asd as D
import openpyxl

# Valores de norma: se leen de la hoja NORMA de la plantilla del paquete, igual que el notebook (cargar_norma).
PLANTILLA = os.environ.get('PLANTILLA', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'plantilla',
                                                     'plantilla_soportes.xlsx'))
_ws = openpyxl.load_workbook(PLANTILLA, data_only=True)['NORMA']
_valores, _leyendo = {}, False
for _fila in _ws.iter_rows(values_only=True):
    if not _fila or _fila[0] is None:
        continue
    if str(_fila[0]).strip() == 'CLAVE':
        _leyendo = True
        continue
    if _leyendo and isinstance(_fila[1], (int, float)):
        _valores[str(_fila[0]).strip()] = float(_fila[1])
D.cargar_norma(_valores, 1.0)
import perfiles_gerdau as G
import placas_base as PB

ok_n, fallas = 0, []


def ok(nombre, cond, detalle=''):
    global ok_n
    if cond:
        ok_n += 1
    else:
        fallas.append(nombre)
    print(f"{'OK   ' if cond else 'FALLA'} {nombre}  {detalle}")


res = dict(Pa_t=1000., Pa_c=1000., Ma_x=1000., Ma_y=1000., Va_x=1000., Va_y=1000.)

# R04-01: H1 con axial nulo. Mrx/Mcx + Mry/Mcy = 0.6 + 0.6 = 1.2 (H1-1b con Pr/Pc = 0)
u = D.utilizacion_asd(res, 0, 0, 600, 600, 0, 0)
ok('R04-01 H1 sin axial (biaxial concurrente)', abs(u.get('H1 flexotension', 0) - 1.2) < 1e-12, f"H1={u.get('H1 flexotension')}")
u = D.utilizacion_asd(res, 0, 0, 600, 0, 0, 0)
ok('R04-01 H1 sin axial (uniaxial)', abs(u.get('H1 flexotension', 0) - 0.6) < 1e-12, f"H1={u.get('H1 flexotension')}")

# R04-02: torsion en seccion abierta: bloqueo; sin torsion no hay bloqueo
u = D.utilizacion_asd(res, 0, 0, 0, 0, 0, 0, 1e6)
ok('R04-02 torsion en seccion abierta bloquea', u.get(D.CHEQUEO_TORSION_ABIERTA) == D.FU_BLOQUEO_TORSION, str(u))
u = D.utilizacion_asd(res, 0, 0, 0, 0, 0, 0, 1e-6)
ok('R04-02 ruido numerico no bloquea', D.CHEQUEO_TORSION_ABIERTA not in u)

# R04-12 (IR): E7 con cuatro salientes de patin. Expectativa independiente.
p = dict(A=64., H=40., B=30., t=.6, e=.75)
fy, E, fn = 3515., 2038900., 3000.
Ae_code, _ = D._elementos_E7(p, 'I', fy, E, fn)
sq = math.sqrt(E / fy)
def be_E7(b, t_lr, c1, c2, lam_c):
    lam = b / lam_c[0]
    if lam <= t_lr * math.sqrt(fy / fn):
        return b
    fel = (c2 * t_lr / lam) ** 2 * fy
    r = math.sqrt(fel / fn)
    return min(b * (1 - c1 * r) * r, b)
bw = be_E7(p['H'] - 2 * p['t'], 1.49 * sq, .18, 1.31, (p['e'],))
bf = be_E7(p['B'] / 2, .56 * sq, .22, 1.49, (p['t'],))
Ae_exp = p['A'] - (p['H'] - 2 * p['t'] - bw) * p['e'] - 4 * (p['B'] / 2 - bf) * p['t']
ok('R04-12 E7 IR: cuatro salientes de patin', abs(Ae_code - Ae_exp) < 1e-9, f"codigo={Ae_code:.6f} esperado={Ae_exp:.6f}")

# R04-07/R04-07 placas: datos invalidos y geometria incompatible
stub = types.ModuleType('perfiles_gerdau')
stub.obtener_perfil = lambda nombre: {'H': 15., 'B': 6.}
NOR = dict(BASE_J8_085=0.85, BASE_J8_LIM=1.7, BASE_OMEGA_C=2.31, BASE_FACTOR_ASD=1.5, BASE_PHI_PL=0.90,
           BASE_PHI_ANCLA_T=0.75, BASE_FNT=0.70, BASE_PHI_ANCLA_V=0.75, BASE_FV=0.40, BASE_PHI_CONO=0.70,
           BASE_KC_CONO=10.0, BASE_LAMBDA=1.0, BASE_PHI_SOLD=0.75, BASE_SOLD_FRAC=0.60, BASE_FEXX_KSI=70.0)
DATOS = dict(id=1, fc=250., dado_n=60., dado_b=60., pl_n=30., pl_b=30., pl_t=2., fy=2530., n=4., c_t=5., diam=.75,
             hilos=10., fu=4080., hef=20., sold_w=.6, sold_l=60., mu=.55, nota=None)
CENTRADA = [('C', [0, 0, 20000., 0, 0, 0])]
PB.G = stub          # solo dentro de placas_base: el perfil sintetico (no se altera el modulo de perfiles)
b = PB.verificar_nodo(dict(DATOS, pl_t=-2.), 'sint', (1., 0., 0.), CENTRADA, NOR)
ok('R04-07 espesor negativo: DATO INVALIDO', b['estado'] == 'DATO INVALIDO', b['estado'])
b = PB.verificar_nodo(dict(DATOS, n=4.5), 'sint', (1., 0., 0.), CENTRADA, NOR)
ok('R04-07 anclas fraccionarias: DATO INVALIDO', b['estado'] == 'DATO INVALIDO', b['estado'])
b = PB.verificar_nodo(dict(DATOS, pl_n=10., c_t=1.), 'sint', (1., 0., 0.), CENTRADA, NOR)
ok('R04-07 placa menor que la envolvente: DATO INVALIDO', b['estado'] == 'DATO INVALIDO', b['estado'])
b = PB.verificar_nodo(dict(DATOS, pl_t=float('inf')), 'sint', (1., 0., 0.), CENTRADA, NOR)
ok('R04-07 valor infinito: DATO INVALIDO', b['estado'] == 'DATO INVALIDO', b['estado'])

# R04-03/R04-04: momentos no verificados y estado global. Nunca CUMPLE con verificaciones pendientes.
b = PB.verificar_nodo(DATOS, 'sint', (1., 0., 0.), [('T', [0, 0, 0, 0, 0, 1e9])], NOR)
ok('R04-03 torsion MZ no se presenta como CUMPLE', b['estado'] == 'NO REVISADO', b['estado'])
b = PB.verificar_nodo(DATOS, 'sint', (1., 0., 0.), [('U', [0, 0, -3000., 0, 50000., 0])], NOR)
ok('R04-04 levantamiento con flexion: NO REVISADO', b['estado'] == 'NO REVISADO', b['estado'])
b = PB.verificar_nodo(DATOS, 'sint', (1., 0., 0.), [('B', [0, 0, 20000., 60000., 60000., 0])], NOR)
ok('R04-05 contacto biaxial fuera del nucleo: pendiente explicito y no CUMPLE', b['estado'] in ('NO REVISADO', 'NO CUMPLE')
   and any('biaxial' in p for p in b['pendientes']), b['estado'])
ok('R04-04 limitaciones de anclajes siempre listadas', any('A_Nc' in p for p in b['pendientes']))

# R04-08: Fu ausente con traccion: no se supone fractura
_ir_nombre = next(n for n, v in G.PERFILES.items() if v.get('familia') == 'IR' and D._props_asd(n, 'IR')[0] is not None)
p_ir, _ = D._props_asd(_ir_nombre, 'IR')
res_fu = D.resistencias_asd(p_ir, 'IR', 3515, None, 2038900, .3, 100, 100, 100, 1, 1, 100, Cb=1)
dem_t = dict(Pr_t=.5 * res_fu['Pa_t'], Pr_c=0, Mr_x=0, Mr_y=0, Vr_x=0, Vr_y=0, Tr=0)
ev = D._chequear(p_ir, 'IR', 3515, None, 2038900, .3, 100, 100, 100, 1, 1, 'VIGA', [dem_t], cb=1)
ok('R04-08 Fu ausente con traccion: NO REVISADO', str(ev.get('motivo', '')).startswith('NO REVISADO: falta Fu')
   and ev.get('bloquea_traccion') is True, str(ev.get('motivo')))

# R04-09: demanda NaN no se convierte en cero
cols = ['N I (kgf)', 'N J (kgf)', 'Mz I (kgf·m)', 'Mz J (kgf·m)', 'MZ MAX EN EL TRAMO (kgf·m)', 'My I (kgf·m)',
        'My J (kgf·m)', 'MY MAX EN EL TRAMO (kgf·m)', 'Vy I (kgf)', 'Vy J (kgf)', 'T I (kgf·m)', 'T J (kgf·m)',
        'Vz I (kgf)', 'Vz J (kgf)']
fila_cero = {c: 0.0 for c in cols}
D._demanda_fila(dict(fila_cero, CASO='c', BARRA=1))
fila_nan = dict(fila_cero, **{'Vy I (kgf)': float('nan')})
try:
    D._demanda_fila(dict(fila_nan, CASO='c', BARRA=1))
    ok('R04-09 NaN detiene el calculo', False, 'no lanzo error')
except D.ErrorAsd as e:
    ok('R04-09 NaN detiene el calculo', 'no se supone cero' in str(e))

# R04-11: la alerta del catalogo llega a la API de perfiles
alertas = [n for n, v in G.PERFILES.items() if v.get('alerta_catalogo')]
ok('R04-11 hay perfiles con alerta en el catalogo', len(alertas) > 0, str(len(alertas)))
if alertas:
    ok('R04-11 la alerta llega a obtener_perfil', bool(G.obtener_perfil(alertas[0]).get('alerta_catalogo')),
       alertas[0])

# R04-18 (conservar PARAMETROS al regenerar el libro) se verifica de extremo a extremo con el notebook
# (Kz = 0.5 en la planilla de entrada): ver PRUEBAS_REV05.md. No se importa celda6 aqui porque es un
# script de celda que escribe la plantilla al importarse.

print(f"\nRESULTADO: {'OK' if not fallas else 'FALLA'}  ({ok_n} comprobaciones OK, {len(fallas)} FALLA)")
sys.exit(1 if fallas else 0)
