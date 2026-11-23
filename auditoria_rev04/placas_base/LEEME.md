# Placas base: prueba independiente

`prueba_independiente.py` compara `placas_base.py` (bloque 10b) con cálculos escritos a mano dentro del propio archivo de prueba. No importa ninguna fórmula de `placas_base.py` para calcular las expectativas.

**Uso:** `DIBUJO=../codigo/fuentes_notebook python3 prueba_independiente.py` (sale con código 1 si alguna comprobación falla).

**Qué verifica:** f_adm de aplastamiento; FU de aplastamiento centrado, dentro del núcleo y fuera del núcleo en una dirección; espesor de placa (voladizo DG1); equilibrio de los pernos en tracción (residuo independiente); FU de tracción en pernos, de cono de concreto y de soldadura; levantamiento; cortante.

**Qué no verifica:** que las fórmulas de DG1 o de ACI 318-02 coincidan con la norma. Eso depende de la verificación en imagen de las páginas indicadas en `REFERENCIAS_REV03.md` y de `PENDIENTES_REV03.md` (P1, P2).

El perfil es sintético (H = 15 cm, B = 6 cm). No hay datos del proyecto en esta prueba.
