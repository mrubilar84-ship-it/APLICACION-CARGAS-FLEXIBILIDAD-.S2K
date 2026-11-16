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
| Cortante | G2.1 con Aw = 2·h·t; G2.2 (kv = 5) | h = peralte plano (eje fuerte) o ancho plano (eje débil). Ωv = 1.67. |
| Interacción | H1-1a/b | Igual que IR, CE y LI. |
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
- Valores de referencia de tres secciones (`verificacion_posterior/hss/`): pendiente de la comprobación
  independiente.

## 5. Limitaciones y pendientes

- Torsión (T de BARRAS): no se verifica en HSS, igual que en IR, CE y LI. Los tubos resisten torsión y es
  probable que sea gobernante en algunas barras. Requiere decisión: incorporar H3 o declarar el alcance.
- Nota [c] de la Tabla 12.1.2 (1.12√(E/Fy)): se interpreta como límite de patines de vigas. No se aplica a paredes
  comprimidas. Por confirmar.
- Grado de acero, Fy y Fu del A500 Gr C: por confirmar (dato de entrada).
- Las 7 filas con alerta de catálogo: se mantienen como vienen. Por confirmar con ATC.
- Modelo de Se (F7-3): líneas medias de las paredes, sin radios de esquina. Diferencia de 2 % frente a S del
  catálogo en una sección compacta de referencia.
- Excel de escritorio: no probado (solo LibreOffice).
