"""Parametros de diseno (AISC 360-22, ASD). Vienen de las hojas PARAMETROS y NORMA de la planilla: no hay valores de
norma ni supuestos en este modulo. resolver() valida cada dato y devuelve la configuracion del calculo. Si falta un dato
o una opcion no es valida, devuelve errores y el diseno no se hace."""
import math

CAMPOS_REQUERIDOS = ['VIENTO', 'KZ_TORSION']
VIENTO_NO = 'NO'
NORMA_REQUERIDA = ['FLECHA_DIVISOR', 'PROY_KLR_COMP']


def _vacio(v):
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, float) and math.isnan(v))


def _numero(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def resolver(par, nor):
    """par: {CLAVE: valor} de la hoja PARAMETROS. nor: {'VALORES': {CLAVE: n}} de la hoja NORMA.
    Devuelve (conf, errores). errores vacio = datos completos."""
    errores = []
    for k in CAMPOS_REQUERIDOS:
        if _vacio(par.get(k)):
            errores.append(f'PARAMETROS {k}: falta el dato (elija de la lista o ingrese el valor)')
    if errores:
        return None, errores
    if str(par['VIENTO']).strip().upper() != VIENTO_NO:
        errores.append('PARAMETROS VIENTO: en esta version el viento no se considera (elija NO)')
    # DECISION D4 (abierta): Kz = 1.0 o 0.5 (AISC E4). El significado de cada opcion no esta confirmado.
    kz = _numero(par['KZ_TORSION'])
    if kz not in (1.0, 0.5):
        errores.append('PARAMETROS KZ_TORSION: elija 1.0 o 0.5 (factor Kz de pandeo torsional, AISC E4)')
    V = nor['VALORES']
    for k in NORMA_REQUERIDA:
        if k not in V:
            errores.append(f'NORMA {k}: falta el valor de norma en la hoja NORMA')
    if errores:
        return None, errores
    conf = dict(kz=kz, viento=VIENTO_NO, flecha_divisor=V['FLECHA_DIVISOR'], klr_limite=V['PROY_KLR_COMP'])
    return conf, []
