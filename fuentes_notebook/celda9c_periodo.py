# Bloque 9c: periodo natural del soporte (solo en el notebook; no va a la memoria de calculo).
# Masa = peso propio de las barras (masa Gerdau x longitud, hoja ESTADOS), repartido a los extremos; solo traslacion.
import analisis_opensees as AO
from IPython.display import display
PERIODOS = None
PERIODO_MEMORIA = None           # lo lee la memoria (6.4)
if dib is None or 'materiales_leidos' not in globals():
    print('Ejecute primero el bloque 9 (analisis).')
else:
    try:
        PERIODOS, PESO_PROPIO, PESO_NUDOS = AO.periodos(dib, materiales_leidos, estados_df, dib.id_barra_de_indice,
                                            factor_hss=None if NOR_LEIDA is None
                                            else NOR_LEIDA['VALORES'].get('AISC_B42_HSS'))
    except AO.ErrorAnalisis as error:
        print('NO se calcularon los periodos. Corrija lo siguiente y vuelva a ejecutar este bloque:')
        print(error)
    else:
        print(f'Masa del peso propio: barras {PESO_PROPIO:,.1f} kgf + cargas en nudos {PESO_NUDOS:,.1f} kgf '
              f'= {PESO_PROPIO + PESO_NUDOS:,.1f} kgf (la masa es ese peso dividido por g).')
        print(f'Periodo fundamental T1 = {PERIODOS.loc[0, "T (s)"]:.4f} s')
        PERIODO_MEMORIA = {'tabla': PERIODOS, 'barras': PESO_PROPIO, 'nudos': PESO_NUDOS}
        display(PERIODOS.round(4))
        print('Masa efectiva: porcentaje de la masa que se mueve en cada modo y direccion. Un modo con 0 % en las tres '
              'direcciones no mueve masa en traslacion (los giros no tienen masa en este modelo).')
