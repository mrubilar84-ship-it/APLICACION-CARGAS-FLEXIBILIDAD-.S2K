# celda 27 del notebook; bloque anterior: ## Bloque 10. Diseño por AISC 360-22 (ASD)
# Diseno ASD con ANSI/AISC 360-22 (IR, CE, LI; CS fuera del diseno). Demandas: combinaciones de servicio de COMBINACIONES (bloque 9).
# Resultados POR GRUPO: elija la seccion de cada grupo en su desplegable; la tabla se recalcula al instante.
# "Aplicar" actualiza diseno_asd.xlsx (por elemento) y planilla_con_diseno.xlsx (PERFIL_GRUPO).
import copy
import pandas as pd
from IPython.display import display
import diseno_asd as DA
import memoria_asd as MA
if NOR_LEIDA is not None and dib is not None:
    DA.cargar_norma(NOR_LEIDA['VALORES'], CONF['kz'])   # valores de norma (hoja NORMA) y Kz (PARAMETROS)

RUTA_DISENO = 'diseno_asd.xlsx'
RUTA_PLANILLA_DISENO = 'planilla_con_diseno.xlsx'


def _escribir_planilla(perfiles, listas, fu_matriz):
    escribir_planilla(RUTA_PLANILLA_DISENO, _filas(nodos, NODOS_COLS), _filas(barras, BARRAS_COLS),
                      filas_cargas=filas_cargas_para_excel(cargas), materiales=materiales_filas,
                      combinaciones=comb_crudas,
                      longitudes=filas_longitudes_para_excel(longitudes_df),
                      estados=[[None if _vacio(v) else v for v in f] for f in estados_df.values.tolist()],
                      listas=listas, grupos_perfil=perfiles, fu_matriz=fu_matriz)
    guardar_con_valores(RUTA_PLANILLA_DISENO)


def _escribir_diseno(tabla_listas):
    with pd.ExcelWriter(RUTA_DISENO, mode='a', engine='openpyxl', if_sheet_exists='replace') as w:
        tabla_listas.to_excel(w, sheet_name='LISTAS_GRUPO', index=False)


if dib is None or 'bloques' not in globals():
    print('Ejecute primero el bloque 9 (analisis).')
else:
    try:
        perfiles_grupo = DA.perfil_por_grupo(dib)   # una sola seccion por grupo
        capacidades, resultados, detalle = DA.diseno_asd_desde_planilla(
            dib, materiales_leidos, longitudes_df, bloques['DISENO_BARRAS'], dib.id_barra_de_indice, RUTA_DISENO)
        fu_matriz = DA.matriz_fu_por_perfil(dib, materiales_leidos, longitudes_df, bloques['DISENO_BARRAS'],
                                            dib.id_barra_de_indice)
        listas, tabla_listas = DA.listas_desde_matriz(fu_matriz, dib)
    except DA.ErrorAsd as error:
        print('NO se diseno. Corrija lo siguiente y vuelva a ejecutar este bloque:')
        print(error)
    else:
        _escribir_diseno(tabla_listas)
        _escribir_planilla(perfiles_grupo, listas, fu_matriz)
        print(f'Diseno ASD (AISC 360-22). Excel: {RUTA_DISENO} (RESULTADOS por elemento, DETALLE, LISTAS_GRUPO)')
        print(f'Planilla con perfil por grupo: {RUTA_PLANILLA_DISENO} (hoja PERFIL_GRUPO)')
        con_barras = [g for g in DA.GRUPOS_ELEMENTO if any(b['elemento'] == g for b in dib.barras)]
        for g in DA.GRUPOS_ELEMENTO:
            if g not in con_barras:
                print(f'{g}: sin barras en el modelo.')
        try:
            import ipywidgets as W
            selectores, salidas = {}, {}
            for g in con_barras:
                ops = MA.opciones_grupo(fu_matriz, g)
                nombres = [n for _, n in ops]
                if perfiles_grupo[g] not in nombres:
                    ops.insert(0, (f'{perfiles_grupo[g]}  —  perfil actual', perfiles_grupo[g]))
                selectores[g] = W.Dropdown(options=ops, value=perfiles_grupo[g], description=f'{g}:',
                                           layout=W.Layout(width='760px'))
                salidas[g] = W.Output()

            def _mostrar(g):
                with salidas[g]:
                    salidas[g].clear_output(wait=True)
                    tabla = MA.resultados_grupo(dib, g, selectores[g].value, materiales_leidos, longitudes_df,
                                                bloques['DISENO_BARRAS'], dib.id_barra_de_indice)
                    ok = bool((tabla['ESTADO'] == 'CUMPLE').all())
                    print(f'{g}: {selectores[g].value} · {len(tabla)} barras · '
                          f'{"CUMPLE" if ok else "NO CUMPLE"}')
                    display(tabla)

            for g in con_barras:
                selectores[g].observe(lambda ch, g=g: _mostrar(g), names='value')
                _mostrar(g)

            boton = W.Button(description='Aplicar selección a diseno_asd.xlsx y planilla', button_style='primary')
            aviso = W.Output()

            def _aplicar(_):
                with aviso:
                    aviso.clear_output()
                    sel = {g: selectores[g].value for g in con_barras}
                    d2 = copy.copy(dib)
                    d2.barras = [dict(b, perfil=sel[b['elemento']]) if b['elemento'] in sel else b
                                 for b in dib.barras]
                    DA.diseno_asd_desde_planilla(d2, materiales_leidos, longitudes_df, bloques['DISENO_BARRAS'],
                                                 dib.id_barra_de_indice, RUTA_DISENO)
                    _escribir_diseno(tabla_listas)
                    _escribir_planilla(sel, listas, fu_matriz)
                    print('Actualizado con:', sel)

            boton.on_click(_aplicar)
            display(W.VBox([W.HTML('<b>Elija la sección de cada grupo.</b> La lista está ordenada por tipo y sección; '
                                   'la tabla se recalcula al cambiarla. Interacción = FU flexocompresión (H1/H2).')]
                           + [W.VBox([selectores[g], salidas[g]]) for g in con_barras] + [boton, aviso]))
        except ImportError:
            print('Sin ipywidgets: tablas por grupo con el perfil actual.')
            for g in con_barras:
                display(MA.resultados_grupo(dib, g, perfiles_grupo[g], materiales_leidos, longitudes_df,
                                            bloques['DISENO_BARRAS'], dib.id_barra_de_indice))
