# celda 29 del notebook; bloque anterior: ## Bloque 11. Memoria de cálculo (HTML)
# Bloque 11: memoria de calculo completa (HTML, imprimible a PDF). Usa el mismo calculo que el bloque 10.
# Datos del proyecto (portada). La configuracion de diseno y de norma sale de las hojas PARAMETROS y NORMA.
import memoria_asd as MA

PROYECTO = {
    'nombre': '(nombre del proyecto)',
    'elemento': '(estructura o elemento)',
    'fecha': '',
    'version': '(completar)',
    'elaboro': '',
    'reviso': '',
    'aprobo': '',
}
RUTA_MEMORIA = 'memoria_calculo.html'
if CONF is not None:
    PROYECTO['conf'] = CONF
if dib is None or 'bloques' not in globals() or 'DISENO_BARRAS' not in bloques:
    print('Ejecute primero el bloque 9 (analisis) y el bloque 10 (diseno).')
else:
    try:
        MA.memoria_html(dib, materiales_leidos, longitudes_df, bloques['DISENO_BARRAS'], dib.id_barra_de_indice,
                        RUTA_MEMORIA, PROYECTO, casos=casos, id_de_indice=id_de_indice, equilibrio=equilibrio)
    except DA.ErrorAsd as error:
        print('NO se genero la memoria. Corrija lo siguiente y vuelva a ejecutar este bloque:')
        print(error)
    else:
        print(f'Memoria de calculo: {RUTA_MEMORIA} (abrir y Imprimir > Guardar como PDF)')
