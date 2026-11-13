"""Verificacion de planilla_con_diseno.xlsx en LibreOffice headless.
Uso: python3 verificar_libreoffice.py <planilla.xlsx> <reporte.md> [perfil_alterno]
(1) recalcula todo el libro al abrirlo; (2) compara los valores recalculados con los guardados;
(3) cuenta celdas con error; (4) cambia PERFIL_GRUPO!B2 y muestra que celdas cambian, sin volver a ejecutar OpenSees.
Requiere soffice en el PATH. Probado con LibreOffice 24.2.7.2."""
import os, sys, shutil, subprocess, tempfile, collections, hashlib
import openpyxl

XCU = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" '
       'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
       '<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse">'
       '<value>0</value></prop></item>\n</oor:items>\n')
ERR = ('#N/A', '#VALUE!', '#REF!', '#NAME?', '#DIV/0!', '#NUM!', '#NULL!', 'Err:')

def recalcular(xlsx, carpeta):
    perfil = os.path.join(carpeta, 'perfil_lo')
    os.makedirs(os.path.join(perfil, 'user'), exist_ok=True)
    with open(os.path.join(perfil, 'user', 'registrymodifications.xcu'), 'w', encoding='utf-8') as f:
        f.write(XCU)
    salida = os.path.join(carpeta, 'salida'); os.makedirs(salida, exist_ok=True)
    subprocess.run(['soffice', '-env:UserInstallation=file://' + os.path.abspath(perfil), '--headless', '--calc',
                    '--convert-to', 'xlsx', '--outdir', salida, xlsx], check=True, timeout=900, capture_output=True)
    return os.path.join(salida, os.path.basename(xlsx))

def igual(a, b):
    if a == b: return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-9 * max(1.0, abs(a))
    return False

def comparar(ruta_a, ruta_b):
    A = openpyxl.load_workbook(ruta_a, data_only=True); B = openpyxl.load_workbook(ruta_b, data_only=True)
    res = collections.OrderedDict()
    for ws in A.worksheets:
        wb_ = B[ws.title]; n = 0; tot = 0; ej = []
        for row in ws.iter_rows():
            for c in row:
                a = c.value; b = wb_[c.coordinate].value
                if a is None and b is None: continue
                tot += 1
                if not igual(a, b):
                    n += 1
                    if len(ej) < 3: ej.append((c.coordinate, str(a)[:40], str(b)[:40]))
        res[ws.title] = (n, tot, ej)
    return res

def errores(ruta):
    W = openpyxl.load_workbook(ruta, data_only=True); cuenta = collections.OrderedDict()
    for ws in W.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith(ERR):
                    cuenta[ws.title] = cuenta.get(ws.title, 0) + 1
    return cuenta

def main():
    entrada = os.path.abspath(sys.argv[1]); reporte = os.path.abspath(sys.argv[2])
    alterno = sys.argv[3] if len(sys.argv) > 3 else 'IR 12 × 16'
    trabajo = tempfile.mkdtemp(prefix='lo_')
    try:
        copia = os.path.join(trabajo, 'entrada.xlsx'); shutil.copy(entrada, copia)
        rec = recalcular(copia, os.path.join(trabajo, 'orig'))
        cache_vs_lo = comparar(copia, rec)
        err = errores(rec)
        wb = openpyxl.load_workbook(copia); ws = wb['PERFIL_GRUPO']
        previo = ws['B2'].value; ws['B2'].value = alterno
        cam_src = os.path.join(trabajo, 'cambio.xlsx'); wb.save(cam_src)
        cam = recalcular(cam_src, os.path.join(trabajo, 'cambio'))
        cambio = comparar(rec, cam)
        ver = subprocess.run(['soffice', '--version'], capture_output=True, text=True).stdout.strip()
        L = ['# Verificacion en LibreOffice de planilla_con_diseno.xlsx', '',
             f'- Herramienta: {ver}', f'- Entrada: {os.path.basename(entrada)} (SHA-256 {hashlib.sha256(open(entrada, "rb").read()).hexdigest()})',
             '- Recalculo forzado al abrir (OOXMLRecalcMode = 0).', '',
             '## 1. Recalculo contra valores guardados', '', '| hoja | celdas comparadas | distintas | ejemplo |', '|---|---|---|---|']
        for h, (n, tot, ej) in cache_vs_lo.items():
            L.append(f'| {h} | {tot} | {n} | {ej[0] if ej else "-"} |')
        L += ['', 'Celdas con valor de error despues de recalcular (por hoja):', '']
        for h, n in err.items(): L.append(f'- {h}: {n}')
        L += ['', '## 2. Cambio de perfil en la lista (sin volver a ejecutar OpenSees)', '',
              f'PERFIL_GRUPO!B2 cambia de "{previo}" a "{alterno}". Celdas que cambian despues de recalcular:', '',
              '| hoja | celdas distintas | ejemplos (celda, antes, despues) |', '|---|---|---|']
        for h, (n, tot, ej) in cambio.items():
            if n: L.append(f'| {h} | {n} | {"; ".join(str(e) for e in ej)} |')
        L += ['', 'Lectura: la lista y las formulas de FU recalculan; rigidez, peso y esfuerzos no cambian porque OpenSees no se vuelve a ejecutar.']
        os.makedirs(os.path.dirname(reporte), exist_ok=True)
        open(reporte, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('reporte escrito')
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)

if __name__ == '__main__':
    main()
