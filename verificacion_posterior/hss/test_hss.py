"""Pruebas del diseno de HSS (AISC 360-22 y NTC-Acero CDMX) contra valores calculados a mano y contra un calculo independiente.
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

# 6) comprobacion independiente (informe de un calculo separado con el texto de AISC 360-22, mismos supuestos:
#    K = 1, KL = Lb = 350 cm, Cb = 1.0). Valores redondeados a kgf o kgf-cm.
#    Eje fuerte de la seccion A: el informe da 2 815 301 con el modelo M1 (eje neutro desplazado en el patin
#    comprimido). Este codigo usa el modelo M3 (lineas medias de las paredes), que da 2 814 396: diferencia 0.03 %.
INDEP = {
    'HSS 16 × 16 × 5/16': dict(Pn=192283, Mx=2814396, My=2814396, Vx=70566, Vy=70566),
    'HSS 16 × 16 × 1/2': dict(Pn=367751, Mx=5600155, My=5600155, Vx=108695, Vy=108695),
    'HSS 10 × 2 × 3/8': dict(Pn=17453, Mx=696597, My=202677, Vx=49897, Vy=4919),
}
for nombre, ref in INDEP.items():
    p = p_de(nombre)
    Lb = 350.0 if nombre != 'HSS 10 × 2 × 3/8' else 350.0
    res = DA.resistencias_asd(p, 'HSS', FY, FU, E, 0.30, 350.0, 350.0, Lb, 1.0, 1.0, 350.0, Cb=1.0)
    check(f'independiente {nombre}: Pn/Omega_c', res['Pa_c'], ref['Pn'], 2e-3)
    check(f'independiente {nombre}: Mn/Omega_b eje x', res['Ma_x'], ref['Mx'], 2e-3)
    check(f'independiente {nombre}: Mn/Omega_b eje y', res['Ma_y'], ref['My'], 2e-3)
    check(f'independiente {nombre}: Vn/Omega_v eje x', res['Va_x'], ref['Vx'], 2e-3)
    check(f'independiente {nombre}: Vn/Omega_v eje y', res['Va_y'], ref['Vy'], 2e-3)

# 7) Cv2 de G2.2 con kv = 5 (G4-1): regimenes G2-9, G2-10 y G2-11
lim1 = 1.10 * math.sqrt(5 * E / FY)
lim2 = 1.37 * math.sqrt(5 * E / FY)
check('Cv2 regimen G2-10 (h/t = 65)', DA._cv2_hss(65.0, E, FY), lim1 / 65.0)
check('Cv2 regimen G2-11 (h/t = 100)', DA._cv2_hss(100.0, E, FY), 1.51 * 5 * E / (100.0 ** 2 * FY))
check('Cv2 regimen G2-9 (h/t = 40)', DA._cv2_hss(40.0, E, FY), 1.0)

# 8) torsion H3.1 y H3.2 (HSS rectangular)
p = p_de('HSS 8 × 8 × 1/2')
C_mano = 2 * (20.32 - 1.27) * (20.32 - 1.27) * 1.27 - 4.5 * (4 - math.pi) * 1.27 ** 3
Tc_mano = 0.6 * FY * C_mano / 1.67                                   # h/t = 13.0 <= 2.45 sqrt(E/Fy): Fcr = 0.6 Fy
res = DA.resistencias_asd(p, 'HSS', FY, FU, E, 0.30, 350.0, 350.0, 350.0, 1.0, 1.0, 350.0, Cb=1.0)
check('torsion 8x8x1/2: Tc = Fcr C / 1.67 (H3-3, kgf·cm)', res['Tc'], Tc_mano, 1e-4)

def tn_de(t, H0):
    q = dict(H=H0, B=H0, t=t, A=0.0)
    return DA.torsion_hss(q, FY, E)
sq = math.sqrt(E / FY)
t1 = 0.3; H1_ = 70 * t1 + 3 * t1                                   # h/t = 70: H3-4
tn1, d1 = tn_de(t1, H1_)
check('torsion H3-4 (h/t = 70): Fcr = 0.6 Fy 2.45 sqrt(E/Fy)/(h/t)', d1['Fcr'], 0.6 * FY * 2.45 * sq / 70.0, 1e-6)
t2 = 0.2; H2_ = 100 * t2 + 3 * t2                                  # h/t = 100: H3-5
tn2, d2 = tn_de(t2, H2_)
check('torsion H3-5 (h/t = 100): Fcr = 0.458 pi^2 E/(h/t)^2', d2['Fcr'], 0.458 * math.pi ** 2 * E / 100.0 ** 2, 1e-6)

# H3.2: con Tr > 0.2 Tc la interaccion es H3-6; con Tr <= 0.2 Tc es H1
Pr, Mx, Vx = 50000.0, 500000.0, 5000.0
for frac, esperado_h3 in [(0.5, True), (0.1, False)]:
    d = dict(Pr_t=0.0, Pr_c=Pr, Mr_x=Mx, Mr_y=0.0, Vr_x=Vx, Vr_y=0.0, Tr=frac * res['Tc'])
    u = DA.utilizacion_asd(res, d['Pr_t'], d['Pr_c'], d['Mr_x'], d['Mr_y'], d['Vr_x'], d['Vr_y'], d['Tr'])
    if esperado_h3:
        mano = Pr / res['Pa_c'] + Mx / res['Ma_x'] + (Vx / res['Va_x'] + frac) ** 2
        check('H3-6 con Tr = 0.5 Tc', u['H3 interaccion (H3-6)'], mano, 1e-9)
        if 'H1 flexocompresion' in u:
            FALLOS.append('H1 presente con Tr > 0.2 Tc'); print('FALLA: H1 presente con Tr > 0.2 Tc')
    else:
        ratio = Pr / res['Pa_c']; mx_ = Mx / res['Ma_x']
        mano = (ratio + 8.0 / 9.0 * mx_) if ratio >= 0.2 else (ratio / 2.0 + mx_)
        check('H1 con Tr = 0.1 Tc (torsion descartada)', u['H1 flexocompresion'], mano, 1e-9)
        if 'H3 interaccion (H3-6)' in u:
            FALLOS.append('H3-6 presente con Tr <= 0.2 Tc'); print('FALLA: H3-6 presente con Tr <= 0.2 Tc')
    check(f'utilizacion de torsion Tr/Tc = {frac}', u['T torsion (H3.1)'], frac, 1e-9)

print('RESULTADO:', 'OK' if not FALLOS else f'FALLAN: {FALLOS}')
sys.exit(1 if FALLOS else 0)
