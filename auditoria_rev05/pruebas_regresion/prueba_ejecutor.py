"""Prueba del ejecutor (R04-19): un notebook con error debe salir con codigo distinto de cero; uno completo, con 0."""
import json, os, subprocess, sys, tempfile

RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ejecutor', 'ejecutar_nb.py')
casos = [('error_al_inicio', ['raise RuntimeError("FALLO_A")', 'x = 1'], 1),
         ('error_al_final', ['x = 1', 'raise ValueError("FALLO_B")'], 1),
         ('completo', ['x = 1', 'print("hola")'], 0)]
fallas = 0
for nombre, celdas, esperado in casos:
    with tempfile.TemporaryDirectory() as d:
        ruta = os.path.join(d, 'prueba.ipynb')
        json.dump({'cells': [{'cell_type': 'code', 'source': [c]} for c in celdas]}, open(ruta, 'w'))
        r = subprocess.run([sys.executable, RUN, ruta], capture_output=True, text=True)
        ok = r.returncode == esperado
        fallas += (not ok)
        print(f"{'OK   ' if ok else 'FALLA'} {nombre}: codigo={r.returncode} esperado={esperado} | "
              f"{r.stdout.strip().splitlines()[-1][:100]}")
print(f"\nRESULTADO: {'OK' if not fallas else 'FALLA'} ({3 - fallas} de 3)")
sys.exit(1 if fallas else 0)
