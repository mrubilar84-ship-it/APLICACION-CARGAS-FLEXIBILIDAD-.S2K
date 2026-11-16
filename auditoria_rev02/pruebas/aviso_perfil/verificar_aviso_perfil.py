"""Prueba del aviso EJECUCION de PERFIL_GRUPO (planilla_con_diseno.xlsx) con LibreOffice headless.
Uso: python3 verificar_aviso_perfil.py <planilla_con_diseno.xlsx> <carpeta_de_trabajo>
Casos: sin cambio (debe decir vigente), cambio de perfil de COLUMNA (debe decir DESACTUALIZADO),
vuelta al perfil analizado (vigente) y perfil vacio (SIN PERFIL). Sale con codigo 0 solo si los 4 casos cumplen."""
import os, sys, shutil, subprocess, openpyxl
XCU = ('<?xml version="1.0" encoding="UTF-8"?>\n<oor:items xmlns:oor="http://openoffice.org/2001/registry" '
       'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
       '<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse">'
       '<value>0</value></prop></item>\n</oor:items>\n')
src, trabajo = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(os.path.join(trabajo, 'perfil', 'user'), exist_ok=True)
open(os.path.join(trabajo, 'perfil', 'user', 'registrymodifications.xcu'), 'w', encoding='utf-8').write(XCU)
ESPERADO = {
    'sin_cambio':     (lambda ws: None,                                      'vigente'),
    'cambio_columna': (lambda ws: ws.__setitem__('B2', 'IR 12 × 16'),        'DESACTUALIZADO'),
    'vuelve_igual':   (lambda ws: (ws.__setitem__('B2', 'IR 12 × 16'), ws.__setitem__('H2', 'IR 12 × 16')), 'vigente'),
    'sin_perfil':     (lambda ws: ws.__setitem__('B3', None),                'SIN PERFIL'),  # fila 3 = VIGA
}
ok_total = True
for nombre, (cambio, esperado) in ESPERADO.items():
    wb = openpyxl.load_workbook(src); cambio(wb['PERFIL_GRUPO'])
    caso = os.path.join(trabajo, nombre + '.xlsx'); wb.save(caso)
    out = os.path.join(trabajo, 'salida_' + nombre); os.makedirs(out, exist_ok=True)
    subprocess.run(['soffice', '-env:UserInstallation=file://' + os.path.join(trabajo, 'perfil'), '--headless', '--calc',
                    '--convert-to', 'xlsx', '--outdir', out, caso], check=True, capture_output=True, timeout=600)
    fila = 3 if nombre == 'sin_perfil' else 2   # fila del grupo que se modifica
    texto = openpyxl.load_workbook(os.path.join(out, nombre + '.xlsx'), data_only=True)['PERFIL_GRUPO'].cell(row=fila, column=9).value
    ok = str(texto).startswith(esperado)
    ok_total &= ok
    print(('OK   ' if ok else 'FALLA'), nombre, '| EJECUCION fila', fila, '=', texto, '| esperado empieza con', esperado)
print('RESULTADO:', 'OK' if ok_total else 'FALLA')
sys.exit(0 if ok_total else 1)
