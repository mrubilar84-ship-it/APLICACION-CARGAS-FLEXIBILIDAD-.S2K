# Mapa de codigo (revision 01)

Generado con AST desde codigo/modulos/.


## analisis_opensees.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 31 | clase | `ErrorAnalisis` |  |
| 35 | funcion | `_num` | Numero o None (vacio, NaN o texto no numerico). |
| 47 | funcion | `_marcado` | True si la celda REPORTAR dice SI. |
| 54 | funcion | `materiales_desde_filas` | {nombre: {'E', 'nu'}} desde las filas de MATERIALES (NOMBRE, TIPO, FY, FU, E, NU, FUENTE). |
| 63 | funcion | `estados_desde_df` | [(nombre, peso_propio)] en el orden de la hoja ESTADOS. PESO PROPIO debe ser SI o NO. |
| 77 | funcion | `propiedades_barras` | Propiedades de cada barra: seccion desde la base Gerdau y E, nu desde MATERIALES. Lanza ErrorAnalisis |
| 106 | funcion | `_verificar_conectividad` |  |
| 116 | funcion | `_modelo` | Construye el modelo OpenSees del caso: nodos, apoyos, barras (con rotulas), cargas nodales y peso propio. |
| 169 | funcion | `_resolver` | Un caso (estado): desplazamientos de nodos, fuerzas en extremos de barras y reacciones (cm, kgf). |
| 203 | funcion | `_combinar` | Superposicion lineal: partes = [(factor, resultado)]. |
| 216 | funcion | `_residuo` | Equilibrio global de fuerzas: suma de reacciones + cargas aplicadas + peso propio (debe ser ~0). |
| 231 | funcion | `_fuerzas_extremo` | Fuerzas de un extremo en unidades de salida: kgf y kgf·m. |
| 236 | funcion | `_tablas` |  |
| 270 | funcion | `tabla_maximos` | Maximo y minimo de cada esfuerzo entre los extremos I y J, por barra y caso (solo barras REPORTAR = SI). |
| 285 | funcion | `tabla_deformada` | Coordenadas de todos los nodos por caso: original, desplazamientos (mm, rad) y posicion deformada (m). |
| 299 | funcion | `_arco` | Arco de momento: positivo alrededor de a x b (regla de la mano derecha). |
| 308 | funcion | `figura_ejes_locales` | PNG: ejes locales de una barra de ejemplo (viga a lo largo de X con peralte vertical), fuerzas en los |
| 368 | funcion | `_lineas` |  |
| 376 | funcion | `figura_deformada` | Figura 3D interactiva: deformada por estado y combinacion (botones). Sin escala dada, la escala hace que el |
| 417 | funcion | `_escribir` |  |
| 438 | funcion | `clase_combinacion` | Clase de una combinacion segun el TIPO (hoja ESTADOS) de sus estados con factor no nulo: 'viento' si incluye W |
| 452 | funcion | `_deflexion_viga` | Desviacion vertical (Z global, cm) de la viga i a lo largo de su eje (xi = 0 a 1), respecto a la cuerda entre |
| 478 | funcion | `_curvatura_max` | Maximo |M| = EI * v'' a lo largo de una viga (Euler-Bernoulli exacto entre extremos, malla de 401 puntos). |
| 490 | funcion | `momentos_maximos_viga` | Momento maximo en el tramo (no solo en los extremos) de la barra i para una combinacion (corrige H-01). |
| 508 | funcion | `flechas_vigas` | Flecha vertical maxima de cada viga horizontal (desviacion respecto a la cuerda entre sus extremos) sobre las |
| 534 | funcion | `correr` | Resuelve todos los estados y combinaciones y escribe el Excel de resultados. |
| 594 | funcion | `correr_desde_planilla` | Punto de entrada del notebook: toma los datos de la planilla ya leida y valida (bloque 7). |

## dibujo_directo.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 25 | funcion | `restricciones_de` | (UX, UY, UZ, RX, RY, RZ) como 6 bools. Acepta 'empotrado', 'rotulado' o una lista de 6 valores. |
| 39 | funcion | `marca_apoyo` | 'empotrado' si restringe los 6 GDL; 'rotulado' si restringe alguna traslacion; 'giro' si solo giros. |
| 49 | funcion | `etiqueta_restricciones` |  |
| 56 | clase | `DibujoModelo` |  |
| 174 | funcion | `comparar_modelos` | Compara dos modelos (formato leer_dxf) sin depender del orden de nodos ni barras. |

## diseno_asd.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 48 | funcion | `_req` | Dato obligatorio de LONGITUDES (KX, KY, CB, LX, LY, LB): sin valor no se supone nada, se detiene el diseno. |
| 55 | funcion | `cargar_norma` | Carga los valores de norma desde la hoja NORMA ({CLAVE: valor}) y el Kz elegido en PARAMETROS. |
| 86 | clase | `ErrorAsd` |  |
| 90 | funcion | `_forma` |  |
| 94 | funcion | `_elementos_E7` | Elementos esbeltos en compresion de I y canales (B4.1a / E7). Devuelve Ae y detalle. |
| 127 | funcion | `pn_compresion` | Resistencia nominal a compresion de I y canales (E3, E4, E7). Devuelve (Pn, detalle). |
| 153 | funcion | `_ltb_I` | Pandeo lateral torsional (F2.2 y F2-4..F2-8) con Mp = Fy Zx. |
| 176 | funcion | `mn_fuerte` | Momento nominal eje mayor de I y canales (F2, F3). Devuelve (Mn, detalle). |
| 196 | funcion | `mn_debil` | Momento nominal eje menor de I y canales (F6). |
| 213 | funcion | `_cv` |  |
| 220 | funcion | `vn_fuerte` | Cortante en el alma eje mayor de I y canales (G2). |
| 232 | funcion | `vn_debil` | Cortante en el eje menor (G6): dos patines, Cv2 con kv = 1.2 (nota de usuario de G6). |
| 241 | funcion | `propiedades_angulo` | Propiedades de un angulo de lados iguales: b = pata (H = B), t = espesor. |
| 261 | funcion | `_fn_E3` |  |
| 267 | funcion | `_slend_angulo` | Esbeltez efectiva: z (menor, rz) por E5 o KL/rz, y u (mayor principal) por KL/ru. |
| 280 | funcion | `_resistencias_angulo` |  |
| 344 | funcion | `_utilizacion_angulo` | LI: H2-1 con el momento resultante sobre cada eje principal (cubre cualquier orientacion). |
| 365 | funcion | `resistencias_asd` | Capacidades ASD (admisibles) de la barra: Pa tension, Pa compresion, Ma eje mayor y menor, Va. |
| 399 | funcion | `utilizacion_asd` | Utilizaciones ASD (<= 1 cumple): tension, compresion, flexion eje mayor y menor, cortante, H1 o H2. |
| 428 | funcion | `esbeltez_local` | Esbeltez local por elemento segun NTC: lambda / lambda_r (<= 1 cumple). Compresion: Tabla 3.2.1; |
| 445 | funcion | `tipo_seccion_flexion` | Tipo de seccion (NTC 3.2.1.2, Tabla 3.2.2): 1, 2, 3 o 4 segun el elemento mas esbelto. |
| 464 | funcion | `clasificacion_compresion` | NTC 3.2.1.1 (Tabla 3.2.1): seccion no-esbelta si todos sus elementos cumplen lambda <= lambda_r. |
| 470 | funcion | `_num` |  |
| 482 | funcion | `_texto` |  |
| 488 | funcion | `e5_cumple` | E5(a): el angulo se trata con E5 solo si LONGITUDES marca SI en las cuatro condiciones de E5 (1 a 4). |
| 494 | funcion | `factor_u_angulo` | Factor de rezago U para tension (AISC D3, Tabla D3.1). Ambas patas conectadas: U = 1.0 (caso 1). |
| 502 | funcion | `_props_asd` | Propiedades para ASD desde la base Gerdau. No se estima ninguna propiedad: lo que falta queda NO REVISADO. |
| 527 | funcion | `_demanda_fila` | Demandas ASD de una fila de BARRAS (kgf, kgf·cm). |
| 562 | funcion | `_valores_designacion` | Numeros de la designacion comercial: 'IR 6 × 12' -> [6, 12]; 'LI 3 1/2 × 3/8' -> [3.5, 0.375]. |
| 582 | funcion | `clave_orden` | Orden de las listas: tipo (IR, CE, LI), luego la designacion comercial (peralte o ala, luego peso o espesor) |
| 591 | funcion | `seccion_de` | Seccion sin el tipo: 'IR 10 × 30' -> '10 × 30'. |
| 597 | funcion | `_ductilidad` | Tabla 12.1.2 (NTC): I y canales (DN); angulos sencillos: alas (no atiesadas), lambda = b/t <= 0.30 (alta) o |
| 610 | funcion | `_chequear` | Utilizaciones ASD por demanda (una fila por combinacion) y verificaciones de esbeltez de la barra. |
| 637 | funcion | `_resumen_fu` | FU por verificacion (maximo sobre combinaciones) y caso que gobierna. pares = [(fila, caso)]. |
| 665 | funcion | `_preparar_entradas` | Materiales por nombre, longitudes por ID de barra y combinaciones de servicio. |
| 677 | funcion | `_entrada_barra` | Datos de entrada ASD de la barra i: longitud, K, Cb, ductilidad y material. Lo no dado se supone y se anota. |
| 716 | funcion | `perfil_por_grupo` | Perfil de cada grupo. Cada grupo usa una sola seccion: si sus barras tienen perfiles distintos, ErrorAsd |
| 740 | funcion | `matriz_fu_por_perfil` | FU ASD de cada barra con cada perfil del catalogo (IR, CE, LI), con sus combinaciones, longitudes, K y el |
| 793 | funcion | `diseno_asd_desde_planilla` | Diseno ASD (AISC 360-22) de las barras IR, CE y LI con las combinaciones de servicio (COMBINACIONES). |
| 913 | funcion | `fu_grupo_por_perfil` | Por perfil: el FU maximo de las barras del grupo, cada una con su propia demanda. None si alguna barra del |
| 924 | funcion | `listas_desde_matriz` | Perfiles que cumplen por grupo: cada barra del grupo cumple con su propia demanda (FU <= 1 en resistencia, |
| 969 | funcion | `listas_por_grupo_asd` |  |

## diseno_ntc.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 34 | clase | `ErrorDiseno` |  |
| 39 | funcion | `n_compresion` | Tabla 5.2.1 (perfiles I laminados estandar, tp <= 51 mm): (n eje mayor, n eje menor) segun Fy (kgf/cm2). |
| 48 | funcion | `clasificar_i` | Clasificacion de la seccion I: patines (b = bf/2) y alma (h = d - 2 tf). Tablas 3.2.1 y 3.2.2. |
| 72 | funcion | `resistencia_traccion` | Rt = min(FR Fy A, FR Fu Ae) con Ae = A. Si no hay Fu, solo fluencia (se marca). |
| 81 | funcion | `resistencia_compresion` | Rc = FR chi Fy A con n por eje (tabla 5.2.1). Devuelve (Rc, detalle por eje). |
| 96 | funcion | `_Lu_Lr` | Longitudes Lu y Lr (6.3.5 a 6.3.8). Z = Zx (compacta) o Sx (no compacta, 6.4). |
| 106 | funcion | `_Me` | Momento elastico de pandeo lateral (6.3.4). |
| 111 | funcion | `mn_fuerte` | Mn alrededor del eje fuerte. Patin compacto: 6.3 (ref. Mp). Patin no compacto: 6.4 (ref. My, sin |
| 133 | funcion | `mn_debil` | Mn alrededor del eje debil (6.6). Patin compacto: min(Zy Fy, 1.6 Sy Fy). Patin no compacto: Sy Fy |
| 144 | funcion | `_cv` | Coeficiente Cv (7.2.3 a 7.2.5). |
| 155 | funcion | `vn_fuerte` | Cortante en el plano del alma (7.2.1): Aa = h tw. Vigas I laminadas (h/tw <= 2.24 sqrt(E/Fy)): Cv = 1, FR = 1. |
| 167 | funcion | `vn_debil` | Cortante normal al alma (7.7): Aa = bf tf, b/tp con b = bf/2, kv = 1.2, FR = 0.9. |
| 177 | funcion | `ductilidad_12_1_2` | Tabla 12.1.2: limites de ancho/grueso de elementos en compresion de miembros de ductilidad alta (lambda_da) |
| 207 | funcion | `clasificar_canal` | Canal: patin de ancho total B (tabla 3.2.2, canales) y alma h = d - 2 tf. |
| 230 | funcion | `resistencia_compresion_canal` | Canal (5.2.2.2): Fe = min(Fex, Fe acoplada), Fe acoplada = flexion alrededor del eje debil (no simetrico) con |
| 254 | funcion | `_props` |  |
| 263 | funcion | `_diseno_cuadrada` | Barra maciza cuadrada (CS): compresion 5.2.1(b) con n = 1.4; flexion 6.11 con d = t = lado; |
| 305 | funcion | `diseno_barra` | Capacidades de una barra (cm, kgf). IR (perfil I) y CE (canal). Otras familias: solo tension (ver notas). |
| 365 | funcion | `_mx` |  |
| 370 | funcion | `chequeos_caso` | Revisa un caso (fila de demandas) contra las capacidades de la barra. r: dict con N, V, M por extremo. |
| 445 | funcion | `_columnas_caso` |  |
| 453 | funcion | `_num` |  |
| 462 | funcion | `diseno_desde_planilla` |  |
| 571 | funcion | `_estado` | CUMPLE / NO CUMPLE segun la utilizacion maxima; REVISAR si alguna parte no se pudo revisar. |
| 584 | funcion | `_fila_capacidad` | Una fila de la hoja CAPACIDADES: capacidades y longitudes usadas de una barra. |
| 608 | funcion | `_evaluar_perfil_grupo` | True si el perfil cumple todas las revisiones de la NTC para la envolvente del grupo (resistencia a tension |
| 644 | funcion | `listas_por_grupo` |  |
| 719 | funcion | `_escribir` |  |

## memoria_asd.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 37 | funcion | `_v` | Numero con separador de miles y punto decimal; guion si no hay dato. |
| 54 | funcion | `_fu` |  |
| 61 | funcion | `_evaluar` | Evalua la barra i con el motor del bloque 10 y devuelve todo lo necesario para la memoria. |
| 122 | funcion | `_props_tabla` |  |
| 145 | funcion | `_verificaciones` | Filas de la tabla de verificaciones: (verificacion, ecuacion, calculo sustituido, capacidad, demanda, FU). |
| 227 | funcion | `_estado_txt` |  |
| 233 | funcion | `_tabla_verif` |  |
| 288 | funcion | `_interaccion` | FU de interaccion flexocompresion (H1-1 o H2-1), el maximo sobre combinaciones. Sin carga axial, H1 se reduce |
| 303 | funcion | `_fila_grupo` | Una fila de la tabla por grupo: FU de interaccion, esbeltez local y global (calculado y limite) y estado. |
| 331 | funcion | `resultados_grupo` | Tabla por grupo con un perfil elegido para todas sus barras (no cambia el modelo). |
| 341 | funcion | `opciones_grupo` | Opciones del desplegable de un grupo: todas las secciones IR, CE y LI ordenadas por tipo y seccion, con el |
| 359 | funcion | `_maximo_fila` | FU maximo de una combinacion (todas las verificaciones de demanda). |
| 365 | funcion | `_inter_fila` | FU de interaccion flexocompresion de una combinacion (H1 o H2; sin axial, suma de los FU de flexion). |
| 373 | funcion | `_tabla_combinaciones` | Demandas y FU de cada combinacion de servicio de la barra. Resalta la combinacion que controla. |
| 392 | funcion | `_bloque_barra` | Detalle de una barra: datos, propiedades, combinaciones y verificaciones con ecuaciones y referencias. |
| 428 | funcion | `fu_max` | FU maximo de la barra (todas las verificaciones). |
| 433 | funcion | `_desplazamientos` | Desplazamiento maximo de los nodos por combinacion (mm). casos: [(nombre, tipo, res)], res['nodos'] en cm. |
| 450 | funcion | `_png_deformada` | Imagen de la deformada (3D) de un caso: original en gris, deformada en azul. Devuelve (base64, escala). |
| 510 | funcion | `_ref_html` | Linea de referencia (apartado y pagina) bajo el nombre de una verificacion. |
| 515 | funcion | `_refs_verif` | Referencias de AISC para cada verificacion de la tabla (I y canal, o angulo LI). |
| 530 | funcion | `_ref_local` | Referencia NTC de la esbeltez local: Tabla 3.2.1 en compresion, Tabla 3.2.2 en flexion. |
| 535 | funcion | `_nota_normativa` | Nota de la memoria: el diseno es AISC 360-22 ASD y las esbelteces se verifican con la NTC-Acero CDMX. |
| 580 | funcion | `_distorsiones` | Distorsion horizontal de entrepiso (NTC-CA 4.1.1 b): desplazamiento horizontal relativo entre los extremos de cada |
| 607 | funcion | `_cumple_html` |  |
| 611 | funcion | `_distorsion_texto` |  |
| 615 | funcion | `_columnas` | Columnas (barras casi verticales): [(id, nodo_inferior, nodo_superior, h_cm)]. |
| 628 | funcion | `_rel` | Desplazamiento horizontal relativo (cm, vector XY) entre los nodos superior e inferior de una columna. |
| 633 | funcion | `_dcol` | Desplazamiento de entrepiso / h de una columna: gravedad dG mas +-fac*dE (la accion sismica es reversible). |
| 638 | funcion | `_periodo` | Periodo fundamental aproximado, NTC 6.4.1: T = 2*pi*sqrt(sum(W X^2) / (g*sum(F X))), sumando todos los niveles. |
| 671 | funcion | `_seccion_sismo` | 6.3 Distorsion por sismo, metodo estatico (NTC Diseno por Sismo 2023). Todos los valores vienen de la |
| 779 | funcion | `_seccion_desplazamientos` | Seccion 6: desplazamientos por combinacion y deformada de la que controla (6.1); distorsion de entrepiso con |
| 869 | funcion | `_encabezado_doc` |  |
| 887 | funcion | `_criterios_html` |  |
| 912 | funcion | `_parametros_html` | 3.1 Parametros de diseno y de norma usados por el calculo, con su referencia (hojas PARAMETROS y NORMA). |
| 950 | funcion | `_datos_entrada_html` |  |
| 1000 | funcion | `_modelo_html` |  |
| 1015 | funcion | `_pendientes_html` |  |
| 1048 | funcion | `_simbologia_html` |  |
| 1065 | funcion | `memoria_html` | Escribe la memoria de calculo completa (HTML imprimible) del diseno de todas las barras del modelo. |

## orientacion_gerdau.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 17 | funcion | `vector_vecxz` | vecxz por defecto segun el tipo de elemento (igual que el motor). |
| 32 | funcion | `vecxz_desde_direccion` | vecxz que hace que el eje local y (= peralte) apunte segun s (proyectado perpendicular a la barra). |
| 45 | funcion | `vecxz_de_barra` | vecxz de una barra: usa 'eje_fuerte' si existe, si no el default por tipo de elemento. |
| 56 | funcion | `ejes_locales` | Ejes locales (x, y, z) de la barra i. |
| 67 | funcion | `dimensiones` | (d, bf) en metros desde Gerdau (H = d, B = bf en cm). None si el perfil no existe o no tiene dato. |
| 75 | funcion | `contorno` | 4 vertices globales del rectangulo del perfil en el punto medio de la barra i. |
| 95 | funcion | `orientar` | Fija el peralte (eje fuerte) de la barra i con un preset o un vector. Rechaza direccion paralela a la barra. |
| 107 | funcion | `ortogonalidad` | Angulo (grados) entre el eje fuerte asignado y la barra; 90 = perpendicular (correcto). |

## parametros.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 14 | funcion | `_vacio` |  |
| 18 | funcion | `_numero` |  |
| 26 | funcion | `_si_no` |  |
| 31 | funcion | `resolver` | par: {CLAVE: valor} de la hoja PARAMETROS. nor: {'SISTEMAS': {nombre: {Q, gSV, gOI, R0}}, 'VALORES': {CLAVE: n}}. |
| 112 | funcion | `k2_de_T` | k2 = 0.5 (1 - (T/Ta)^2) si T < Ta; 0 si T >= Ta (NTC 3.3.1b). |

## perfiles_gerdau.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 11 | funcion | `obtener_perfil` | Dimensiones en cm: H = d (peralte o diametro), B = bf, e = tw, t = tf. None = dato pendiente. |
| 23 | funcion | `_clave_seccion` | Familia, luego peralte (o diametro/lado), masa (mas liviano primero), ancho. Nulos al final. |
| 32 | funcion | `lista_perfiles_ordenada` | [(etiqueta, nombre)] para la lista desplegable. Muestra masa y estado si no es Revisado. |

## vista3d_plotly.py

| linea | tipo | nombre | proposito |
|---|---|---|---|
| 19 | funcion | `_flecha` | Flecha 3D: linea con etiqueta y cono en la punta. |
| 32 | funcion | `figura_3d` | Devuelve una go.Figure 3D del modelo. escala_seccion solo amplia la seccion dibujada, no el calculo. |
