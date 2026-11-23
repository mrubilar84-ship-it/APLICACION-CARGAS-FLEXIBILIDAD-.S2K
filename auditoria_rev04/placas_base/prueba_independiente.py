"""Prueba independiente de placas_base.py (bloque 10b) contra formulas escritas a mano.

Las expectativas se calculan aqui con formulas propias (no se importa nada de placas_base para calcularlas).
Caso: placa 30 x 30 cm, dado 60 x 60 cm, f'c = 250 kgf/cm2, Fy placa = 2530, perfil sintetico H = 15 cm, B = 6 cm,
eje fuerte en X (W_x = 15, W_y = 6). Pernos: n = 4 (dos por lado en X), c = 5 cm, D = 0.75 pulg, 10 hilos/pulg,
Fu = 4080 kgf/cm2, h_ef = 20 cm. Soldadura w = 0.6 cm, L = 60 cm. Factores: NORMA de la rev03 (F_nt = 0.70).
Uso: DIBUJO=<carpeta con placas_base.py> python3 prueba_independiente.py   (sale con codigo 1 si algun caso falla)
"""
import math, os, sys, types

DIB = os.environ.get('DIBUJO', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'codigo', 'fuentes_notebook'))
sys.path.insert(0, DIB)
stub = types.ModuleType('perfiles_gerdau')                 # solo para la prueba: perfil sintetico
stub.obtener_perfil = lambda nombre: {'H': 15.0, 'B': 6.0}
sys.modules['perfiles_gerdau'] = stub
import placas_base as PB

NOR = dict(BASE_J8_085=0.85, BASE_J8_LIM=1.7, BASE_OMEGA_C=2.31, BASE_FACTOR_ASD=1.5, BASE_PHI_PL=0.90,
           BASE_PHI_ANCLA_T=0.75, BASE_FNT=0.70, BASE_PHI_ANCLA_V=0.75, BASE_FV=0.40, BASE_PHI_CONO=0.70,
           BASE_KC_CONO=10.0, BASE_LAMBDA=1.0, BASE_PHI_SOLD=0.75, BASE_SOLD_FRAC=0.60, BASE_FEXX_KSI=70.0)
D = dict(id=1, fc=250.0, dado_n=60.0, dado_b=60.0, pl_n=30.0, pl_b=30.0, pl_t=2.0, fy=2530.0, n=4.0, c_t=5.0,
         diam=0.75, hilos=10.0, fu=4080.0, hef=20.0, sold_w=0.6, sold_l=60.0, mu=0.55, nota=None)
CASOS = [  # (nombre, [FX, FY, FZ, MX, MY, MZ] en kgf y kgf·cm)
    ('C1 centrada', [0, 0, 20000.0, 0, 0, 0]),
    ('C2 e = N/6 (borde del nucleo)', [0, 0, 20000.0, 0, 100000.0, 0]),
    ('C3 e = 7.5 cm (fuera del nucleo)', [0, 0, 20000.0, 0, 150000.0, 0]),
    ('C4 e = 13.33 cm (pernos en traccion)', [0, 0, 20000.0, 0, 266600.0, 0]),
    ('C5 levantamiento', [0, 0, -3000.0, 0, 50000.0, 0]),
    ('C6 cortante', [2000.0, 0, 20000.0, 0, 0, 0]),
]

# ---------- expectativas independientes ----------
N, B, Wx, Wy, fc, fy = 30.0, 30.0, 15.0, 6.0, 250.0, 2530.0
A1, A2 = N * B, 60.0 * 60.0
Pp = min(0.85 * fc * A1 * math.sqrt(A2 / A1), 1.7 * fc * A1)
f_adm = Pp / (2.31 * A1)
Ab = math.pi / 4 * 0.75 ** 2 * 6.4516
At = math.pi / 4 * (0.75 - 0.9743 / 10.0) ** 2 * 6.4516
allow_T = 0.70 * 4080.0 * At / 2.00
allow_V = 0.40 * 4080.0 * Ab / 2.00
Nb = 10.0 * 1.0 * math.sqrt(fc * 0.0980665) * (200.0) ** 1.5 / 9.80665
allow_cono = Nb / (1.5 / 0.70)
allow_w = 0.6 * 70.0 * 70.307 * 0.707 * 0.6 / 2.00


def fu_flexion_pl(P):
    """t_req = l sqrt(2 Omega f / Fy) con l = max(m, n, lambda n'), Omega = 1.5/0.9; FU = (t_req/t)^2."""
    f = P / A1
    m = (N - 0.95 * Wx) / 2.0
    n = (B - 0.8 * Wy) / 2.0
    npr = math.sqrt(Wx * Wy) / 4.0
    X = 4 * Wx * Wy / (Wx + Wy) ** 2 * 2.31 * P / Pp
    lam = 2 * math.sqrt(X) / (1 + math.sqrt(1 - X))
    l = max(m, n, lam * npr)
    treq = l * math.sqrt(2 * (1.5 / 0.9) * f / fy)
    return (treq / 2.0) ** 2


def traccion_equilibrio(P, e):
    """Pernos en X. Triangular con f = f_adm: C = f_adm B Y/2 = P + T; C (x_T - Y/3) = P (x_T - x_P). Biseccion propia."""
    x_P, x_T = N / 2 - e, N - 5.0
    k = f_adm * B / 2.0
    g = lambda Y: k * Y * (x_T - Y / 3.0) - P * (x_T - x_P)
    a, b = 3 * x_P, N
    for _ in range(200):
        m = (a + b) / 2
        if g(m) < 0:
            a = m
        else:
            b = m
    Y = (a + b) / 2
    return k * Y - P, Y, g(Y)


ok_total = 0
fallas = []


def comprobar_cero(nombre, valor, tol):
    global ok_total
    estado = 'OK   ' if abs(valor) <= tol else 'FALLA'
    if abs(valor) <= tol:
        ok_total += 1
    else:
        fallas.append(nombre)
    print(f'{estado} {nombre:58s} valor={valor:.3e}  tolerancia={tol:.0e}')


def comprobar(nombre, obtenido, esperado, tol=1e-3):
    global ok_total
    dif = abs(obtenido - esperado) / max(abs(esperado), 1e-9)
    estado = 'OK   ' if dif <= tol else 'FALLA'
    if dif <= tol:
        ok_total += 1
    else:
        fallas.append(nombre)
    print(f'{estado} {nombre:58s} obtenido={obtenido:.6g}  esperado={esperado:.6g}  dif_rel={dif:.2e}')


r = PB.verificar_nodo(D, 'CE 6x13', (1.0, 0.0, 0.0), CASOS, NOR)
c = {x['caso']: x for x in r['combos']}
print('estado del nodo:', r['estado'], '| f_adm =', round(r['ctx']['f_adm'], 4), 'Pp =', round(r['ctx']['Pp'], 2))
comprobar('f_adm aplastamiento (J8)', r['ctx']['f_adm'], f_adm)
comprobar('C1 FU aplastamiento', c['C1 centrada']['fu']['ap'], (20000 / A1) / f_adm)
comprobar('C1 FU espesor de placa (DG1, voladizo)', c['C1 centrada']['fu']['pl'], fu_flexion_pl(20000))
comprobar('C2 FU aplastamiento (dentro del nucleo)', c['C2 e = N/6 (borde del nucleo)']['fu']['ap'],
          (2 * 20000 / A1) / f_adm)
f3 = 2 * 20000 / (B * 3 * (N / 2 - 7.5))
comprobar('C3 FU aplastamiento (triangular, X)', c['C3 e = 7.5 cm (fuera del nucleo)']['fu']['ap'], f3 / f_adm)
T4, Y4, res4 = traccion_equilibrio(20000, 266600 / 20000)
comprobar('C4 traccion total T (equilibrio independiente)', c['C4 e = 13.33 cm (pernos en traccion)']['Tside'], T4, 1e-3)
comprobar_cero('C4 residuo del equilibrio independiente |g(Y)| (debe ser ~0)', abs(res4), 1e-6)
comprobar('C4 FU traccion por perno', c['C4 e = 13.33 cm (pernos en traccion)']['fu']['T'], (T4 / 2.0) / allow_T)
comprobar('C4 FU cono', c['C4 e = 13.33 cm (pernos en traccion)']['fu']['cono'], T4 / allow_cono)
Tw4 = 266600 / Wx                                  # Mx = 0: el momento de ala es My / Wx
comprobar('C4 FU soldadura (Tw = max(Mx/Wy, My/Wx))', c['C4 e = 13.33 cm (pernos en traccion)']['fu']['w'],
          (Tw4 / 60.0) / allow_w)
comprobar('C5 traccion total levantamiento T = Pt/2 + My/(N-2c)', c['C5 levantamiento']['Tside'], 1500 + 50000 / 20.0)
comprobar('C5 FU traccion por perno', c['C5 levantamiento']['fu']['T'], (4000 / 2.0) / allow_T)
comprobar('C5 FU cono', c['C5 levantamiento']['fu']['cono'], 4000 / allow_cono)
comprobar('C6 FU cortante por perno (V/n con roscas)', c['C6 cortante']['fu']['V'], (2000 / 4.0) / allow_V)
print(f'\nRESULTADO: {"OK" if not fallas else "FALLA"}  ({ok_total} comprobaciones OK, {len(fallas)} FALLA)')
sys.exit(1 if fallas else 0)
