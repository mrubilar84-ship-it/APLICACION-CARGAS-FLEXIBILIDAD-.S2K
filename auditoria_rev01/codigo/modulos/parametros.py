"""Parametros de diseno y de norma. Vienen de las hojas PARAMETROS y NORMA de la planilla (no hay valores de norma
ni supuestos en este modulo). resolver() valida cada dato, convierte las opciones en numeros y devuelve la
configuracion del calculo. Si falta un dato o una opcion no es valida, devuelve errores y el diseno no se hace."""
import math

CAMPOS_REQUERIDOS = ['SISTEMA_SISMICO', 'CRUJIAS_AMBAS', 'ZONA_SISMICA', 'TS', 'TA', 'TB', 'K_SASID', 'C_SASID',
                     'KS_METODO', 'DEFORMABLES', 'FRAGILES', 'VIENTO', 'METODO', 'KZ_TORSION']
KS_CONSERVADOR = 'CONSERVADOR (Ks=1)'
KS_SEGUN_ZONA = 'SEGUN ZONA (ec. 3.1.1)'
METODO_ESTATICO = 'ESTÁTICO'
VIENTO_NO = 'NO'


def _vacio(v):
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, float) and math.isnan(v))


def _numero(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def _si_no(v):
    t = str(v).strip().upper()
    return {'SÍ': True, 'SI': True, 'NO': False}.get(t)


def resolver(par, nor):
    """par: {CLAVE: valor} de la hoja PARAMETROS. nor: {'SISTEMAS': {nombre: {Q, gSV, gOI, R0}}, 'VALORES': {CLAVE: n}}.
    Devuelve (conf, errores). errores vacio = datos completos."""
    errores = []
    for k in CAMPOS_REQUERIDOS:
        if _vacio(par.get(k)):
            errores.append(f'PARAMETROS {k}: falta el dato (elija de la lista o ingrese el valor)')
    if errores:
        return None, errores
    V = nor['VALORES']
    sistemas = nor['SISTEMAS']
    sistema = str(par['SISTEMA_SISMICO']).strip()
    if sistema not in sistemas:
        errores.append(f'PARAMETROS SISTEMA_SISMICO: "{sistema}" no esta en la lista de la hoja NORMA')
        return None, errores
    s = sistemas[sistema]
    crujias = _si_no(par['CRUJIAS_AMBAS'])
    if crujias is None:
        errores.append('PARAMETROS CRUJIAS_AMBAS: elija SÍ o NO')
    zona = str(par['ZONA_SISMICA']).strip().upper()
    if zona not in ('A', 'B', 'C'):
        errores.append('PARAMETROS ZONA_SISMICA: elija A, B o C')
    num = {}
    for k, nombre in [('TS', 'Ts'), ('TA', 'Ta'), ('TB', 'Tb'), ('K_SASID', 'k'), ('C_SASID', 'c')]:
        x = _numero(par[k])
        if x is None or x <= 0:
            errores.append(f'PARAMETROS {k}: {nombre} debe ser un numero mayor que cero (valor del SASID)')
        num[k] = x
    if not errores and num['TB'] <= num['TA']:
        errores.append('PARAMETROS TB: Tb debe ser mayor que Ta (valores del SASID)')
    ks_metodo = str(par['KS_METODO']).strip()
    if ks_metodo not in (KS_CONSERVADOR, KS_SEGUN_ZONA):
        errores.append(f'PARAMETROS KS_METODO: elija "{KS_CONSERVADOR}" o "{KS_SEGUN_ZONA}"')
    # DECISION D10 (abierta): DEFORMABLES = SÍ da LDNE 0.004 (NTC 1.7). Se eligio SÍ porque el proyecto no tiene frageles; confirmar.
    deformables = _si_no(par['DEFORMABLES'])
    fragiles = _si_no(par['FRAGILES'])
    if deformables is None:
        errores.append('PARAMETROS DEFORMABLES: elija SÍ o NO')
    if fragiles is None:
        errores.append('PARAMETROS FRAGILES: elija SÍ o NO')
    if str(par['VIENTO']).strip().upper() != VIENTO_NO:
        errores.append('PARAMETROS VIENTO: en esta version el viento no se considera (elija NO)')
    # DECISION D4 (abierta): Kz = 1.0 o 0.5 (AISC E4). El significado de cada opcion no esta confirmado.
    kz = _numero(par['KZ_TORSION'])
    if kz not in (1.0, 0.5):
        errores.append('PARAMETROS KZ_TORSION: elija 1.0 o 0.5 (factor Kz de pandeo torsional, AISC E4)')
    if str(par['METODO']).strip().upper() != METODO_ESTATICO:
        errores.append('PARAMETROS METODO: en esta version solo se usa el metodo estatico')
    if errores:
        return None, errores

    k1 = V['K1_SI'] if crujias else V['K1_NO']
    # DECISION D6 (abierta): Q' = 1 + (Q-1)/k con k del SASID. Con k = 1, Q' = Q. Si k < 1, Q' > Q (NTC 3.2, comentario).
    qp = 1.0 + (s['Q'] - 1.0) / num['K_SASID']                       # NTC 3.2.1 (rama Ta-Tb), con k del SASID
    if ks_metodo == KS_CONSERVADOR:
        # DECISION D7 (abierta): Ks = 1 por defecto (conservador). Alternativa: Ks por zona (tabla 3.1.1, eq. 3.1.1).
        ks, ks_txt = 1.0, 'Ks = 1 (conservador)'
    elif zona == 'A':
        ks, ks_txt = 1.0 / V['KS_A_DEN'], f'Ks = 1/{V["KS_A_DEN"]:g} (zona A)'
    elif zona == 'C':
        ks, ks_txt = 1.0 / V['KS_C_DEN'], f'Ks = 1/{V["KS_C_DEN"]:g} (zona C)'
    else:
        den = V['KS_B_A'] - V['KS_B_B'] * (num['TS'] - V['KS_B_C'])
        if den <= 0:
            errores.append('PARAMETROS TS: con Ts de la zona B, 1/[6-4(Ts-0.5)] no es valido; revise Ts')
            return None, errores
        ks, ks_txt = 1.0 / den, f'Ks = 1/[{V["KS_B_A"]:g}-{V["KS_B_B"]:g}(Ts-{V["KS_B_C"]:g})] (zona B)'
    conf = dict(
        sistema=sistema, Q=s['Q'], gSV=s['gSV'], gOI=s['gOI'], R0=s['R0'], k1=k1,
        crujias_ambas=crujias, zona=zona, ts=num['TS'], ta=num['TA'], tb=num['TB'],
        k_sasid=num['K_SASID'], c_sasid=num['C_SASID'], qp=qp,
        ks=ks, ks_metodo=ks_metodo, ks_txt=ks_txt,
        deformables=deformables, gLDNE=V['LDNE_DEFORMABLES'] if deformables else V['LDNE_NO'],
        fragiles=fragiles, lim_h=V['NTC_CA_H_FRAGILES'] if fragiles else V['NTC_CA_H_OTROS'],
        seg2=V['SEG2_FACTOR'], flecha_divisor=V['FLECHA_DIVISOR'],
        rp_sv=V['RP_SV'], rp_oi=V['RP_OI'], k2_coef=V['K2_COEF'], k2_exp=V['K2_EXP'], g=V['G'],
        viento=VIENTO_NO, metodo=METODO_ESTATICO, kz=kz)
    conf['R'] = k1 * s['R0']                                          # k2 se suma con el periodo (ver k2_de_T)
    return conf, []


def k2_de_T(T, conf):
    """k2 = 0.5 (1 - (T/Ta)^2) si T < Ta; 0 si T >= Ta (NTC 3.3.1b)."""
    if T is None or T >= conf['ta']:
        return 0.0
    return conf['k2_coef'] * (1.0 - (T / conf['ta']) ** conf['k2_exp'])
