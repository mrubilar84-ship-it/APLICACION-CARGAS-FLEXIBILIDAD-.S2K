"""Pruebas del diseno de HSS (AISC 360-22 y NTC-Acero CDMX) contra valores calculados a mano.
Uso: python3 test_hss.py   (sale con codigo 0 solo si todas las comprobaciones cumplen)
No requiere el notebook: carga los modulos de fuentes_notebook/ con una base vacia (la base se usa solo para
obtener_perfil, que aqui no se llama; los datos se toman de datos/hss_atc_catalogo.json)."""
import ast, json, math, os, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
FN = os.path.join(REPO, 'fuentes_notebook')
sys.path.insert(0, FN)
TMP = tempfile.mkdtemp(prefix='hss_test_')
open(os.path.join(TMP, 'perfiles_gerdau.py'), 'w').write('PERFILES = {}\n')
sys.path.insert(0, TMP)
import diseno_asd as DA

ARBOL = ast.parse(open(os.path.join(FN, 'celda6_plantilla.py'), encoding='utf-8').read())
NORMA = next(ast.literal_eval(n.value) for n in ARBOL.body
             if isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == 'NORMA_VALORES' for t in n.targets))
DA.cargar_norma({c: v for (c, v, *_r) in NORMA}, 1.0)
E, NU, FY, FU = 2038900.0, 0.30, 3234.0, 4359.0
CAT = {r['perfil_comercial']: r for r in json.load(open(os.path.join(FN, 'datos', 'hss_atc_catalogo.json'),
                                                        encoding='utf-8'))['perfiles']}
FALLOS = []


def check(nombre, obtenido, esperado, tol_rel=1e-3):
    ok = abs(obtenido - esperado) <= tol_rel * max(1.0, abs(esperado))
    print(f"{'OK   ' if ok else 'FALLA'} {nombre}: obtenido={obtenido:.6g} esperado={esperado:.6g}")
    if not ok:
        FALLOS.append(nombre)


def p_de(nombre):
    r = CAT[nombre]
    return dict(H=r['d_ala_diametro_cm'], B=r['bf_b_cm'], e=r['tw_cm'], t=r['tf_t_cm'], A=r['area_cm2'], Ix=r['ix_cm4'],
                Iy=r['iy_cm4'], Sx=r['sx_cm3'], Sy=r['sy_cm3'], rx=r['rx_cm'], ry=r['ry_cm'], J=r['j_cm4'],
                Zx=r['zx_cm3'], Zy=r['zy_cm3'], Cw=0.0)


# 1) cortante de 8 x 8 x 1/2 (G2.1, Aw = 2 h t, h = 20.32 - 3 t, Cv = 1 porque h/t <= 2.24 sqrt(E/Fy))
p = p_de('HSS 8 × 8 × 1/2')
h = 20.32 - 3 * 1.27
vn, om, _ = DA.vn_fuerte(p, 'HSS', FY, E)
check('cortante eje fuerte HSS 8x8x1/2 (Vn/Omega, kgf)', vn / om, 0.6 * FY * 2 * h * 1.27 / 1.67)

# 2) E7-2: pared sin reduccion si lambda <= lambda_r sqrt(Fy/Fn); con reduccion si lambda es mayor
fn = 3000.0
lr = DA.AISC_HSS_LR_COMP * math.sqrt(E / FY)
lim = lr * math.sqrt(FY / fn)
def ae_pared(lam):
    t = 0.5
    b = lam * t
    q = dict(B=b + 3 * t, H=b + 3 * t, t=t, A=0.0)
    q['A'] = 4 * b * t
    ae, det = DA._elementos_E7_hss(q, FY, E, fn)
    return det['elementos'][0][3] / b          # be/b de la pared horizontal
check('E7-2: be = b justo por debajo de lambda_r sqrt(Fy/Fn)', ae_pared(lim * 0.99), 1.0)
be_sobre = ae_pared(lim * 1.02)
if not (0.5 < be_sobre < 1.0):
    FALLOS.append('E7-3 reduccion justo por encima del umbral'); print('FALLA E7-3: be/b =', be_sobre)
else:
    print(f'OK    E7-3: be/b justo por encima del umbral = {be_sobre:.4f}')

# 3) F7-3 en una seccion esbelta: Se sin reduccion debe coincidir con el S del catalogo (dentro de 3 %)
p = p_de('HSS 16 × 16 × 5/16')
bf = p['B'] - 3 * p['t']
se_full = DA._Se_hss(p, 'x', bf)
ratio = se_full / p['Sx']
if abs(ratio - 1) > 0.03:
    FALLOS.append('Se sin reduccion vs S catalogo'); print('FALLA Se sin reduccion/S catalogo =', round(ratio, 4))
else:
    print(f'OK    Se (sin reduccion) / S catalogo = {ratio:.4f} (modelo de lineas medias)')

# 4) ductilidad NTC media: 6 x 6 x 1/4 con pared plana de 13.335 cm y t = 0.635 cm
p = p_de('HSS 6 × 6 × 1/4')
d = DA._ductilidad(p, 'HSS', FY, E, 'COLUMNA', 'MEDIA')
check('ductilidad media 6x6x1/4 (lambda/0.64 sqrt(E/Fy))', d['U'], (13.335 / 0.635) / (0.64 * math.sqrt(E / FY)), 2e-3)

# 5) claves normativas de HSS en la hoja NORMA de la plantilla
esperadas = {'AISC_HSS_LP_PATIN': 1.12, 'AISC_HSS_LR_PATIN': 1.40, 'AISC_HSS_LP_ALMA': 2.42, 'AISC_HSS_LR_ALMA': 5.70,
             'AISC_HSS_LR_COMP': 1.40, 'AISC_HSS_C1': 0.20, 'AISC_HSS_C2': 1.38, 'NTC_HSS_LR_COMP': 1.40,
             'NTC_HSS_LIM_PATIN_PL': 1.12, 'NTC_HSS_LIM_PATIN_P': 1.12, 'NTC_HSS_LIM_PATIN_R': 1.40,
             'NTC_HSS_LIM_ALMA_P': 2.42, 'NTC_HSS_LIM_ALMA_R': 5.70, 'NTC_HSS_DUC_ALTA': 0.55, 'NTC_HSS_DUC_MEDIA': 0.64}
valores = {c: v for (c, v, *_r) in NORMA}
for k, v in esperadas.items():
    check(f'NORMA {k}', valores[k], v, 1e-12)

print('RESULTADO:', 'OK' if not FALLOS else f'FALLAN: {FALLOS}')
sys.exit(1 if FALLOS else 0)
