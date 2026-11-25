"""Genera datos/perfiles_or_imca.json (familia OR, IMCA: PTE rectangular y PTE cuadrado) desde las transcripciones.

Uso:  python3 extraer_or_imca.py          (no necesita el PDF; lee los .txt de esta carpeta)

Fuente: "Perfiles OR" IMCA, PDF d58fbb75-PERFILES_OR.pdf (sha256 abajo). Las transcripciones se hicieron a mano desde
las paginas escaneadas (PDF 1 a 16); cada fila se comprobo con relaciones geometricas (ver or_check):
  - or_imca_rect_xx.txt: rectangulares, eje X-X:  d b t_nom | pulg | tdis kgm lbft A bt ht | Ix Zx Sx rx
  - or_imca_rect_yy.txt: rectangulares, eje Y-Y:  d b t_nom | Iy Zy Sy ry | J C
  - or_imca_cuadrado.txt: cuadrados (PTE CUADRADO, PDF 13 a 16): lado t | pulg | tdis kgm lbft A bt | I Z S r | J C

Reglas (decisiones del usuario):
- Diseno con el espesor de diseno tal como aparece en la tabla (tdis, cm). No se aplica el factor AISC B4.2 (0.93):
  el factor es solo de HSS. Los valores A, I, S, Z, r y J son los impresos (ya corresponden a tdis).
- Peso propio: kg/m impreso (peso nominal).
- Nombre: "OR {d}x{b}x{t}x{kg/m} (kgf/m)" para rectangulares y "OR {lado}x{t}x{kg/m} (kgf/m)" para cuadrados;
  d, b y t en mm como se imprimen (t es el espesor nominal) y kg/m con los decimales impresos.
- Dimensiones de la base en cm: H = d (o lado), B = b (o lado), e = t = tdis (cm).
- Filas con valores que no cuadran entre si se conservan tal cual impresas y van con 'alerta_catalogo' (la alerta llega
  a los resultados de diseno); no se corrigen.
"""
import hashlib
import json
import os

D = os.path.dirname(os.path.abspath(__file__))
PDF_SHA256 = '0d8bfce20217f1e818e1d37db6cf412f6f25af690f3ec63b7c378419b29d557e'
REFERENCIA = 'IMCA, Perfiles OR (PTE rectangular y PTE cuadrado), PDF d58fbb75-PERFILES_OR.pdf'
ESTADO = 'Catalogo IMCA (OR)'

# Filas con valores que no cuadran entre si (ver transcripcion). Clave: (d o lado, b o t_label, t_nom o tdis?)
ALERTA_RECT = {
    '305x51': 'Revisar: kg/m y A no cuadran con el resto de la familia (kg/m/A = 0.785; las demas filas 0.82 a 0.85). '
              'Dato tal como aparece en la tabla impresa.',
    '305x76': 'Revisar: I menor que la de 305x51 pese a ser mas ancha, y ry no coincide con sqrt(Iy/A). '
              'Dato tal como aparece en la tabla impresa.',
    '610x305': 'Revisar: kg/m/A = 0.785 (las demas filas 0.82 a 0.85). Dato tal como aparece en la tabla impresa.',
}
ALERTA_CUAD = {
    '89x2.7': 'Revisar: el espesor de diseno impreso (0.28) corresponde a la fila siguiente de la tabla; A, I y kg/m son '
              'consistentes con ese espesor. Dato tal como aparece.',
    '89x3.0': 'Revisar: el espesor de diseno impreso (0.32) corresponde a la fila siguiente de la tabla; A, I y kg/m son '
              'consistentes con ese espesor. Dato tal como aparece.',
    '89x3.4': 'Revisar: el espesor de diseno impreso (0.35) corresponde a la fila siguiente de la tabla; A, I y kg/m son '
              'consistentes con ese espesor. Dato tal como aparece.',
    '89x3.8': 'Revisar: el espesor de diseno impreso (0.39) corresponde a la fila siguiente de la tabla; A, I y kg/m son '
              'consistentes con ese espesor. Dato tal como aparece.',
    '89x4.2': 'Revisar: el espesor de diseno impreso (0.43) corresponde a la fila siguiente de la tabla; A, I y kg/m son '
              'consistentes con ese espesor. Dato tal como aparece.',
    '89x4.6': 'Revisar: valores identicos a 76x4.8 (I 103.0, kg/m 10.22, A 12.21); no encajan con 89x4.2 ni 89x4.8. '
              'Dato tal como aparece.',
    '89x4.8': 'Revisar: espesor de diseno impreso 0.49 (el patron de la familia daria 0.44). Dato tal como aparece.',
    '127x3.2:1': 'Revisar: la etiqueta 3.2 y las pulgadas 5x1/8 no coinciden con el espesor de diseno 0.18, el area 8.79 '
                 'y la inercia 228.8 (corresponden a ~1.9 mm). Dato tal como aparece.',
    '127x3.4': 'Revisar: valores identicos a 114x3.4 (I 283.6, S 49.6, kg/m 11.70, A 13.91); no encajan con 127x3.2 '
               'ni 127x3.8. Dato tal como aparece.',
    '559x19.1': 'Revisar: etiqueta 19.1 (3/4 pulg) pero espesor de diseno 1.18, A 254.83 y b/t 44.31 corresponden a 12.7 '
                'mm. Dato tal como aparece.',
    '559x22.2': 'Revisar: etiqueta 22.2 (7/8 pulg) pero espesor de diseno 1.48, A 315.67 y b/t 34.85 corresponden a 15.9 '
                'mm. Dato tal como aparece.',
}
PAGINA_PDF_CUAD = {}
for _fam, _pag in [((51, 57, 64, 76, 89), 13), ((102, 114, 127, 140), 14),
                   ((152, 178, 203, 229, 254, 305, 356), 15), ((406, 457, 508, 559), 16)]:
    for _f in _fam:
        PAGINA_PDF_CUAD[_f] = _pag


def _filas(ruta):
    for linea in open(ruta, encoding='utf-8'):
        if linea.startswith('#') or not linea.strip():
            continue
        yield [x.strip() for x in linea.split('|')]


def _registro(nombre, designacion, seccion, H, B, t_dis, masa, A, Ix, Iy, Sx, Sy, rx, ry, J, Zx, Zy, alerta, pagina):
    return {'perfil_comercial': nombre, 'familia': 'OR', 'designacion_pulgadas': designacion, 'seccion': seccion,
            'd_ala_diametro_cm': H, 'bf_b_cm': B, 'tw_cm': t_dis, 'tf_t_cm': t_dis, 'area_cm2': A,
            'ix_cm4': Ix, 'iy_cm4': Iy, 'sx_cm3': Sx, 'sy_cm3': Sy, 'rx_cm': rx, 'ry_cm': ry, 'j_cm4': J,
            'cw_cm6': 0.0, 'zx_cm3': Zx, 'zy_cm3': Zy, 'ro_cm': None, 'masa_kg_m': masa, 'estado': ESTADO,
            'pagina_manual': None, 'pagina_pdf': pagina, 'pagina_catalogo_atc': None,
            'referencia_catalogo': REFERENCIA, 'campos_pendientes': [], 'fuente_completado': None,
            'fuente_propiedades': 'IMCA OR: espesor de diseno impreso (sin factor B4.2); peso = kg/m impreso.',
            'alerta_catalogo': alerta}


def _rectangulares():
    yy = {}
    for p in _filas(os.path.join(D, 'or_imca_rect_yy.txt')):
        d, b, t = p[0].split()
        Iy, Zy, Sy, ry = p[1].split()
        J, C = p[2].split()
        yy[(d, b, t)] = dict(Iy=float(Iy), Zy=float(Zy), Sy=float(Sy), ry=float(ry), J=float(J))
    recs = []
    for p in _filas(os.path.join(D, 'or_imca_rect_xx.txt')):
        d, b, t = p[0].split()
        tdis, kgm, lbft, A, bt, ht = p[2].split()
        Ix, Zx, Sx, rx = (float(v) for v in p[3].split())
        y = yy[(d, b, t)]
        clave = f'{d}x{b}'
        alerta = ALERTA_RECT.get(clave) if clave in ('305x51', '305x76') and t in ('4.8', '6.4', '7.9') else None
        if clave == '610x305' and t in ('12.7', '15.9', '19.1'):
            alerta = ALERTA_RECT['610x305']
        nombre = f'OR {d}x{b}x{t}x{kgm} (kgf/m)'
        recs.append(_registro(nombre, p[1], 'rectangular', int(d) / 10, int(b) / 10, float(tdis), float(kgm),
                              float(A), Ix, y['Iy'], Sx, y['Sy'], rx, y['ry'], y['J'], Zx, y['Zy'], alerta, None))
    return recs


def _cuadrados():
    recs = []
    for p in _filas(os.path.join(D, 'or_imca_cuadrado.txt')):
        lado, t = p[0].split()
        tdis, kgm, lbft, A, bt = p[2].split()
        I, Z, S, r = (float(v) for v in p[3].split())
        J, C = (float(v) for v in p[4].split())
        clave = f'{lado}x{t}'
        alerta = ALERTA_CUAD.get(clave)
        if lado == '127' and t == '3.2' and tdis == '0.18':
            alerta = ALERTA_CUAD['127x3.2:1']
        if lado == '559':
            alerta = ALERTA_CUAD[f'559x{t}']
        nombre = f'OR {lado}x{t}x{kgm} (kgf/m)'
        l_cm = int(lado) / 10
        recs.append(_registro(nombre, p[1], 'cuadrada', l_cm, l_cm, float(tdis), float(kgm), float(A), I, I, S, S,
                              r, r, J, Z, Z, alerta, PAGINA_PDF_CUAD[int(lado)]))
    return recs


def main():
    perfiles = _rectangulares() + _cuadrados()
    nombres = [p['perfil_comercial'] for p in perfiles]
    assert len(set(nombres)) == len(nombres), 'nombres OR repetidos'
    salida = {'fuente': 'IMCA Perfiles OR (PTE rectangular y cuadrado), transcripcion a mano del PDF',
              'sha256_pdf': PDF_SHA256, 'n_registros': len(perfiles),
              'n_con_alerta_catalogo': sum(1 for p in perfiles if p['alerta_catalogo']),
              'perfiles': perfiles}
    with open(os.path.join(D, 'perfiles_or_imca.json'), 'w', encoding='utf-8') as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)
    print(len(perfiles), 'registros OR;', salida['n_con_alerta_catalogo'], 'con alerta')


if __name__ == '__main__':
    main()
