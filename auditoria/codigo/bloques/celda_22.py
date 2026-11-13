# celda 22 del notebook; bloque anterior: ## Bloque 9b. Deformada con escala editable
# Deformada por estado y combinacion. Escala editable: cambie ESCALA_DEFORMADA y ejecute solo esta celda.
# None = automatica (el mayor desplazamiento mide el 10 % de la dimension del modelo).
# Ejemplo: ESCALA_DEFORMADA = 50  (multiplica los desplazamientos por 50 en el dibujo).
# No modifica el calculo ni el Excel de resultados (DEFORMADA guarda los desplazamientos sin escalar).
ESCALA_DEFORMADA = None

import analisis_opensees as AO
if dib is None or 'casos' not in globals():
    print('Ejecute primero el bloque 9 (analisis).')
else:
    AO.figura_deformada(dib, casos, id_de_indice, escala=ESCALA_DEFORMADA).show(renderer='iframe')
