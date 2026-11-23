"""Ejecuta, celda por celda y en orden, un notebook de soportes (R04-19).

Uso:  python3 ejecutar_nb.py <ruta.ipynb>
Escribe los modulos de las celdas %%writefile en la carpeta del notebook: use una carpeta vacia.
Sale con codigo 0 solo si TODAS las celdas de codigo terminan sin excepcion. Ante un error sale con codigo 1
y no reutiliza ni declara completas las salidas de la ejecucion truncada.
"""
import json, os, sys, traceback

if len(sys.argv) != 2:
    sys.exit('Uso: python3 ejecutar_nb.py <ruta.ipynb>')
NB = os.path.abspath(sys.argv[1])
os.chdir(os.path.dirname(NB))
sys.path.insert(0, os.getcwd())
nb = json.load(open(os.path.basename(NB), encoding='utf-8'))
ns = {'__name__': '__main__'}
try:
    from IPython.display import display
    ns['display'] = display
except Exception:
    ns['display'] = print

ok, fallo = 0, None
for i, c in enumerate(nb['cells']):
    if c['cell_type'] != 'code':
        continue
    src = ''.join(c['source'])
    if src.startswith('%%writefile '):
        primera, resto = src.split('\n', 1)
        nombre = primera.split()[1]
        with open(nombre, 'w', encoding='utf-8') as f:
            f.write(resto)
        print(f'[celda {i}] escrito {nombre}')
        continue
    src = '\n'.join(l for l in src.split('\n') if not l.lstrip().startswith(('%', '!')))
    try:
        exec(compile(src, f'celda{i}', 'exec'), ns)
        print(f'[celda {i}] OK')
        ok += 1
    except SystemExit as e:
        if e.code in (None, 0):
            print(f'[celda {i}] SALIDA (codigo 0)')
            ok += 1
            break
        fallo = i
        print(f'[celda {i}] ERROR: SystemExit con codigo {e.code}')
        break
    except Exception:
        fallo = i
        print(f'[celda {i}] ERROR')
        traceback.print_exc()
        break

if fallo is None:
    print(f'RESUMEN: EJECUCION COMPLETA ({ok} celdas de codigo OK)')
    sys.exit(0)
print(f'RESUMEN: EJECUCION INCOMPLETA en la celda {fallo} ({ok} celdas de codigo OK antes del error). No use las salidas de esta carpeta.')
sys.exit(1)
