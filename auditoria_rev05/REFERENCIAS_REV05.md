# Referencias normativas y fuentes: revision 03

Estado de cada fuente. Los documentos de terceros no se incluyen en el paquete (derechos de autor); se identifican por SHA-256 para que el auditor pueda compararlos con su copia.

| archivo recibido | que es | uso y estado | SHA-256 |
|---|---|---|---|
| `9c401816-aisc-360-22-16thedition_1.7z` | AISC 360-22 (archivo 7z; PDF interno "aisc-360-22-16thedition 1.pdf") | Usado: B4.1 (pag. 16.1-19), Tabla B4.1a caso 5 (pag. 16.1-21), Tabla B4.1b casos 10 a 15 (pag. 16.1-22 y 16.1-23). No incluido: documento de terceros. | `b9db21be767bac46dae0a86f7978403a3e4c7e1205d51e466e1c7c9080ac1d84` |
| `c335dc82-Solicitud_Antecedentes_Auditoria_Soportes_Rev00.md` | Solicitud del auditor (rev00, 13 nov 2026) | Base de esta respuesta. | `3135188beb155f4954b628d608cbd1df4e130198a3419c676f01c0423f6c8179` |
| `b87bc285-aisc-dg1-placas-base-y-anclas.md` | Resumen de AISC Design Guide 1, 2.a ed. (texto extraido; el PDF no esta en la sesion) | Usado para placas base. Paginas verificadas en imagen (segun el resumen): 14, 19 y 42. Resto: texto no verificado. | `59d6ba5acb7d81c665efa698af266451a2d7e4bf918b254d2e2762a509686a02` |
| `3cbd132c-IMCA-5ta-ed-guia-diseno-acero.md` | Extracto de la guia IMCA 5.a ed. | Usado: II-89 (KL/r <= 200), II-218 (J8). No incluido. | `84eb7ed274da77c97b4ccaba320201786f7be93e4d45f771afebd1592d833c99` |
| `5762cee2-respuesta-solicitud-imca.md` | Respuesta del chat IMCA, ronda 1 | Referencia interna. | `180c3a41ec51c6c71eab886fcd542b63b45950e6ddbe80d59f9ff85c0a61073f` |
| `46eed0fc-respuesta-solicitud-imca-ronda2.md` | Respuesta del chat IMCA, ronda 2 | Referencia interna. | `5808bf9c62b91e3b1407b84ce35de606925d9282df8db66ba6e8f72aaa324f78` |
| `39038301-NORMA_TECNICA_COMPLEMENTARIAS_PARA_DISE_O_Y_CONSTRUCCION_DE_ESTRUCTRAS_DE_ACERO.7z` | NTC-Acero CDMX (archivo 7z) | NO APLICA al diseno (decision del usuario). No revisado en esta entrega. | `2f0b9566c171cfae6080322aacca73e6f4ad2cb24b824c4da97fc2d557549f4a` |
| `152ac343-Mexico_2023-09-16_NTC-SISMO_-_Para_Entrega.zip` | Archivo de NTC sismo (zip) | Origen y edicion no resueltos (R-05). No se calculan cargas sismicas en el notebook. | `d63562cb83bc9f160095d0794d795c198cd032ee0c6d370f15ceb61682cb94d5` |
| planilla del proyecto (nombre omitido) | Planilla del proyecto (entrada del usuario) | Datos del proyecto: no incluido en el paquete. Solo su hash. | `3c364a9cc13905167c4390ba86d14393ac65b772d7dacc072d5f446af879430b` |
| `64f9f793-resultados.s2k` | Modelo SAP2000 de comparacion (proyecto) | Datos del proyecto: no incluido. Solo su hash. | `614937d83010754ab54a35f6948082a45ff6a4ecc08011204e9159cdb05b0f5b` |

## Pendiente de fuente

- AISC Design Guide 1, 2.a ed.: el PDF completo no esta en la sesion. Solo el resumen. Confirmar paginas 3.1.2 (espesor de placa) y 3.2.1 (A_t) en imagen.
- ACI 318-02, Apendice D (D.5.2, ecuacion D-7): no disponible. El valor de k = 10 (SI) y el texto no estan verificados.
- IMCA 5.a ed., capitulo J completo (J8-1, J8-2 verificadas en imagen en II-218; J3, J2.4 y J10 no leidos).
- Base Gerdau rev04: catalogo JSON en `fuentes_notebook/datos/` (SHA-256 c5fdf1b1b09a9a7e98bfcdc92504a2b258bfc54d9571d1548eda3595ac0b3754, segun la rev02). 30 valores completados verificados contra las paginas impresas 26 y 27 (rev02).

## Verificaciones de la revisión 05 (texto extraído de AISC 360-22; no en imagen)

| tema | referencia | hallazgo |
|---|---|---|
| espesor de diseño de HSS | AISC 360-22 §B4.2 (texto extraído) | t = nominal para HSS según ASTM A1065/A1085; para otras normas, t = 0.93 · nominal |
| E7 (elementos esbeltos) | AISC 360-22 §E7.1, pág. 16.1-48 (E7-2, E7-3, E7-5) y Tabla E7.1 en pág. 16.1-49 | E7-2: be = b si λ ≤ λr·√(Fy/Fn). E7-5: Fel = (c2·λr/λ)²·Fy. Tabla E7.1: alma c1 = 0.18, c2 = 1.31; patín/otros c1 = 0.22, c2 = 1.49 |
| LTB en HSS (F7) | AISC 360-22 §F7, pág. 16.1-63 y siguientes | Ecuaciones de LTB numeradas F7-8 (inelástico), F7-9 (elástico), F7-10 (Lp), F7-11 (Lr). La excepción de HSS cuadrados no aparece en el texto de F7 extraído |
| alma de I en flexión | AISC 360-22 Tabla B4.1b, caso 15, pág. 16.1-23 | λp = 3.76·√(E/Fy), λr = 5.70·√(E/Fy) |
| catálogo ATC de HSS | `c56426e1-catalogo_atc_para_agregar_tubulares_a_base_de_datos.pdf` (61 págs.) | Las tablas dan espesor de alma (tw) y de patín (tf). El texto del catálogo no indica si es nominal o de diseño, ni la norma del producto |
