import json, os, sys, traceback
NB = sys.argv[1]
os.chdir(os.path.dirname(os.path.abspath(NB)))
sys.path.insert(0, os.getcwd())
nb = json.load(open(os.path.basename(NB), encoding='utf-8'))
ns = {'__name__': '__main__'}
try:
    from IPython.display import display
    ns['display'] = display
except Exception:
    ns['display'] = print
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
    except SystemExit:
        print(f'[celda {i}] SystemExit'); break
    except Exception:
        print(f'[celda {i}] ERROR'); traceback.print_exc(); break
