# celda 20 del notebook; bloque anterior: ## Bloque 9. Análisis con OpenSees y Excel de resultados
# Analisis lineal con OpenSees y Excel de resultados. Todo sale de la planilla (bloques 6 y 7).
import subprocess
import sys
from IPython.display import display, Image

try:
    import openseespy.opensees  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'openseespy'], check=True)
import analisis_opensees as AO

RUTA_RESULTADOS = 'resultados_soportes.xlsx'
if dib is None:
    print('Sin modelo para analizar: corrija la planilla (bloque 7).')
else:
    try:
        bloques, equilibrio, casos = AO.correr_desde_planilla(dib, materiales_leidos, estados_df, nodos, barras,
                                                              dib.id_barra_de_indice, id_de_indice, RUTA_RESULTADOS)
    except AO.ErrorAnalisis as error:
        print('NO se analizo. Corrija lo siguiente en la planilla y vuelva a ejecutar este bloque:')
        print(error)
    else:
        print('Equilibrio global por estado (residuo de fuerzas, debe ser ~0 kgf):')
        for nombre, residuo in equilibrio:
            print(f'  {nombre}: {residuo:.3g} kgf')
        if bloques['BARRAS'].empty and bloques['NODOS'].empty:
            print('Ninguna barra ni nodo marcado REPORTAR = SI: el Excel de resultados no tiene datos.')
        print(f"Excel de resultados: {RUTA_RESULTADOS}")
        print('Hojas: RESUMEN (con ejes locales), BARRAS, NODOS, REACCIONES, MAXIMOS_BARRAS, DEFORMADA')
        print(f"Filas: barras {len(bloques['BARRAS'])}, nodos {len(bloques['NODOS'])}, "
              f"reacciones {len(bloques['REACCIONES'])}, maximos {len(bloques['MAXIMOS_BARRAS'])}")
        print('Ejes locales y signos:')
        display(Image(filename='ejes_locales.png', width=1000))
        print('Maximos y minimos por barra y caso (primeras filas):')
        display(bloques['MAXIMOS_BARRAS'].head(12))
        print('Deformada: ver la celda siguiente (escala editable, no vuelve a resolver).')
