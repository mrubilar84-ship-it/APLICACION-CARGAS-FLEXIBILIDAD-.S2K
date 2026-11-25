"""Pruebas de la familia OR (IMCA, PTE rectangular y cuadrado) en la base de perfiles y en el diseno ASD.

Uso:  DIBUJO=<carpeta con los modulos del notebook (diseno_asd.py, perfiles_gerdau.py, gerdau_datos.py)> python3 test_or_imca.py
Comprueba: registros y nombres; valores impresos (sin factor B4.2); enrutamiento de las ecuaciones de seccion hueca
igual que HSS (E7, F7, G2, G4, H3) y que el factor AISC_B42_HSS no se aplica a OR; alertas de las filas dudosas.
Sale con codigo 1 si alguna comprobacion falla.
"""
import math
import os
import sys

DIB = os.environ.get('DIBUJO')
if not DIB:
    sys.exit('Defina DIBUJO=<carpeta con los modulos del notebook>')
sys.path.insert(0, DIB)
import diseno_asd as DA          # noqa: E402
import perfiles_gerdau as G      # noqa: E402

import openpyxl                  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PLANTILLA = os.environ.get('PLANTILLA', os.path.join(RAIZ, 'plantilla_soportes.xlsx'))


def cargar_valores(ruta):
    """Valores {CLAVE: valor} de la hoja NORMA de la plantilla."""
    ws = openpyxl.load_workbook(ruta, data_only=True)['NORMA']
    valores, leyendo = {}, False
    for fila in ws.iter_rows(values_only=True):
        if not fila or fila[0] is None:
            continue
        if str(fila[0]).strip() == 'CLAVE':
            leyendo = True
            continue
        if leyendo and isinstance(fila[1], (int, float)):
            valores[str(fila[0]).strip()] = float(fila[1])
    return valores


DA.cargar_norma(cargar_valores(PLANTILLA), 1.0)
FALLOS = []
FY, E_ACERO, G_ACERO, LB = 3515.0, 2.04e6, 7.9e5, 300.0      # kgf/cm2, cm


def chequeo(texto, cond):
    print(('OK    ' if cond else 'FALLO ') + texto)
    if not cond:
        FALLOS.append(texto)


OR_RECT = 'OR 51x25x3.2x3.27 (kgf/m)'
OR_CUAD = 'OR 51x1.9x2.85 (kgf/m)'
OR_CON_ALERTA = 'OR 127x3.2x7.41 (kgf/m)'
HSS = 'HSS 4 × 4 × 3/16'

registros_or = [p for p in G.PERFILES.values() if p['familia'] == 'OR']
chequeo(f'base: 416 registros OR (rectangulares 274 + cuadrados 142), hay {len(registros_or)}', len(registros_or) == 416)
chequeo('nombres OR unicos', len({p['perfil_comercial'] for p in registros_or}) == len(registros_or))
chequeo('OR en FAMILIAS_ASD y al final de FAMILIA_ORDEN', 'OR' in DA.FAMILIAS_ASD and DA.FAMILIA_ORDEN[-1] == 'OR')
chequeo('20 registros con alerta_catalogo (filas que no cuadran)',
        sum(1 for p in registros_or if p.get('alerta_catalogo')) == 20)
chequeo('127x3.2 de la primera fila lleva alerta', bool(G.PERFILES[OR_CON_ALERTA].get('alerta_catalogo')))

p_or = G.obtener_perfil(OR_RECT)
chequeo('51x25x3.2: masa = kg/m impreso (3.27)', abs(p_or['masa'] - 3.27) < 1e-9)
chequeo('51x25x3.2: dimensiones H = 5.1 cm, B = 2.5 cm', abs(p_or['H'] - 5.1) < 1e-9 and abs(p_or['B'] - 2.5) < 1e-9)
chequeo('51x25x3.2: espesor de diseno t = 0.29 cm impreso (sin factor)', abs(p_or['t'] - 0.29) < 1e-9)
chequeo('51x25x3.2: A = 3.92, Ix = 11.7 impresos', abs(p_or['A'] - 3.92) < 1e-9 and abs(p_or['Ix'] - 11.7) < 1e-9)

prop_or, falta = DA._props_asd(OR_RECT, 'OR')
chequeo(f'_props_asd(OR) no deja NO REVISADO ({falta})', prop_or is not None and not falta)
chequeo('_props_asd(OR): t de diseno = tdis impreso (sin factor AISC_B42_HSS)',
        prop_or is not None and abs(prop_or['t'] - 0.29) < 1e-9)
chequeo('_props_asd(OR): A y J como se imprimen',
        prop_or is not None and abs(prop_or['A'] - 3.92) < 1e-9 and abs(prop_or['J'] - 9.9) < 1e-9)

prop_hss, _ = DA._props_asd(HSS, 'HSS')
chequeo('HSS sigue aplicando el factor B4.2 (t = 0.93 t_nominal)',
        prop_hss is not None and abs(prop_hss['t'] - DA.FACTOR_ESPESOR_HSS * prop_hss['t_nominal']) < 1e-9)

chequeo("_forma('OR') == 'HSS' (seccion hueca)", DA._forma('OR') == 'HSS')
chequeo("seccion_de('OR ...') quita el tipo", DA.seccion_de(OR_RECT) == '51x25x3.2x3.27 (kgf/m)')
chequeo('orden de lista: OR despues de HSS', DA.clave_orden(OR_RECT)[0] > DA.clave_orden(HSS)[0])

# Mismo enrutamiento que HSS: con la misma geometria y espesor, OR debe dar exactamente las mismas ecuaciones.
p_hss_como_or = dict(prop_or)   # mismas propiedades; solo cambia la familia que se pasa
chequeo('mn_fuerte(OR) == mn_fuerte(HSS) con la misma geometria',
        abs(DA.mn_fuerte(dict(prop_or), 'OR', FY, E_ACERO, G_ACERO, LB, 1.0)[0]
            - DA.mn_fuerte(p_hss_como_or, 'HSS', FY, E_ACERO, G_ACERO, LB, 1.0)[0]) < 1e-6)
chequeo('mn_debil(OR) == mn_debil(HSS)',
        abs(DA.mn_debil(dict(prop_or), 'OR', FY, E_ACERO)[0] - DA.mn_debil(dict(prop_or), 'HSS', FY, E_ACERO)[0]) < 1e-6)
chequeo('vn_fuerte(OR) == vn_fuerte(HSS) (G4)',
        abs(DA.vn_fuerte(dict(prop_or), 'OR', FY, E_ACERO)[0] - DA.vn_fuerte(dict(prop_or), 'HSS', FY, E_ACERO)[0]) < 1e-6)
chequeo('vn_debil(OR) == vn_debil(HSS) (G4)',
        abs(DA.vn_debil(dict(prop_or), 'OR', FY, E_ACERO)[0] - DA.vn_debil(dict(prop_or), 'HSS', FY, E_ACERO)[0]) < 1e-6)
tn, det = DA.torsion_hss(dict(prop_or), FY, E_ACERO)
chequeo(f'torsion H3.1 de OR calculable (Tn = {tn:.1f} kgf·cm)', math.isfinite(tn) and tn > 0)

# Perfil cuadrado: mismas ecuaciones
prop_cuad, falta_c = DA._props_asd(OR_CUAD, 'OR')
chequeo(f'cuadrado 51x1.9: propiedades completas ({falta_c})', prop_cuad is not None and not falta_c)
chequeo('cuadrado: Ix = Iy y Sx = Sy (seccion doblemente simetrica)',
        prop_cuad is not None and abs(prop_cuad['Ix'] - prop_cuad['Iy']) < 1e-9
        and abs(prop_cuad['Sx'] - prop_cuad['Sy']) < 1e-9)

print('FALLOS:', len(FALLOS))
sys.exit(1 if FALLOS else 0)
