# celda 15 del notebook; bloque anterior: ## Bloque 7. Leer, validar y armar el modelo
# Leer la planilla llenada, validar y armar el modelo
import glob
import os
import numpy as np
import pandas as pd
from dibujo_directo import DibujoModelo, ELEMENTOS, TIPOS_CONEXION, GRADOS

TOL = 1e-3
EJE_COLS = ['EJE_FUERTE_X', 'EJE_FUERTE_Y', 'EJE_FUERTE_Z']


def _vacio(v):
    return v is None or (isinstance(v, float) and np.isnan(v)) or str(v).strip() == ''


def _col(fila, nombre):
    """Valor de una columna; None si la planilla no tiene esa columna (planillas anteriores)."""
    return fila[nombre] if nombre in fila.index else None


def _tipo(v):
    return '' if _vacio(v) else str(v).strip().lower()


def buscar_planilla():
    """Busca la planilla llenada en /kaggle/input (archivos .xlsx con 'soportes' en el nombre). Si hay mas de una se
    detiene: no se elige una al azar (R-09). Si no hay ninguna, usa la plantilla de ejemplo."""
    subidas = sorted(f for f in glob.glob('/kaggle/input/**/*.xlsx', recursive=True)
                     if 'soportes' in os.path.basename(f).lower())
    if len(subidas) > 1:
        raise RuntimeError(f'Hay {len(subidas)} planillas con "soportes" en /kaggle/input: deje solo una. '
                           + '; '.join(subidas))
    return subidas[0] if subidas else RUTA_PLANTILLA


def leer_perfil_grupo(ruta):
    """Perfil elegido por grupo (hoja PERFIL_GRUPO de la planilla con diseno): {GRUPO: PERFIL}. {} si no existe."""
    try:
        g = pd.read_excel(ruta, sheet_name='PERFIL_GRUPO', dtype=object)
    except Exception:
        return {}
    salida = {}
    for _, r in g.iterrows():
        if not _vacio(r.get('GRUPO')) and not _vacio(r.get('PERFIL ELEGIDO')):
            salida[str(r['GRUPO']).strip().upper()] = str(r['PERFIL ELEGIDO']).strip()
    return salida


def leer_planilla(ruta):
    nodos = pd.read_excel(ruta, sheet_name='NODOS', dtype=object)
    barras = pd.read_excel(ruta, sheet_name='BARRAS', dtype=object)
    nodos = nodos[[not all(_vacio(v) for v in fila) for fila in nodos[['ID', 'X (m)', 'Y (m)', 'Z (m)']].values]]
    barras = barras[[not all(_vacio(v) for v in fila) for fila in barras[['ID', 'NODO_I', 'NODO_J']].values]]
    if 'DUCTILIDAD' not in barras.columns:          # planilla anterior: sin la columna DUCTILIDAD
        barras = barras.assign(DUCTILIDAD=None)
    # Con diseno, el perfil de cada barra lo da su grupo (PERFIL_GRUPO); la celda PERFIL de BARRAS es una formula.
    grupos = leer_perfil_grupo(ruta)
    if grupos:
        barras = barras.copy()
        barras['PERFIL'] = [grupos.get(str(e).strip().upper(), p) for e, p in zip(barras['ELEMENTO'], barras['PERFIL'])]
    return nodos, barras


def leer_materiales(ruta):
    """Hoja MATERIALES de la planilla, normalizada a [NOMBRE, TIPO, FY, FU, E, NU, FUENTE]. None si la planilla no
    tiene la hoja. Una columna que no exista (planilla anterior) queda vacia: el analisis la marca como error."""
    try:
        m = pd.read_excel(ruta, sheet_name='MATERIALES', dtype=object)
    except Exception:
        return None
    cols = {str(c).split(' (')[0].strip().upper(): c for c in m.columns}
    orden = ['NOMBRE', 'TIPO', 'FY', 'FU', 'E', 'NU', 'FUENTE']
    salida = []
    for _, r in m.iterrows():
        nombre = r[cols['NOMBRE']] if 'NOMBRE' in cols else r.iloc[0]
        if _vacio(nombre):
            continue
        salida.append([None if (k not in cols or _vacio(r[cols[k]])) else r[cols[k]] for k in orden])
    return salida


def _letra(n):
    from openpyxl.utils import get_column_letter
    return get_column_letter(n)


def leer_combinaciones(ruta, estados):
    """Hoja COMBINACIONES (informacion para el notebook). Devuelve (filas_crudas, combinaciones, mensajes):
    filas_crudas = factores tal como estan en la hoja (40 x 30); combinaciones = {nombre: {estado: factor}}."""
    msgs = []
    try:
        import openpyxl
        ws = openpyxl.load_workbook(ruta, data_only=False)['COMBINACIONES']
    except Exception:
        return [], {}, msgs
    nombres_estado = [str(v).strip() if not _vacio(v) else None for v in estados['NOMBRE'].values]
    filas_crudas, combinaciones = [], {}
    for k in range(40):
        fila_excel = 3 + k
        crudo = [ws.cell(row=fila_excel, column=2 + j).value for j in range(30)]
        filas_crudas.append(crudo)
        factores = {}
        for j, v in enumerate(crudo):
            if _vacio(v):
                continue
            try:
                f = float(v)
            except (TypeError, ValueError):
                msgs.append(('COMBINACIONES', fila_excel, 'ERROR', f'factor no numerico en la columna {_letra(2 + j)}'))
                continue
            if f == 0:
                continue
            if j >= len(nombres_estado) or nombres_estado[j] is None:
                msgs.append(('COMBINACIONES', fila_excel, 'ERROR', f'factor {f} en la columna {_letra(2 + j)}, que no tiene estado en ESTADOS'))
                continue
            factores[nombres_estado[j]] = f
        if factores:
            combinaciones[f'ASD{k + 1}'] = factores
    return filas_crudas, combinaciones, msgs


def validar(nodos, barras):
    """Lista de (hoja, fila_excel, tipo, mensaje). ERROR = no se arma el modelo; AVISO = informativo."""
    msgs = []
    def avisar(hoja, fila, tipo, texto):
        msgs.append((hoja, fila, tipo, texto))

    ids, coords = {}, []
    for k, r in nodos.iterrows():
        fila = k + 2
        try:
            id_ = int(float(r['ID']))
        except (TypeError, ValueError):
            avisar('NODOS', fila, 'ERROR', 'ID no es un entero'); continue
        if id_ in ids:
            avisar('NODOS', fila, 'ERROR', f'ID {id_} repetido'); continue
        try:
            p = (float(r['X (m)']), float(r['Y (m)']), float(r['Z (m)']))
        except (TypeError, ValueError):
            avisar('NODOS', fila, 'ERROR', 'coordenada X, Y o Z no numerica'); continue
        for q_id, q in coords:
            if all(abs(p[c] - q[c]) < TOL for c in range(3)):
                avisar('NODOS', fila, 'ERROR', f'coincide con el nodo {q_id}')
        ids[id_] = p
        coords.append((id_, p))
        for g in GRADOS:
            if _tipo(_col(r, g)) not in ('', 'si', 'no'):
                avisar('NODOS', fila, 'ERROR', f"{g} '{_col(r, g)}' no reconocido (use SI o NO; vacio = libre)")
        if _tipo(_col(r, 'REPORTAR')) not in ('', 'si', 'no'):
            avisar('NODOS', fila, 'AVISO', "REPORTAR debe ser SI o vacio: este nodo no sale en el Excel de resultados")

    vistos = set()
    for k, r in barras.iterrows():
        fila = k + 2
        try:
            n1, n2 = int(float(r['NODO_I'])), int(float(r['NODO_J']))
        except (TypeError, ValueError):
            avisar('BARRAS', fila, 'ERROR', 'NODO_I o NODO_J no es un entero'); continue
        if n1 not in ids or n2 not in ids:
            avisar('BARRAS', fila, 'ERROR', f'nodo inexistente en NODOS ({n1} o {n2})'); continue
        if n1 == n2:
            avisar('BARRAS', fila, 'ERROR', 'barra de un nodo consigo mismo'); continue
        par = frozenset((n1, n2))
        if par in vistos:
            avisar('BARRAS', fila, 'AVISO', f'barra {n1}-{n2} repetida: se ignora')
        vistos.add(par)
        elem = str(r['ELEMENTO']).strip().upper()
        if elem not in ELEMENTOS:
            avisar('BARRAS', fila, 'ERROR', f"ELEMENTO '{r['ELEMENTO']}' no reconocido")
        perfil = str(r['PERFIL']).strip()
        if perfil not in G.PERFILES:
            avisar('BARRAS', fila, 'ERROR', f"PERFIL '{perfil}' no existe en la base Gerdau")
        else:
            p = G.PERFILES[perfil]
            if p['d_ala_diametro_cm'] is None or p['bf_b_cm'] is None:
                avisar('BARRAS', fila, 'AVISO', f"perfil {perfil} sin dato geometrico (estado: {p['estado']})")
        # eje fuerte: vector libre. Una componente basta: las vacias valen 0. Todas vacias = por defecto.
        vec = [_col(r, c) for c in EJE_COLS]
        if any(not _vacio(v) for v in vec):
            try:
                v = np.array([0.0 if _vacio(x) else float(x) for x in vec])
            except (TypeError, ValueError):
                avisar('BARRAS', fila, 'ERROR', 'componente del eje fuerte no numerica'); v = None
            if v is not None:
                nv = np.linalg.norm(v)
                if nv < 1e-9:
                    avisar('BARRAS', fila, 'ERROR', 'eje fuerte nulo: indique una direccion o deje las tres vacias')
                elif n1 in ids and n2 in ids:
                    d = np.array(ids[n2]) - np.array(ids[n1])
                    if abs(np.dot(v / nv, d / np.linalg.norm(d))) > 0.999:
                        avisar('BARRAS', fila, 'ERROR', 'eje fuerte paralelo a la barra: elija otra direccion')
        material = '' if _vacio(_col(r, 'MATERIAL')) else str(_col(r, 'MATERIAL')).strip()
        if not material:
            avisar('BARRAS', fila, 'ERROR', 'falta MATERIAL: elija una calidad de la lista (hoja MATERIALES)')
        elif material not in MATERIALES_VALIDOS:
            avisar('BARRAS', fila, 'ERROR', f"MATERIAL '{material}' no existe en la hoja MATERIALES")
        duct_b = _col(r, 'DUCTILIDAD')
        if not _vacio(duct_b) and str(duct_b).strip().upper() not in ('ALTA', 'MEDIA'):
            avisar('BARRAS', fila, 'ERROR', 'DUCTILIDAD debe ser ALTA, MEDIA o vacio')
        for col in ('CONEXION_I', 'CONEXION_J'):
            c = _tipo(_col(r, col))
            if c and c not in TIPOS_CONEXION:
                avisar('BARRAS', fila, 'ERROR', f"{col} '{_col(r, col)}' no reconocida (use empotrado, rotulado o vacio)")
        if _tipo(_col(r, 'REPORTAR')) not in ('', 'si', 'no'):
            avisar('BARRAS', fila, 'AVISO', "REPORTAR debe ser SI o vacio: esta barra no sale en el Excel de resultados")
    return msgs


def construir_modelo(nodos, barras):
    """Arma el DibujoModelo con los IDs de la planilla. Devuelve (dib, id_de_indice, mensajes)."""
    dib = DibujoModelo(ruta=RUTA_PLANILLA_LEIDA)
    mapa, msgs = {}, []
    id_barra = {}                       # indice de barra en el modelo -> ID de la hoja BARRAS
    for _, r in nodos.iterrows():
        mapa[int(float(r['ID']))] = dib.nodo(float(r['X (m)']), float(r['Y (m)']), float(r['Z (m)']))
    for _, r in barras.iterrows():
        n1, n2 = mapa[int(float(r['NODO_I']))], mapa[int(float(r['NODO_J']))]
        ci = _tipo(_col(r, 'CONEXION_I')) or 'empotrado'
        cj = _tipo(_col(r, 'CONEXION_J')) or 'empotrado'
        material = '' if _vacio(_col(r, 'MATERIAL')) else str(_col(r, 'MATERIAL')).strip()
        try:
            idx = dib.barra(n1, n2, str(r['ELEMENTO']).strip().upper(), str(r['PERFIL']).strip(),
                            conexion_i=ci, conexion_j=cj, material=material)
        except ValueError as e:
            msgs.append(('BARRAS', int(float(r['ID'])), 'ERROR', str(e))); continue
        vec = [_col(r, c) for c in EJE_COLS]
        if idx is not None:
            id_barra[idx] = int(float(r['ID']))
        if idx is not None and any(not _vacio(v) for v in vec):
            try:
                dib.eje_fuerte(idx, tuple(0.0 if _vacio(v) else float(v) for v in vec))
            except ValueError as e:
                msgs.append(('BARRAS', int(float(r['ID'])), 'ERROR', str(e)))
    for _, r in nodos.iterrows():
        restr = [_tipo(_col(r, g)) == 'si' for g in GRADOS]          # UX, UY, UZ, RX, RY, RZ marcados SI
        if any(restr):
            dib.apoyo(mapa[int(float(r['ID']))], restr)
    id_de_indice = {idx: id_ for id_, idx in mapa.items()}
    dib.id_barra_de_indice = id_barra
    return dib, id_de_indice, msgs


CARGA_FILA0 = 9
CARGA_COLS_LEER = ['ID', 'ESTADO', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ', 'NOTA']


def leer_cargas(ruta):
    """Hoja CARGAS: una fila por nodo y estado. FX, FY, FZ en kgf; MX, MY, MZ en kgf·m (ejes globales X, Y, Z)."""
    try:
        c = pd.read_excel(ruta, sheet_name='CARGAS', header=CARGA_FILA0 - 2, dtype=object)
    except Exception:
        return pd.DataFrame(columns=CARGA_COLS_LEER)
    c = c.iloc[:, :9]
    c.columns = CARGA_COLS_LEER
    return c[[not all(_vacio(v) for v in fila) for fila in c[['ID', 'ESTADO']].values]]


def leer_estados(ruta):
    """Hoja ESTADOS: nombre del estado (lo define el usuario), tipo, descripcion y PESO PROPIO (SI/NO).
    Si la planilla no tiene la columna PESO PROPIO (planilla anterior), queda vacia: el analisis la marca."""
    columnas = ['NOMBRE', 'TIPO', 'DESCRIPCION', 'PESO PROPIO']
    try:
        e = pd.read_excel(ruta, sheet_name='ESTADOS', dtype=object)
    except Exception:
        return pd.DataFrame(columns=columnas)
    filas = []
    for _, r in e.iterrows():
        if _vacio(r.iloc[0]):
            continue
        pp = r.iloc[3] if e.shape[1] > 3 and str(e.columns[3]).strip().upper().startswith('PESO') else None
        filas.append([r.iloc[0], r.iloc[1] if e.shape[1] > 1 else None,
                      r.iloc[2] if e.shape[1] > 2 else None, pp])
    return pd.DataFrame(filas, columns=columnas)


def leer_longitudes(ruta):
    """Hoja LONGITUDES: filas alineadas con BARRAS (fila 2 = primera barra). Vacia si la planilla no la tiene.
    Las columnas se leen por nombre: una planilla anterior sin las columnas nuevas las toma vacias (NO / supuesto)."""
    try:
        l = pd.read_excel(ruta, sheet_name='LONGITUDES', dtype=object)
    except Exception:
        return pd.DataFrame(columns=LONG_COLS)
    l = l.reindex(columns=LONG_COLS)        # por nombre; columnas que falten quedan vacias
    # el ID sale de BARRAS (formula). Si el archivo no trae el valor calculado, se toma por posicion de fila.
    try:
        ids_barras = pd.read_excel(ruta, sheet_name='BARRAS', dtype=object)['ID'].tolist()
    except Exception:
        ids_barras = []
    ids = []
    for k in range(len(l)):
        v = l['ID'].iloc[k]
        ids.append(v if not _vacio(v) else (ids_barras[k] if k < len(ids_barras) else None))
    l['ID'] = ids
    return l


def leer_parametros(ruta):
    """Hoja PARAMETROS: {CLAVE: valor} (columna VALOR). None si la planilla no tiene la hoja (plantilla anterior)."""
    import openpyxl
    try:
        ws = openpyxl.load_workbook(ruta, data_only=True)['PARAMETROS']
    except KeyError:
        return None
    par = {}
    for fila in range(5, ws.max_row + 1):
        clave = ws.cell(row=fila, column=1).value
        if _vacio(clave):
            continue
        par[str(clave).strip()] = ws.cell(row=fila, column=3).value
    return par


def leer_norma(ruta):
    """Hoja NORMA: {'SISTEMAS': {nombre: {Q, gSV, gOI, R0}}, 'VALORES': {CLAVE: valor}}. None si falta la hoja."""
    import openpyxl
    try:
        ws = openpyxl.load_workbook(ruta, data_only=True)['NORMA']
    except KeyError:
        return None
    sistemas, valores, modo = {}, {}, None
    for fila in range(1, ws.max_row + 1):
        a = ws.cell(row=fila, column=1).value
        if _vacio(a):
            continue
        t = str(a).strip()
        if t == 'NOMBRE DEL SISTEMA':
            modo = 'S'
            continue
        if t == 'CLAVE':
            modo = 'V'
            continue
        if t.startswith(('NORMA:', 'SISTEMAS ESTRUCTURALES', 'VALORES DE NORMA')):
            modo = None
            continue
        if modo == 'S':
            sistemas[t] = {'Q': float(ws.cell(row=fila, column=2).value), 'gSV': float(ws.cell(row=fila, column=3).value),
                           'gOI': float(ws.cell(row=fila, column=4).value), 'R0': float(ws.cell(row=fila, column=5).value)}
        elif modo == 'V':
            valores[t] = float(ws.cell(row=fila, column=2).value)
    return {'SISTEMAS': sistemas, 'VALORES': valores}


def validar_datos_diseno(barras, longitudes):
    """Datos obligatorios para el diseno de cada barra: LX, LY, LB, KX, KY, CB en LONGITUDES y DUCTILIDAD en
    columnas y vigas (BARRAS). Sin estos datos no se supone nada: aparece como ERROR."""
    msgs = []
    lon = {int(float(r['ID'])): r for _, r in longitudes.iterrows() if not _vacio(r['ID'])}
    for k, r in barras.iterrows():
        if _vacio(r['ID']):
            continue
        id_ = int(float(r['ID']))
        fila = k + 2
        lr = lon.get(id_)
        # DECISION D17 (abierta): LX, LY, LB, KX, KY y CB obligatorios; alternativa: valores por defecto marcados.
        for campo in ['LX (m)', 'LY (m)', 'LB (m)', 'KX', 'KY', 'CB']:
            if lr is None or _vacio(lr[campo]):
                msgs.append(('LONGITUDES', fila, 'ERROR', f'barra {id_}: falta {campo} (dato obligatorio para el diseno)'))
        elemento = str(r['ELEMENTO']).strip().upper() if not _vacio(r['ELEMENTO']) else ''
        # DECISION D19 (abierta): DUCTILIDAD obligatoria solo en COLUMNA y VIGA; ARRIOSTRE y DIAGONAL opcionales.
        if elemento in ('COLUMNA', 'VIGA') and _vacio(r['DUCTILIDAD']):
            msgs.append(('BARRAS', fila, 'ERROR', f'barra {id_} ({elemento}): falta DUCTILIDAD (ALTA o MEDIA)'))
    return msgs


def leer_filas_parametros(ruta):
    """Filas de PARAMETROS para la memoria: (concepto, clave, valor, unidad, referencia)."""
    import openpyxl
    try:
        ws = openpyxl.load_workbook(ruta, data_only=True)['PARAMETROS']
    except KeyError:
        return []
    filas = []
    for fila in range(5, ws.max_row + 1):
        clave = ws.cell(row=fila, column=1).value
        if _vacio(clave):
            continue
        vacio_a = lambda v: '' if v is None else v
        filas.append((vacio_a(ws.cell(row=fila, column=2).value), str(clave).strip(),
                      vacio_a(ws.cell(row=fila, column=3).value), vacio_a(ws.cell(row=fila, column=4).value),
                      vacio_a(ws.cell(row=fila, column=6).value)))
    return filas


def leer_filas_norma(ruta):
    """Filas de NORMA (valores de norma) para la memoria: (clave, valor, unidad, referencia)."""
    import openpyxl
    try:
        ws = openpyxl.load_workbook(ruta, data_only=True)['NORMA']
    except KeyError:
        return []
    filas, en_valores = [], False
    for fila in range(1, ws.max_row + 1):
        a = ws.cell(row=fila, column=1).value
        if _vacio(a):
            continue
        t = str(a).strip()
        if t == 'CLAVE':
            en_valores = True
            continue
        v = ws.cell(row=fila, column=2).value
        if en_valores and isinstance(v, (int, float)):
            filas.append((t, float(v), ws.cell(row=fila, column=3).value or '', ws.cell(row=fila, column=4).value or ''))
    return filas


def validar_longitudes(longitudes):
    """Valores de LONGITUDES: numericos y mayores que cero. Vacio no es error: el diseño lo marca como supuesto."""
    msgs = []
    campos = ['LX (m)', 'LY (m)', 'KX', 'KY', 'LB (m)', 'CB']
    for k, r in longitudes.iterrows():
        fila = k + 2
        if _vacio(r['ID']):
            if any(not _vacio(r[c]) for c in campos):
                msgs.append(('LONGITUDES', fila, 'AVISO', 'hay valores en una fila sin barra en BARRAS: no se usan'))
            continue
        for c in ['E5 UNA PATA', 'E5 UNION SOLDADA O 2 PERNOS', 'E5 SIN CARGA INTERMEDIA', 'E5 INDIVIDUAL O ALMA DE ARMADURA']:
            if not _vacio(r[c]) and str(r[c]).strip().upper() not in ('SI', 'NO'):
                msgs.append(('LONGITUDES', fila, 'ERROR', f'{c} debe ser SI, NO o vacio'))
        if not _vacio(r['LI CONEXION']) and str(r['LI CONEXION']).strip().upper() not in ('UNA PATA', 'DOS PATAS'):
            msgs.append(('LONGITUDES', fila, 'ERROR', 'LI CONEXION debe ser UNA PATA, DOS PATAS o vacio'))
        for c in campos:
            if _vacio(r[c]):
                continue
            try:
                v = float(r[c])
            except (TypeError, ValueError):
                msgs.append(('LONGITUDES', fila, 'ERROR', f'{c} no es numerico'))
                continue
            if v <= 0:
                msgs.append(('LONGITUDES', fila, 'ERROR', f'{c} debe ser mayor que cero'))
    return msgs


def validar_cargas(cargas, estados, ids_nodo):
    """Valida CARGAS contra NODOS y ESTADOS. Devuelve (mensajes, sumas) con sumas[(id_nodo, estado)] = [6 valores]."""
    msgs, sumas = [], {}
    nombres = {str(v).strip() for v in estados['NOMBRE'].values if not _vacio(v)}
    for k, r in cargas.iterrows():
        fila = k + CARGA_FILA0
        try:
            id_ = int(float(r['ID']))
        except (TypeError, ValueError):
            msgs.append(('CARGAS', fila, 'ERROR', 'ID NODO no es un entero'))
            continue
        if id_ not in ids_nodo:
            msgs.append(('CARGAS', fila, 'ERROR', f'el nodo {id_} no existe en NODOS'))
            continue
        est = str(r['ESTADO']).strip()
        if est not in nombres:
            msgs.append(('CARGAS', fila, 'ERROR', f"el estado '{est}' no existe en la hoja ESTADOS"))
            continue
        try:
            valores = [0.0 if _vacio(r[c]) else float(r[c]) for c in ['FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']]
        except (TypeError, ValueError):
            msgs.append(('CARGAS', fila, 'ERROR', 'fuerza o momento no numerico'))
            continue
        clave = (id_, est)
        if clave in sumas:
            msgs.append(('CARGAS', fila, 'AVISO', f'el nodo {id_} ya tiene el estado {est}: se suman'))
            sumas[clave] = [a + b for a, b in zip(sumas[clave], valores)]
        else:
            sumas[clave] = valores
    return msgs, sumas


def adjuntar_cargas(dib, sumas, id_de_indice):
    """dib.cargas = {estado: {indice_nodo: [Fx, Fy, Fz (kgf), Mx, My, Mz (kgf·cm)]}}.
    Los momentos se pasan de kgf·m a kgf·cm porque el motor de OpenSees trabaja en kgf y kgf·cm."""
    idx_de_id = {v: k for k, v in id_de_indice.items()}
    dib.cargas = {}
    for (id_, est), v in sumas.items():
        fx, fy, fz, mx, my, mz = v
        dib.cargas.setdefault(est, {})[idx_de_id[id_]] = [fx, fy, fz, mx * 100.0, my * 100.0, mz * 100.0]


def filas_longitudes_para_excel(longitudes):
    """Filas de la hoja LONGITUDES (todas las columnas salvo ID, que es formula), para regenerar el Excel."""
    filas = []
    for _, r in longitudes.iterrows():
        filas.append([None if _vacio(r[c]) else r[c] for c in LONG_COLS[1:]])
    return filas


def filas_cargas_para_excel(cargas):
    """Filas de la hoja CARGAS para regenerar el Excel con sus datos."""
    filas = []
    for _, r in cargas.iterrows():
        try:
            id_ = int(float(r['ID']))
        except (TypeError, ValueError):
            id_ = None
        vals = [0.0 if _vacio(r[c]) else float(r[c]) for c in ['FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']]
        filas.append([id_, None if _vacio(r['ESTADO']) else str(r['ESTADO']).strip(), *vals,
                      None if _vacio(r['NOTA']) else r['NOTA']])
    return filas


RUTA_PLANILLA_LEIDA = buscar_planilla()   # o escriba la ruta exacta, por ejemplo '/kaggle/input/mi-dataset/mis_soportes.xlsx'
print('Planilla que se lee:', RUTA_PLANILLA_LEIDA)
nodos, barras = leer_planilla(RUTA_PLANILLA_LEIDA)
materiales_leidos = leer_materiales(RUTA_PLANILLA_LEIDA)     # None = la planilla no tiene la hoja MATERIALES
materiales_filas = materiales_leidos or MATERIALES_DEFAULT   # solo para dibujar y validar nombres; el analisis usa materiales_leidos
MATERIALES_VALIDOS = {str(f[0]).strip() for f in materiales_filas}
mensajes = validar(nodos, barras)
cargas = leer_cargas(RUTA_PLANILLA_LEIDA)
estados_df = leer_estados(RUTA_PLANILLA_LEIDA)
longitudes_df = leer_longitudes(RUTA_PLANILLA_LEIDA)
# DUCTILIDAD (ALTA o MEDIA) se marca en BARRAS; el diseno la lee por ID desde la tabla de longitudes
_duct_por_id = {int(float(r['ID'])): r['DUCTILIDAD'] for _, r in barras.iterrows() if not _vacio(r['ID'])}
longitudes_df['DUCTILIDAD'] = [None if _vacio(v) else _duct_por_id.get(int(float(v)), None)
                               for v in longitudes_df['ID']]
ids_nodo = set()
for _v in nodos['ID'].values:
    try:
        ids_nodo.add(int(float(_v)))
    except (TypeError, ValueError):
        pass
msgs_cargas, sumas_cargas = validar_cargas(cargas, estados_df, ids_nodo)
mensajes += msgs_cargas
comb_crudas, combinaciones_modelo, msgs_comb = leer_combinaciones(RUTA_PLANILLA_LEIDA, estados_df)
mensajes += msgs_comb
mensajes += validar_longitudes(longitudes_df)
mensajes += validar_datos_diseno(barras, longitudes_df)
import parametros as P
PAR_LEIDA = leer_parametros(RUTA_PLANILLA_LEIDA)     # hoja PARAMETROS (listas desplegables del Excel)
NOR_LEIDA = leer_norma(RUTA_PLANILLA_LEIDA)          # hoja NORMA (valores de norma con su referencia)
CONF = None
if PAR_LEIDA is None or NOR_LEIDA is None:
    mensajes.append(('PARAMETROS', '', 'ERROR', 'la planilla no tiene las hojas PARAMETROS y NORMA: use la plantilla nueva'))
else:
    CONF, errores_par = P.resolver(PAR_LEIDA, NOR_LEIDA)
    mensajes += [('PARAMETROS', '', 'ERROR', e) for e in errores_par]
    if CONF is not None:
        CONF['par_filas'] = leer_filas_parametros(RUTA_PLANILLA_LEIDA)
        CONF['nor_filas'] = leer_filas_norma(RUTA_PLANILLA_LEIDA)
dib, id_de_indice, extra = (None, None, [])
if not any(t == 'ERROR' for _, _, t, _ in mensajes):
    dib, id_de_indice, extra = construir_modelo(nodos, barras)
    mensajes += extra
    if any(t == 'ERROR' for _, _, t, _ in extra):
        dib = None                  # un error al construir deja el modelo incompleto: no se entrega
if dib is not None:
    adjuntar_cargas(dib, sumas_cargas, id_de_indice)
    dib.combinaciones = combinaciones_modelo          # informacion para el notebook: {nombre: {estado: factor}}
    print(f'Combinaciones de carga: {len(combinaciones_modelo)}')
    print('Estados de carga:', [str(v) for v in estados_df['NOMBRE'].values])
    print(f'Asignaciones nodo-estado: {len(sumas_cargas)}')
resumen = pd.DataFrame(mensajes, columns=['hoja', 'fila_excel', 'tipo', 'mensaje'])
if resumen.empty:
    print('Planilla sin observaciones.')
else:
    display(resumen)
if dib is not None:
    print(f'Modelo armado: {len(dib.nodos)} nodos, {len(dib.barras)} barras, {len(dib.apoyos)} apoyos')
    modelo = dib.a_modelo()        # formato leer_dxf(): listo para el motor de analisis
else:
    print('Modelo NO armado: corrija los ERROR de la tabla y vuelva a ejecutar este bloque.')
