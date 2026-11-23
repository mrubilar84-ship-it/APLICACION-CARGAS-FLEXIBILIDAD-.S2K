"""Regenera plantilla_soportes.xlsx desde las fuentes de esta carpeta (base Gerdau rev04 y HSS del catalogo ATC,
hojas de diseno y NORMA de celda6_plantilla.py).
Uso:  python3 generar_plantilla.py SALIDA.xlsx
Requiere LibreOffice (soffice) para guardar los valores calculados, como la plantilla de la raiz del repositorio."""
import json, os, runpy, shutil, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))


def base_en(carpeta):
    """Arma en 'carpeta' los modulos de la base (perfiles_gerdau.py y gerdau_datos.py) con la misma logica que el
    notebook: el generador build_soportes_planilla3.py fusiona el catalogo Gerdau y los HSS."""
    nb_tmp = os.path.join(carpeta, 'nb_descartable.ipynb')
    sys_argv = sys.argv
    sys.argv = ['build_soportes_planilla3.py', nb_tmp]
    try:
        gen = runpy.run_path(os.path.join(D, 'build_soportes_planilla3.py'), run_name='generar_base')
    finally:
        sys.argv = sys_argv
    os.remove(nb_tmp)
    texto = json.loads(gen['datos_texto']())
    with open(os.path.join(carpeta, 'gerdau_datos.py'), 'w', encoding='utf-8') as f:
        f.write('_DATOS_TEXTO = ' + repr(texto) + '\n')
    shutil.copy(os.path.join(D, 'perfiles_gerdau_nb.py'), os.path.join(carpeta, 'perfiles_gerdau.py'))


def cargar_celda6():
    """Carga celda6_plantilla.py sin su bloque de notebook: la plantilla incrustada se deja vacia (el bloque la
    leeria) y display se sustituye por print. El codigo de la funcion de creacion no cambia."""
    import types
    ruta = os.path.join(D, 'celda6_plantilla.py')
    fuente = open(ruta, encoding='utf-8').read()
    marca = "PLANTILLA_B64 = '__PLANTILLA_B64__'"
    assert fuente.count(marca) == 1, 'marca de plantilla no encontrada en celda6_plantilla.py'
    fuente = fuente.replace(marca, "PLANTILLA_B64 = ''")
    mod = types.ModuleType('celda6_plantilla')
    mod.__file__ = ruta
    mod.display = print
    sys.modules['celda6_plantilla'] = mod
    exec(compile(fuente, ruta, 'exec'), mod.__dict__)
    return mod


def main(salida):
    salida = os.path.abspath(salida)
    carpeta = tempfile.mkdtemp(prefix='base_plantilla_')
    base_en(carpeta)
    sys.path[:0] = [carpeta, D]
    os.chdir(carpeta)
    C = cargar_celda6()
    C.crear_plantilla(salida, sobrescribir=True)
    print('plantilla escrita:', salida)


if __name__ == '__main__':
    main(sys.argv[1])
