# Bloque 10b: placas base (ASD). Datos en la hoja BASES; cargas = combinaciones de servicio de REACCIONES (bloque 9).
# Aplastamiento (IMCA cap. J), espesor de placa, pernos a traccion y cortante, cono de concreto y soldadura
# (AISC Design Guide 1 y ACI 318-02). Lo que no se verifico en imagen queda marcado NO REVISADO en la memoria.
import placas_base as PB
from IPython.display import display
BASES_RESULTADOS = None
if dib is None or 'bloques' not in globals() or 'REACCIONES' not in bloques:
    print('Ejecute primero el bloque 9 (analisis).')
elif BASES_FILAS is None:
    print('La planilla no tiene la hoja BASES: no hay placas base que verificar.')
elif NOR_LEIDA is None:
    print('La planilla no tiene la hoja NORMA: no se puede verificar la placa base.')
elif not BASES_FILAS:
    print('La hoja BASES no tiene filas con datos: no hay placas base que verificar.')
else:
    BASES_RESULTADOS = PB.diseno_bases(dib, id_de_indice, BASES_FILAS, bloques['REACCIONES'], NOR_LEIDA['VALORES'])
    _sin_datos = [r for r in BASES_RESULTADOS if r['estado'] in ('SIN DATOS', 'FALTA NORMA', 'DATO INVALIDO')]
    if _sin_datos:
        print('AVISO: no se calculan placas base en estos nodos (hoja BASES de su planilla):')
        for r in _sin_datos:
            _falta = ', '.join(list(r.get('faltan', [])) + list(r.get('norma', [])))
            print(f"   nodo {r['id']}: falta(n) {_falta or r.get('notas')}")
        print('   Si su planilla es anterior: agregue en BASES las columnas PERNOS EN X (Nx) y PERNOS EN Y (Ny) '
              '(2+2 = 2 y 2), o use la plantilla nueva plantilla_soportes.xlsx.')
    _oc = NOR_LEIDA['VALORES'].get('BASE_OMEGA_C')
    if _oc is not None and abs(float(_oc) - 2.5) > 1e-9:
        print(f'AVISO: en la hoja NORMA de su planilla BASE_OMEGA_C = {float(_oc):g}; el criterio DG1 es 2.50. '
              'Actualice esa celda (el calculo usa el valor de su planilla).')
    display(PB.tabla_resumen(BASES_RESULTADOS))
    print('Placas base: resumen arriba. El detalle de cada verificacion (ecuaciones y valores) va en la memoria (bloque 11).')
