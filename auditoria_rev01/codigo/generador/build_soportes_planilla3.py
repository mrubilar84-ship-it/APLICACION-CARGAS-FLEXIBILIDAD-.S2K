"""Notebook de soportes por planilla v3: eje fuerte como vector libre, vista en vivo en el Excel (formulas y
graficos vinculados a las celdas), y regeneracion del Excel con la figura 3D (secciones y ejes fuertes).
Uso: build_soportes_planilla3.py SALIDA.ipynb [PLANTILLA.xlsx]   (la plantilla, si se da, se incrusta)"""
import base64, json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
SALIDA = sys.argv[1]
PLANTILLA = sys.argv[2] if len(sys.argv) > 2 else None
FUENTE_GERDAU = '<ruta_local_de_carga>'
CAMPOS = ['familia', 'perfil_comercial', 'estado', 'masa_kg_m', 'd_ala_diametro_cm', 'bf_b_cm', 'tw_cm',
          'tf_t_cm', 'area_cm2', 'ix_cm4', 'iy_cm4', 'sx_cm3', 'sy_cm3', 'rx_cm', 'ry_cm', 'j_cm4', 'cw_cm6',
          'zx_cm3', 'zy_cm3', 'ro_cm']


def leer(nombre):
    with open(os.path.join(D, nombre), encoding='utf-8') as f:
        return f.read()


def md(texto):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': texto.splitlines(keepends=True)}


def code(texto):
    # Celda de codigo colapsable: el codigo queda oculto (se despliega con el boton de la celda); las salidas se ven.
    return {'cell_type': 'code', 'metadata': {'jupyter': {'source_hidden': True}}, 'execution_count': None, 'outputs': [],
            'source': texto.splitlines(keepends=True)}


# Campos que la base rev04 deja vacios y que el manual Gerdau trae en sus tablas (CE: pagina 26; IR: pagina 27).
# Clave = nombre sin el superindice ᴬ ni espacios. Solo se completan campos vacios (se verifica).
CORRECCIONES_MANUAL = {
    'IR10×12': {'j_cm4': 2.5},
    'IR10×15': {'ix_cm4': 2686.0, 'sx_cm3': 226.0, 'rx_cm': 10.0},
    'CE3×3.5': {'j_cm4': 0.72, 'cw_cm6': 384.61, 'ro_cm': 4.00},
    'CE3×4.1': {'j_cm4': 0.98, 'cw_cm6': 478.86, 'ro_cm': 3.90},
    'CE4×4.5': {'area_cm2': 8.90, 'iy_cm4': 12.00, 'sy_cm3': 4.00, 'ry_cm': 1.20, 'j_cm4': 1.30, 'cw_cm6': 1167.10,
                'zy_cm3': 9.00, 'ro_cm': 5.10},
    'CE4×5.40': {'j_cm4': 1.44, 'cw_cm6': 1520.51, 'ro_cm': 4.80},
    'CE6×8.20': {'j_cm4': 2.77, 'cw_cm6': 8414.88, 'ro_cm': 6.70},
    'CE6×10.50': {'j_cm4': 4.69, 'cw_cm6': 12672.17, 'ro_cm': 6.30},
    'CE6×13.00': {'j_cm4': 8.92, 'cw_cm6': 17790.92, 'ro_cm': 6.00},
}


def completar_desde_manual(perfiles):
    n = 0
    for p in perfiles:
        extra = CORRECCIONES_MANUAL.get(p['perfil_comercial'].replace('ᴬ', '').replace(' ', ''))
        for campo, valor in (extra or {}).items():
            assert p.get(campo) is None, (p['perfil_comercial'], campo, p.get(campo))
            p[campo] = valor
            n += 1
    print('valores completados desde el manual Gerdau:', n)


def datos_texto():
    with open(FUENTE_GERDAU, encoding='utf-8') as f:
        perfiles = json.load(f)['perfiles']
    completar_desde_manual(perfiles)
    compacto = [{k: p.get(k) for k in CAMPOS} for p in perfiles]
    return json.dumps(json.dumps(compacto, ensure_ascii=False, separators=(',', ':')))


PORTADA = """# Soportes: modelo por planilla Excel

Notebook nuevo (no modifica el ejemplo `agente_estructural.ipynb`). El modelo se define en una planilla, como en RAM Element: no hay que dibujar.

## Flujo

1. **Bloque 6**: carga la plantilla `plantilla_soportes.xlsx` (incrustada) y muestra sus hojas. Descárguela desde la pestaña Output.
2. Llénela en Excel:
   - **NODOS**: ID, X, Y, Z (m) y UX, UY, UZ, RX, RY, RZ (`SI` = grado restringido; vacío o NO = libre). Empotrado = los 6 en SI; rotulado = UX, UY, UZ.
   - **BARRAS**: ID, NODO_I, NODO_J, ELEMENTO, PERFIL (lista Gerdau), EJE_FUERTE_X/Y/Z (vector libre del peralte; vacío = por defecto), CONEXION_I y CONEXION_J (`empotrado` o `rotulado` en cada extremo) y DUCTILIDAD (ALTA o MEDIA, lista; vacío = no verifica la Tabla 12.1.2).
   - **VISTA_VIVA**: planta y alzado que cambian al editar NODOS o BARRAS. Puede elegir el nivel Z (C3) y la cota Y (C4).
   - **LONGITUDES**: por barra, LX y LY (m) longitud no arriostrada en X e Y, KX y KY (factor K), LB (m) para pandeo lateral y CB. Vacío = supuesto, y queda marcado en el diseño.
   - **Ángulos (LI)**: en LONGITUDES, marque SI en las cuatro columnas E5 solo si la barra las cumple; si no, el diseño usa K·L/rz y H2. LI CONEXION (UNA PATA o DOS PATAS) y LI LONGITUD CONEXION (m) fijan el factor U de tracción.
   - **CONEXIONES**, **LISTAS**, **CALCULO**: no editar (CALCULO sostiene los gráficos).
3. Súbala a Kaggle con **Add data**. El **bloque 7** la lee y valida.
4. **Bloque 8**: dibuja planta, alzado y 3D (secciones y ejes fuertes) en el notebook y regenera la planilla como `planilla_con_vista.xlsx`, con las vistas en vivo de VISTA_VIVA. Vuelva a ejecutar este bloque después de cambiar la planilla.
5. **Bloque 9**: análisis con OpenSees. Usa E y NU de MATERIALES, la sección de la base Gerdau, los apoyos y rótulas, las cargas por estado, el peso propio (ESTADOS: PESO PROPIO = SI) y las combinaciones de COMBINACIONES. Escribe `resultados_soportes.xlsx` con las barras, nodos y reacciones marcados REPORTAR = SI.
6. **Bloque 10**: diseño por AISC 360-22 (ASD) de IR, CE y LI, con las combinaciones de servicio del bloque 9 (sin las que incluyen viento: para el diseño solo aplica el sismo) y las longitudes de LONGITUDES. Las barras CS (macizas) y LM quedan fuera del diseño. Escribe `diseno_asd.xlsx` (CAPACIDADES, RESULTADOS, DETALLE, LISTAS_GRUPO) y `planilla_con_diseno.xlsx`, con las listas desplegables de perfiles que cumplen por grupo.

**Cambio de perfil por grupo (Excel):** en `planilla_con_diseno.xlsx`, la hoja **PERFIL_GRUPO** tiene un desplegable por grupo. Al elegir un perfil, se aplica a todas las barras de ese grupo (todas las columnas, todas las vigas...) y el FU y la esbeltez local y global se recalculan en la hoja **FU_BARRAS** sin volver a ejecutar nada. La hoja **FU_MATRIZ** guarda el FU de cada barra con cada perfil del catalogo. Si cambia ELEMENTO, longitudes o cargas, vuelva a ejecutar el bloque 10. Suba la planilla a Kaggle y ejecute el bloque 7: toma el perfil elegido por grupo. **Cada grupo tiene una sola sección:** si BARRAS trae perfiles distintos dentro de un grupo, el bloque 10 se detiene y lista cuáles son.

**Lo que se actualiza solo en Excel:** la vista en planta y alzado (hoja VISTA_VIVA).
**Lo que requiere ejecutar el bloque 8:** la vista 3D con secciones y ejes fuertes (Excel no dibuja en 3D por sí solo).

**Reglas:** coordenadas en metros; un nodo no puede repetir coordenadas; una barra no puede unir un nodo consigo mismo; el eje fuerte, si se da, no puede ser paralelo a la barra. Basta una componente: las vacias valen 0.

## Índice de bloques

1. Motor de dibujo (dibujo_directo.py)
2. Datos Gerdau rev04 (gerdau_datos.py)
3. Base de perfiles y lista ordenada (perfiles_gerdau.py)
4. Orientación y secciones (orientacion_gerdau.py)
5. Uso (sin código)
6. Cargar plantilla Excel
7. Leer, validar y armar el modelo
8. Dibujo de revisión y planilla regenerada
9. Análisis con OpenSees y Excel de resultados (analisis_opensees.py, celda9_analisis.py)
"""

BLOQUE_6 = leer('celda6_plantilla.py')
BLOQUE_7 = leer('celda7_validar.py')
BLOQUE_8 = leer('celda8_dibujo.py')
BLOQUE_9 = leer('celda9_analisis.py')
BLOQUE_9B = leer('celda9b_deformada.py')
BLOQUE_10 = leer('celda10_diseno.py')
BLOQUE_11 = leer('celda11_memoria.py')


def construir():
    if PLANTILLA and os.path.exists(PLANTILLA):
        with open(PLANTILLA, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
    else:
        b64 = ''
    celdas = [md(PORTADA)]
    celdas.append(md('## Bloque 1. Motor de dibujo (dibujo_directo.py)'))
    celdas.append(code('%%writefile dibujo_directo.py\n' + leer('dibujo_directo.py')))
    celdas.append(md('## Bloque 2. Datos Gerdau rev04 (gerdau_datos.py)\n\nLos 247 perfiles en un solo texto. No hay que editar este bloque.'))
    celdas.append(code('%%writefile gerdau_datos.py\n_DATOS_TEXTO = ' + datos_texto() + '\n'))
    celdas.append(md('## Bloque 3. Base de perfiles y lista ordenada (perfiles_gerdau.py)'))
    celdas.append(code('%%writefile perfiles_gerdau.py\n' + leer('perfiles_gerdau_nb.py')))
    celdas.append(md('## Bloque 4. Orientación y secciones (orientacion_gerdau.py)'))
    celdas.append(code('%%writefile orientacion_gerdau.py\n' + leer('orientacion_gerdau.py')))
    celdas.append(code('%%writefile vista3d_plotly.py\n' + leer('vista3d_plotly.py')))
    celdas.append(md('## Bloque 5. Uso\n\nEjecutar los bloques 1 a 4 una sola vez. Luego trabajar con los bloques 6 a 8.'))
    celdas.append(md('## Bloque 6. Cargar plantilla Excel\n\nCarga `plantilla_soportes.xlsx` y muestra sus hojas. Llénela en Excel y súbala a Kaggle con Add data.'))
    celdas.append(code(BLOQUE_6.replace('__PLANTILLA_B64__', b64)))
    celdas.append(code('%%writefile parametros.py\n' + leer('parametros.py')))
    celdas.append(md('## Bloque 7. Leer, validar y armar el modelo\n\nLee la planilla subida a Kaggle o, si no hay ninguna, la de ejemplo. Si hay ERROR, no se arma el modelo.'))
    celdas.append(code(BLOQUE_7))
    celdas.append(md('## Bloque 8. Dibujo de revisión y planilla regenerada\n\nFigura planta, alzado y 3D, y `planilla_con_vista.xlsx`. Ejecutar después de cada cambio.'))
    celdas.append(code(BLOQUE_8))
    celdas.append(md('## Bloque 9. Análisis con OpenSees y Excel de resultados\n\nLos datos vienen de la planilla: E y NU (MATERIALES), sección (base Gerdau), apoyos y rótulas, cargas, peso propio (ESTADOS) y combinaciones (COMBINACIONES). Solo sale lo marcado REPORTAR = SI. Escribe `resultados_soportes.xlsx`.'))
    celdas.append(code('%%writefile analisis_opensees.py\n' + leer('analisis_opensees.py')))
    celdas.append(code(BLOQUE_9))
    celdas.append(md('## Bloque 9b. Deformada con escala editable\n\nCambie `ESCALA_DEFORMADA` y ejecute solo esta celda: no vuelve a resolver el análisis.'))
    celdas.append(code(BLOQUE_9B))
    celdas.append(md('## Bloque 10. Diseño por AISC 360-22 (ASD)\n\nCapacidades de IR, CE y LI (tensión, compresión, flexión, cortante, interacción H1 o H2) con las combinaciones de servicio del bloque 9 (sin las que incluyen viento: para el diseño solo aplica el sismo) y las longitudes de la hoja LONGITUDES. Escribe `diseno_asd.xlsx` y `planilla_con_diseno.xlsx`. Las barras CS quedan fuera del diseño. Los resultados salen **por grupo**: elija la sección de cada grupo en su desplegable (ordenado por tipo y sección); la tabla se recalcula y el botón **Aplicar** actualiza el Excel por elemento y la planilla (hoja PERFIL_GRUPO).'))
    celdas.append(code('%%writefile diseno_ntc.py\n' + leer('diseno_ntc.py')))
    celdas.append(code('%%writefile diseno_asd.py\n' + leer('diseno_asd.py')))
    celdas.append(code('%%writefile memoria_asd.py\n' + leer('memoria_asd.py')))
    celdas.append(code(BLOQUE_10))
    celdas.append(md('## Bloque 11. Memoria de cálculo (HTML)\n\nGenera `memoria_calculo.html` con los datos, las propiedades y cada verificación de cada barra, con su ecuación, los valores sustituidos y el FU. Incluye la nota normativa: diseño AISC 360-22 (ASD) y esbelteces local y global con la NTC-Acero CDMX 2020. Para PDF: abra el archivo y use Imprimir > Guardar como PDF. Edite PROYECTO dentro del bloque.'))
    celdas.append(code(BLOQUE_11))
    nb = {'cells': celdas,
          'metadata': {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
                       'language_info': {'name': 'python'}},
          'nbformat': 4, 'nbformat_minor': 5}
    with open(SALIDA, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print('escrito', SALIDA, len(celdas), 'celdas', os.path.getsize(SALIDA), 'bytes | plantilla incrustada:', bool(b64))


construir()
