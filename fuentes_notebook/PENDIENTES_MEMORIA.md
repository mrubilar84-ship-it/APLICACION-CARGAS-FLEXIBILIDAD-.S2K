# Pendientes retirados de la memoria de cálculo

Registro interno. Por indicación del usuario, estos textos ya no salen en la memoria de cálculo (`memoria_asd.py`).
Siguen siendo pendientes reales del cálculo: revisarlos antes de dar el cálculo por cerrado.

## Placas base (sección 8)
- Momento en la base sin compresión, torsión MZ y contacto biaxial: no verificados. Se marcan en la lista de notas de `placas_base.py`.
- Levantamiento: flexión de la placa por los pernos no verificada; levantamiento con momento en X solo con pernos en la dirección N.
- Interacción tracción–corte: se usa AISC 360-22 J3-3b con coeficientes de DG1. La ecuación de DG1 no está verificada en imagen.
- Pernos (limitaciones fijas de `placas_base.py`): arrancamiento lateral, rotura lateral y pryout no verificados; efecto de grupo y distancias al borde del cono no verificados (el cono se calcula sin reducción: un cono por lado, A_Nc = A_Nco); espesor del elemento al que se fijan los pernos no verificado.
- Cono ACI 318-02 Ap. D (ec. D-7): texto no verificado en imagen.
- Soldadura: modelo simplificado (cortante y tensión); no es un modelo de grupo de soldadura y no verifica el momento.
- Transferencia de compresión por contacto (columna a placa): no verificada.
- Cortante: se resiste con pernos y soldadura; no se considera fricción entre placa y concreto (práctica chilena).
- DG1 §3.2 (anclas) no verificado en imagen. DG1 §3.1.2 (espesor) es texto extraído. φ = 0.90 y Ω = 1.67 no verificados en imagen.
- Valores de NORMA marcados NO REVISADO en la hoja NORMA.

## Análisis y modelo (sección 4)
- Análisis elástico de primer orden (OpenSees, lineal): efectos P-Δ, P-δ e imperfecciones no incluidos; estabilidad del marco no revisada.
- AISC C2 (B1/B2, segundo orden) no aplicado: requiere K2 del pandeo elástico del piso, que la planilla no contiene.

## Barras
- Ángulos: pandeo flexotorsional (E4) no implementado; si b/t > 0.71·√(E/Fy) la barra queda NO REVISADO.
- Ángulos LI: el análisis usa Ix = Iy del catálogo (decisión del proyecto), sin producto de inercia; no demostrado.
- Ángulos sin E5 verificado: se usa K·L/rz y H2.
- Torsión de barras: H3 aplica solo a HSS en esta versión.
- Material sin Fu en MATERIALES: barras sin verificación.
- Texto anterior "No se verifican conexiones, placas, soldaduras ni pernos": ya no es cierto para placas base (sección 8); revisar.

## HSS
- Espesor de diseño 0.93·t (AISC 360-22 B4.2) aplicado a todos los HSS: la norma del producto no figura en el catálogo; confirmar con el fabricante.

## Predimensionamiento
- Las secciones de la memoria son de predimensionamiento: cambiar una sección cambia la rigidez y las demandas; hay que volver a correr el análisis.

## Estados de barra NO REVISADO por datos faltantes
- Se mantienen en la memoria (estado de datos, no comentario). Pendiente de decisión.

## Alternativa con atiezador (sección 8.i.3b)
- Aproximación: el voladizo que gobierna se reduce a la mitad (atiezador a media distancia entre patín y borde). No cambia el veredicto principal.
- El atiezador no se dimensiona: espesor, soldadura al patín y a la placa, flexión y corte no verificados. Su posición real y su método de DG1 para placas rigidizadas no están en la fuente disponible.

## Derivas de entrepiso bajo sismo (hoja DESPLAZAMIENTOS, memoria 6.3)
- LIMITE_DERIVA: el criterio W40428 no fija el límite de deriva de entrepiso para racks. Sin valor confirmado (MDOC de sismo CFE 2015 o Wood) la memoria muestra PENDIENTE; nunca OK.
- Convención de desplazamientos (ELASTICO o AMPLIFICADO): se registra en la hoja. El modelo es elástico lineal; si el MDOC exige amplificar δ, el resultado cambia.
- Deflexión horizontal de vigas y columnas (sección 12, δ ≤ L/λ): fuera de esta versión.
