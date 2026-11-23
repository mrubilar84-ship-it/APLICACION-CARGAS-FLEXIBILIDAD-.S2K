# HSS (tubulares rectangulares y cuadradas, catálogo ATC): cambios del diseño

Fecha: 16 de noviembre de 2026. Alcance: base de perfiles, diseño ASD (AISC 360-22 y NTC-Acero CDMX), memoria,
hojas MATERIALES y NORMA de la planilla, y generación de la plantilla.

## 1. Datos (`datos/hss_atc_catalogo.json`)

- Fuente: catálogo de productos ATC, páginas impresas 08 a 10 (PDF 12 a 15). SHA-256 del PDF:
  `f4bb737b77157d326b476d02b9b1b179bfc2a312d85e8c714ca3c7dbc5c2da82`.
- Extracción reproducible: `datos/extraer_hss_atc.py <catalogo.pdf>`. Lee la capa de texto del PDF; no hay
  transcripción manual.
- 116 secciones: 39 cuadradas (9 tamaños, 4" a 16") y 77 rectangulares (20 tamaños, 7"x5" a 20"x12").
  Espesores de 3/16" a 1/2". Nombres en la base: `HSS h × b × espesor` (por ejemplo `HSS 8 × 8 × 1/2`).
- Valores de I, S, r, área y peso: tal como vienen en el catálogo, en cm.
- J (torsión): fórmula de pared delgada de sección cerrada, J = 2 t (b − t)² (h − t)² / (b + h − 2t).
- Zx y Zy: b h²/4 − (b − 2t)(h − 2t)²/4 (y análogo), sin radios de esquina.
- Cw = 0 (sección cerrada).
- Peso y área: coinciden en todas las filas (diferencia máxima 0,6 %).
- 7 filas con valores que no concuerdan entre sí (S, r o I frente a la geometría). Se conservan tal como vienen
  y se marcan en `alerta_catalogo`. No se corrigen ni se excluyen (decisión del usuario).

## 2. Diseño (`diseno_asd.py`)

Forma `HSS`: anchos planos sin radio de esquina, bp = B − 3t y hp = H − 3t (AISC, B4.1).

| Verificación | Referencia | Implementación |
|---|---|---|
| Tracción | D2 | Igual que el resto (Ae = Ag). |
| Compresión | E3-4, E3-2/E3-3; E7.1 | Fe por eje (sin pandeo torsional en sección cerrada). Ae = Ag − Σ(b − be)·t en las cuatro paredes. |
| Paredes esbeltas (E7) | E7-2, E7-3, E7-5; Tabla E7.1 caso (b) | be = b si λ ≤ λr·√(Fy/Fn); si no, be = b(1 − c1·r)·r ≤ b con r = √(Fel/Fn), Fel = (c2·λr/λ)²·Fy; c1 = 0.20, c2 = 1.38, λr = 1.40√(E/Fy). |
| Flexión eje fuerte | F7-1, F7-2, F7-3 (F7-4), F7-6, F7-8, F7-9, F7-10, F7-11 | Mp = Fy·Zx. Patín: compacto, no compacto (F7-2) o esbelto (F7-3 con Se). Alma: no compacta (F7-6); alma esbelta se rechaza (AISC: no hay HSS con almas esbeltas). LTB con Lp y Lr. |
| Flexión eje débil | F7-1, F7-2/F7-3, F7-6 | Igual, con las paredes verticales como patines. Sin LTB (nota de usuario de F7). |
| Cortante | G4-1 con Aw = 2·h·t; Cv2 de G2.2 (G2-9 a G2-11) con kv = 5 | h = peralte plano (eje fuerte) o ancho plano (eje débil). Ωv = 1.67. Corregido: la versión anterior usaba G2.1 con kv = 5.34 y Cv1; en el catálogo el resultado numérico es el mismo porque h/t ≤ 61 < 61.76. |
| Torsión | H3.1 (H3-1, H3-3, H3-4, H3-5); ΩT = 1.67 | Tn = Fcr·C, C = 2(B−t)(H−t)t − 4.5(4−π)t³ (nota de usuario de H3.1). Fcr según h/t, con h = lado plano mayor. Demanda Tr = máximo de |T| en los extremos de la barra (BARRAS, kgf·m → kgf·cm). Utilización Tr/Tc. |
| Interacción | H1-1a/b; H3-6 (H3.2) | Si Tr ≤ 0.2·Tc: H1 (la torsión se descarta, H3.2). Si Tr > 0.2·Tc: H3-6 = Pr/Pc + Mrx/Mcx + Mry/Mcy + (Vr/Vc + Tr/Tc)² ≤ 1, con Vr/Vc el mayor de x o y. |
| Esbeltez local NTC | Tabla 3.2.1 (compresión), Tabla 3.2.2 (flexión) | Paredes: λr = 1.40 (compresión); patines 1.12/1.12/1.40; almas 2.42/5.70. |
| Ductilidad NTC | Tabla 12.1.2, paredes de HSS rectangulares | λda = 0.55√(E/Fy) (alta), λdm = 0.64√(E/Fy) (media); se verifica la pared más esbelta. |

Valores normativos: hoja NORMA de la plantilla, con su cláusula y página (filas `AISC_HSS_*` y `NTC_HSS_*`).

### 2.1 Corrección de E7-2 (afecta también a IR, CE y LI)

La versión anterior usaba λ ≤ λr (sin el factor √(Fy/Fn)) y consideraba la pared sin reducción cuando
Fel ≥ Fn. El texto de AISC 360-22 (E7-2) indica be = b cuando λ ≤ λr·√(Fy/Fn). Entre ambos umbrales, la versión
anterior no reducía el ancho y AISC sí, por lo que era no conservadora. Se corrigió en `_elementos_E7` (IR, CE, LI)
y en `_elementos_E7_hss`. En el ejemplo gravitacional y en el caso sísmico de prueba ningún número de IR, CE ni
LI cambia (ver sección 4).

## 3. Memoria, planilla y base

- Memoria: propiedades de HSS (incluidos Zx, Zy y J de fórmula), ecuaciones de E3/E7, F7 en ambos ejes, G2 con
  Aw = 2ht, referencias de cláusula y página, y página del catálogo ATC.
- MATERIALES: fila `A500 Gr C` con Fy = 3234 kgf/cm² y Fu = 4359 kgf/cm² (46 y 62 ksi). Es un dato de entrada
  que se puede cambiar en el Excel. Pendiente: confirmar grado y valores con el proveedor del tubo.
- BARRAS: `MATERIAL = A500 Gr C` en cada barra de HSS. Cada grupo debe tener una sola sección (regla existente).
- Plantilla: `generar_plantilla.py` regenera `plantilla_soportes.xlsx` desde las fuentes (base, LISTAS, NORMA).

## 4. Verificación

- Ejemplo gravitacional y caso sísmico de prueba, con la base y la plantilla nuevas: ningún número cambia en
  IR, CE ni LI en las hojas de diseño y de resultados. Solo cambian el texto de alcance de RESUMEN y la lista de
  opciones por grupo (ahora incluye HSS).
- Planilla de prueba con HSS 8 × 8 × 1/2 en columnas y HSS 10 × 6 × 3/8 en vigas: el notebook corre completo
  (diseño, memoria y Excel). La viga no cumple la ductilidad media de la Tabla 12.1.2 (U = 1.47): sus paredes
  tienen b/t = 23.6, y el límite es 16.1.
- Comprobación independiente (cálculo separado con el texto de AISC 360-22, mismos supuestos K = 1, KL = Lb = 350 cm,
  Cb = 1.0) en tres secciones: Pn/Ωc, Mn/Ωb (ambos ejes) y Vn/Ωv (ambos ejes) coinciden dentro de 0.2 %.
  En 16×16×5/16 el eje fuerte da 2 814 396 con el modelo de Se de líneas medias (M3); el modelo con eje neutro
  desplazado en el patín comprimido (M1) da 2 815 301 (+0.03 %). Ambos valores están en la prueba
  `verificacion_posterior/hss/test_hss.py`.
- Ix de 16×16×1/2 (alerta del catálogo): el diseño usa Sx, rx y ry impresos, no Ix. La alerta no cambia ningún
  resultado de diseño. Si se usara S = I/c, Mn eje x bajaría 1.1 %.

## 5. Limitaciones y pendientes

- Torsión en IR, CE y LI: no se verifica, como antes. Si una barra de esos perfiles tiene T distinto de cero, la
  memoria lo indica en los supuestos de la barra.
- Torsión en HSS: la demanda es el máximo de los extremos, sin verificar la torsión a lo largo de la barra (la
  torsión uniforme podría variar en el tramo). Se usa la C de la nota de usuario, que AISC indica como conservadora.
- Nota [c] de la Tabla 12.1.2 (1.12√(E/Fy)): se interpreta como límite de patines de vigas. No se aplica a paredes
  comprimidas. Por confirmar.
- Grado de acero, Fy y Fu del A500 Gr C: por confirmar (dato de entrada).
- Las 7 filas con alerta de catálogo: se mantienen como vienen. Por confirmar con ATC.
- Modelo de Se (F7-3): líneas medias de las paredes, sin radios de esquina (M3). Diferencia de 2 % frente a S del
  catálogo en una sección compacta de referencia; 0.03 % frente al modelo M1 en la sección esbelta.
- Excel de escritorio: no probado (solo LibreOffice).

## 6. Torsión (H3) en HSS: verificación

- Pruebas unitarias en `verificacion_posterior/hss/test_hss.py`: Tc de 8×8×1/2 (H3-3) contra cálculo a mano;
  regímenes H3-4 (h/t = 70) y H3-5 (h/t = 100); H3-6 con Tr = 0.5·Tc y H1 con Tr = 0.1·Tc.
- Caso de extremo a extremo `verificacion_posterior/hss/planilla_torsion_ENTRADA.xlsx`: un momento de 70 000 kgf·m
  alrededor de X en el nodo 8 (estado Sobrecarga, combinación ASD2). La viga 13 (HSS 10 × 6 × 3/8) tiene
  Tr = 191 112 kgf·cm, Tc = 769 266 kgf·cm, Tr/Tc = 0.248 (usa H3-6). El H3-6 se recalculó a mano con las
  demandas de BARRAS y da 0.1769, igual que el notebook.
- Regresión: ejemplo gravitacional y caso sísmico sin cambios en IR, CE ni LI (solo el texto de alcance de RESUMEN).
  Las columnas nuevas (utilización de torsión y H3-6) van al final de DETALLE y RESULTADOS.
- Valores normativos en la hoja NORMA: AISC_OMEGA_T_HSS, AISC_H3_LIM1, AISC_H3_LIM2, AISC_H3_LIM3, AISC_H3_K,
  AISC_H3_FCR_Y y AISC_H3_20PCT, con su cláusula.

## 7. Tamaño del notebook

- El importador de la plataforma acepta hasta 1 MB. El notebook quedó en 0.80 MB porque la base de perfiles
  (280 registros) se guarda en el notebook como texto comprimido (zlib + base64). `perfiles_gerdau_nb.py` lo descomprime
  al cargarse. La plantilla de Excel embebida (317 KB en base64) no cambió.

## 8. Espesor de diseño de HSS (AISC 360-22 B4.2)

- Regla: t de diseño = 0.93 × t nominal para HSS distinto de ASTM A1065/A1085 (AISC 360-22 B4.2). El catálogo ATC no
  indica la norma del producto: se supone que no es A1065/A1085. Por confirmar con el fabricante.
- Valor en la hoja NORMA: `AISC_B42_HSS` = 0.93, con su cláusula. Si falta, `cargar_norma` da error (no se supone).
- Propiedades de diseño: catálogo × razón de la sección de esquina viva con t de diseño y con t nominal, para A, Ix,
  Iy, Sx, Sy, Zx, Zy y J; rx = rx,catálogo · √(razón I / razón A). Con factor 1.0 se reproduce el catálogo exacto.
  Con esta razón solo cambia el espesor: no se mezclan los radios de esquina del catálogo con una fórmula sin radios.
- Ancho y peralte planos (bp = B − 3t, hp = H − 3t) con el t de diseño. La masa por metro no cambia.
- El análisis (OpenSees) usa las propiedades nominales del catálogo. Pendiente: confirmar si el análisis también debe
  usar el espesor de diseño.
- Prueba: `verificacion_posterior/hss/test_b42_hss.py` (factor 1.0 exacto; factor 0.93 contra cálculo independiente;
  clave faltante; exclusión de KL/r en vigas).
- La memoria muestra el espesor nominal y el de diseño en la sección de propiedades, y una nota de B4.2 en la barra.

## 9. Memoria: orden del cálculo por barra

- Sección 1: "Orden del cálculo por barra" con seis pasos: datos y propiedades, demandas, esbeltez (B4.1 y KL/r),
  resistencias (D, E, F, G, H3), interacción (H1, H2, H3) y resultado.
- Sección 7: cada barra crítica se presenta con esos mismos pasos numerados, con ecuaciones y referencias.
- KL/r ≤ 200 se verifica solo en miembros comprimidos; las vigas quedan fuera (decisión del proyecto).
