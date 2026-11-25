"""Base de perfiles: Gerdau rev04, HSS del catalogo ATC y OR del catalogo IMCA (todos en la misma base)."""
import base64
import json
import zlib
from gerdau_datos import _DATOS_TEXTO

_DATOS = json.loads(zlib.decompress(base64.b64decode(_DATOS_TEXTO)).decode('utf-8'))   # texto comprimido (zlib + base64)
PERFILES = {p['perfil_comercial']: p for p in _DATOS}

FAMILIA_ORDEN = ['IR', 'CE', 'LI', 'HSS', 'OR']   # CS, OS y SOL (macizos) eliminados; OR: IMCA PTE (rect. y cuad.)


def obtener_perfil(nombre):
    """Dimensiones en cm: H = d (peralte o diametro), B = bf, e = tw, t = tf. None = dato pendiente."""
    p = PERFILES.get(nombre)
    if p is None:
        return None
    return {'familia': p['familia'], 'H': p['d_ala_diametro_cm'], 'B': p['bf_b_cm'],
            'e': p['tw_cm'], 't': p['tf_t_cm'], 'A': p['area_cm2'], 'Ix': p['ix_cm4'], 'Iy': p['iy_cm4'],
            'Sx': p['sx_cm3'], 'Sy': p['sy_cm3'], 'rx': p['rx_cm'], 'ry': p['ry_cm'], 'J': p['j_cm4'],
            'Cw': p['cw_cm6'], 'Zx': p.get('zx_cm3'), 'Zy': p.get('zy_cm3'), 'ro': p.get('ro_cm'),
            'estado': p['estado'], 'masa': p['masa_kg_m'], 'pagina_manual': p.get('pagina_manual'),
            'fuente_completado': p.get('fuente_completado'), 'seccion': p.get('seccion'),
            'pagina_catalogo_atc': p.get('pagina_catalogo_atc'), 'referencia_catalogo': p.get('referencia_catalogo'),
            'fuente_propiedades': p.get('fuente_propiedades'),
            'alerta_catalogo': p.get('alerta_catalogo'), 'campos_pendientes': p.get('campos_pendientes')}


def _clave_seccion(p):
    """Familia, luego peralte (o diametro/lado), masa (mas liviano primero), ancho. Nulos al final."""
    def k(v):
        return (v is None, v or 0)
    return (FAMILIA_ORDEN.index(p['familia']),
            k(p['d_ala_diametro_cm']), k(p['masa_kg_m']), k(p['bf_b_cm']),
            p['perfil_comercial'])


def lista_perfiles_ordenada():
    """[(etiqueta, nombre)] para la lista desplegable. Muestra masa y estado si no es Revisado."""
    out = []
    for p in sorted(_DATOS, key=_clave_seccion):
        masa = '' if p['masa_kg_m'] is None else f"   {p['masa_kg_m']:g} kg/m"
        estado = '' if p['estado'] == 'Revisado' else f"   [{p['estado']}]"
        out.append((f"{p['perfil_comercial']}{masa}{estado}", p['perfil_comercial']))
    return out
