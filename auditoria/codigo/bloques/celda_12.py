# celda 12 del notebook; bloque anterior: ## Bloque 6. Cargar plantilla Excel
# Plantilla Excel: escribe el libro completo (NODOS, BARRAS, CARGAS, ESTADOS, CONEXIONES, LISTAS, VISTA_VIVA).
# La misma funcion regenera el Excel con sus datos en el bloque 8, asi nada se pierde al guardar.
import os
import base64
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
COLS_MATRIZ_XL = ['CLAVE', 'ID', 'PERFIL', 'ELEMENTO DISENO', 'FU MAXIMO', 'FU DEMANDA',
                  'FU ESBELTEZ LOCAL (B4.1)', 'FU ESBELTEZ GLOBAL (KL/r<=200)',
                  'FU DUCTILIDAD (12.1.2, 12.1.3.1)', 'CASO QUE GOBIERNA', 'ESTADO']
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.drawing.image import Image as XLImage
from openpyxl.workbook.properties import CalcProperties
from dibujo_directo import DibujoModelo, ELEMENTOS, TIPOS_APOYO, TIPOS_CONEXION
import perfiles_gerdau as G
import pandas as pd

NODOS_COLS = ['ID', 'X (m)', 'Y (m)', 'Z (m)', 'UX', 'UY', 'UZ', 'RX', 'RY', 'RZ', 'NOTA', 'REPORTAR']
GRADOS_COLS = ['UX', 'UY', 'UZ', 'RX', 'RY', 'RZ']       # columnas E..J de NODOS: SI = grado restringido
BARRAS_COLS = ['ID', 'NODO_I', 'NODO_J', 'ELEMENTO', 'PERFIL', 'EJE_FUERTE_X', 'EJE_FUERTE_Y', 'EJE_FUERTE_Z',
               'CONEXION_I', 'CONEXION_J', 'MATERIAL', 'NOTA', 'REPORTAR', 'DUCTILIDAD']
MAT_MAX = 10
MAT_FIN = MAT_MAX + 1
# Valores de partida de la plantilla. Son datos de ENTRADA en la hoja MATERIALES: el notebook los lee de ahi
# (no los fija). E = 200 000 MPa = 2 038 900 kgf/cm2 y NU = 0.3, igual que A-36 en el modelo SAP CMZ-5746.
E_ACERO_PARTIDA = 2038900
NU_ACERO_PARTIDA = 0.3
MATERIALES_DEFAULT = [
    ['A-36', 'Acero', 2530, 4078, E_ACERO_PARTIDA, NU_ACERO_PARTIDA,
     'Manual Gerdau, pie de pagina 22 (fy). Fu y E: modelo SAP CMZ-5746 (A36).'],
    ['A-529 G 50', 'Acero', 3515, 4570, E_ACERO_PARTIDA, NU_ACERO_PARTIDA,
     'Manual Gerdau, pie de pagina 22 (fy). Fu 65 ksi: referencia Gerdau Corsa (confirmar). E y NU: confirmar.'],
    ['A-572
# (contenido grande omitido: plantilla embebida)
