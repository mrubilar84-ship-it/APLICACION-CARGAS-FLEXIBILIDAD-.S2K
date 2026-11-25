"""Actualiza la hoja LISTAS de plantilla_soportes.xlsx (raiz del repositorio) a la base de perfiles vigente
(Gerdau rev04, HSS del catalogo ATC y OR del catalogo IMCA), sin tocar las demas hojas: se edita el XML de LISTAS y
los nombres definidos LISTA_<GRUPO>. Cada lista trae los perfiles en el orden de lista_perfiles_ordenada() y, al
final, 30 filas de formula para las secciones GEN (hoja SECCIONES, desde la fila SECC_FIL_INI).

Uso:  python3 actualizar_listas_plantilla.py ../plantilla_soportes.xlsx     (reescribe el archivo)
Por que no openpyxl: al guardar con openpyxl se pierden los valores calculados de las formulas de las demas hojas
(ver el aviso de formulas sin valor en el notebook).
"""
import importlib
import os
import re
import shutil
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

D = os.path.dirname(os.path.abspath(__file__))
SECC_FIL_INI = 5          # fila de la primera seccion GEN en la hoja SECCIONES (celda6_plantilla.py)
SECC_MAX = 30
GRUPOS = ['COLUMNA', 'VIGA', 'ARRIOSTRE', 'DIAGONAL']
COLUMNAS = ['F', 'G', 'H', 'I']


def _base_perfiles():
    """Modulo perfiles_gerdau (la base fusionada) con la misma logica que el notebook."""
    sys.path.insert(0, D)
    import generar_plantilla
    carpeta = tempfile.mkdtemp(prefix='base_listas_')
    generar_plantilla.base_en(carpeta)
    sys.path.insert(0, carpeta)
    for m in ('perfiles_gerdau', 'gerdau_datos'):
        sys.modules.pop(m, None)
    return importlib.import_module('perfiles_gerdau'), carpeta


def _celda_texto(ref, texto):
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(texto)}</t></is></c>'


def _celda_formula(ref, k):
    f = f'IF(SECCIONES!$A${SECC_FIL_INI + k}="","",SECCIONES!$A${SECC_FIL_INI + k})'
    return f'<c r="{ref}" t="str"><f>{escape(f)}</f><v/></c>'


def _hoja_xml(xml, G):
    """Reescribe sheetData y dimension de la hoja LISTAS. Conserva la fila 1 (encabezados) y las celdas D (ELEMENTO)."""
    orden = [nombre for _, nombre in G.lista_perfiles_ordenada()]
    n = len(orden)
    # celdas D (ELEMENTO) existentes, por fila
    elementos = {}
    for m in re.finditer(r'<c r="D(\d+)"[^>]*?(?:/>|>.*?</c>)', xml, re.S):
        elementos[int(m.group(1))] = m.group(0)
    fila1 = re.search(r'<row r="1".*?</row>', xml, re.S).group(0)
    filas = [fila1]
    for i, nombre in enumerate(orden):
        r = i + 2
        p = G.PERFILES[nombre]
        celdas = [_celda_texto(f'A{r}', nombre), _celda_texto(f'B{r}', p['estado'])]
        if p['masa_kg_m'] is not None:
            celdas.append(f'<c r="C{r}"><v>{p["masa_kg_m"]!r}</v></c>')
        if r in elementos:
            celdas.append(elementos[r])
        celdas += [_celda_texto(f'{c}{r}', nombre) for c in COLUMNAS]
        filas.append(f'<row r="{r}">' + ''.join(celdas) + '</row>')
    for k in range(SECC_MAX):
        r = n + 2 + k
        filas.append(f'<row r="{r}">' + ''.join(_celda_formula(f'{c}{r}', k) for c in COLUMNAS) + '</row>')
    ultima = n + 1 + SECC_MAX
    nuevo = '<sheetData>' + ''.join(filas) + '</sheetData>'
    xml = re.sub(r'<sheetData>.*</sheetData>', lambda _: nuevo, xml, count=1, flags=re.S)
    xml = re.sub(r'<dimension ref="[^"]*"/>', f'<dimension ref="A1:I{ultima}"/>', xml, count=1)
    return xml, ultima


def _nombres(xml_wb, ultima):
    for g, c in zip(GRUPOS, COLUMNAS):
        xml_wb, k = re.subn(rf'(<definedName name="LISTA_{g}">)LISTAS!\$[A-Z]+\$2:\$[A-Z]+\$\d+(</definedName>)',
                            rf'\g<1>LISTAS!${c}$2:${c}${ultima}\g<2>', xml_wb)
        assert k == 1, (g, k)
    return xml_wb


def actualizar(ruta):
    G, carpeta = _base_perfiles()
    tmp = ruta + '.tmp'
    with zipfile.ZipFile(ruta) as origen:
        wb = origen.read('xl/workbook.xml').decode('utf-8')
        rels = origen.read('xl/_rels/workbook.xml.rels').decode('utf-8')
        rid = re.search(r'<sheet name="LISTAS"[^>]*r:id="(rId\d+)"', wb).group(1)
        destino_hoja = re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"', rels) or \
            re.search(rf'Target="([^"]+)"[^>]*Id="{rid}"', rels)
        ruta_hoja = 'xl/' + destino_hoja.group(1)
        xml_hoja, ultima = _hoja_xml(origen.read(ruta_hoja).decode('utf-8'), G)
        wb_nuevo = _nombres(wb, ultima)
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as nuevo:
            for item in origen.infolist():
                if item.filename == ruta_hoja:
                    datos = xml_hoja.encode('utf-8')
                elif item.filename == 'xl/workbook.xml':
                    datos = wb_nuevo.encode('utf-8')
                else:
                    datos = origen.read(item.filename)
                nuevo.writestr(item, datos)
    shutil.move(tmp, ruta)
    shutil.rmtree(carpeta, ignore_errors=True)
    print(f'LISTAS: {len(G.lista_perfiles_ordenada())} perfiles + {SECC_MAX} filas GEN; rango 2..{ultima}')


if __name__ == '__main__':
    actualizar(sys.argv[1])
