# Referencias normativas: extractos usados por el codigo

Texto extraido de los PDF que el proyecto cargo (pdftotext -layout). Cada extracto indica el archivo de origen y las lineas del texto. Las paginas impresas estan en el propio texto. Si una pagina no coincide, verificar contra el PDF original.


# NTC Diseno por Sismo 2023 (texto: Mexico 2023-09-16 NTC-SISMO - Para Entrega.pdf)


## 1.7 Revision de los desplazamientos laterales (LDNE, SV, OI)

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 1440-1500 del texto extraido.

```text
1.7      Revisión de los desplazamientos laterales

  La distorsión de entrepiso se define como la diferencia entre los desplazamientos laterales de los pisos consecutivos que lo
delimitan dividida entre la diferencia de elevaciones correspondiente. Para efectos de revisión, los desplazamientos laterales
se obtienen con un análisis que considera los efectos combinados de las fuerzas sísmicas de diseño y de las fuerzas
gravitacionales, y deberá considerarse la mayor distorsión de las que se calculan para cada elemento o subsistema vertical
contenido en el entrepiso (marcos, muros o cualquier otro elemento vertical). Para el cálculo de las distorsiones se deberán
incluir, cuando así proceda, los efectos de torsión, de segundo orden, bidireccionales, de interacción suelo-estructura, y de
flexibilidad de los diafragmas de piso establecidos en el capítulo 2, así como el factor de carga que corresponda según lo
establecido en 3.4 de la NTC-Criterios. La revisión de las distorsiones se deberá hacer de manera independiente para las dos
direcciones principales de análisis, y debe considerar los niveles de desempeño indicados en la tabla 1.1a, según el grupo al
que pertenezca la construcción de acuerdo con la clasificación de 1.4.

  Para el cumplimiento del nivel de desempeño de Seguridad de Vida, se revisará que las distorsiones obtenidas con el espectro
de diseño que corresponda a la intensidad sísmica de interés, establecido de acuerdo con el capítulo 3, multiplicadas por QR',
no excedan los valores especificados para la distorsión límite γSV en las tablas 4.3.1, 4.3.2, 4.3.3 y 4.3.4, según la estructuración
que se haya adoptado. Q es el factor de comportamiento sísmico especificado en las mismas tablas. El valor de R' se calculará
para el periodo fundamental de vibrar de la estructura en la dirección en que se revisan las distorsiones de acuerdo con 3.3.
Dado que el nivel de desempeño de Seguridad de Vida hace referencia al comportamiento de los elementos estructurales, se
le considera un estado límite de falla y, en consecuencia, se deben considerar los factores de carga prescritos por las NTC-
Criterios durante el análisis.

  Para el cumplimiento del nivel de desempeño de Ocupación Inmediata, se revisará que las distorsiones obtenidas con el
espectro elástico de diseño que corresponda a la intensidad sísmica de interés, establecido de acuerdo con el capítulo 3,
multiplicadas por R', no excedan los valores especificados para la distorsión límite γOI en las tablas 4.3.1, 4.3.2, 4.3.3 y 4.3.4,
según la estructuración que se haya adoptado. El valor de R' se calculará para el periodo fundamental de vibrar de la estructura
en la dirección en que se revisan las distorsiones de acuerdo con 3.3. Las distorsiones no requieren ser multiplicadas por Q
debido a que para este nivel de desempeño se usa Q = 1. Dado que el nivel de desempeño de Ocupación Inmediata hace
referencia al comportamiento de los elementos estructurales, se le considera un estado límite de falla y, en consecuencia, se
deben considerar los factores de carga prescritos por las NTC-Criterios durante el análisis.

  Para el cumplimiento del nivel de desempeño de Limitación de Daño No Estructural, se revisará que las distorsiones
obtenidas con el espectro elástico sin reducir que corresponda a la intensidad sísmica de interés, establecido de acuerdo con
el capítulo 3, no excedan 0.002, salvo que todos los elementos no estructurales sean capaces de soportar deformaciones
apreciables o estén separados de la estructura principal de manera que no sufran daños por sus deformaciones. En tal caso, el
límite en cuestión será 0.004. Al calcular las distorsiones mencionadas en este párrafo pueden descontarse las debidas a la
flexión de conjunto de la estructura. Dado que el nivel de desempeño de Limitación de Daño No Estructural hace referencia
exclusiva al desempeño de los elementos no estructurales, se le considera un estado límite de servicio y, en consecuencia, no
se deben considerar factores de carga durante el análisis.

  Cuando se use un método de análisis dinámico paso a paso, la revisión de las distorsiones de entrepiso se hará como se
especifica en 7.4.4.

  Los desplazamientos laterales y las distorsiones para la intensidad sísmica base de diseño se emplearán para revisar los
requisitos de separación de edificios colindantes de 1.8.

                      Comentario:
                      En ediciones de esta Norma anteriores a 2017, la revisión de los desplazamientos laterales de entrepiso tenía
                      solamente la función de cumplir el requisito de que ante sismos frecuentes no se presentaran daños en elementos
                      no estructurales. En esta edición se dan criterios para revisar tres niveles de desempeño: Seguridad de Vida,
NORMA TÉCNICA COMPLEMENTARIA PARA EL DISEÑO POR SISMO                                                                                27



                     Ocupación Inmediata y Limitación de Daño No Estructural. Para los tres niveles de desempeño se revisa la
                     distorsión máxima de entrepiso. El primero tiene el objetivo de que la distorsión de ningún entrepiso exceda la
                     capacidad de deformación lateral del entrepiso para la que el daño es reparable y no pone en riesgo la integridad
                     física de los ocupantes del edificio. La capacidad de distorsión de entrepiso debe tomar en cuenta tanto la parte de
                     comportamiento lineal como la no lineal del mismo; o sea que depende de la ductilidad del sistema estructural. Por
                     ello los resultados del análisis de la estructura para el nivel de desempeño de Seguridad de Vida se deben
                     multiplicar por Q y por R', dado que este análisis supone un comportamiento lineal hasta la deformación de
```


## 2.4 Efectos de segundo orden (ecuacion 2.4.1, pag. 32)

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 1752-1780 del texto extraido.

```text
2.4      Efectos de segundo orden

  Deben tenerse en cuenta explícitamente en el análisis los efectos geométricos de segundo orden; esto es, los momentos,
fuerzas axiales y cortantes adicionales provocadas por las cargas verticales al obrar en la estructura desplazada lateralmente.
Estos efectos pueden despreciarse en los entrepisos en que la distorsión establecida para la revisión de acuerdo con 1.7 no
exceda la cantidad siguiente:
                                                                Vi
                                                           0.08                                                        (2.4.1)
                                                                Wpi

donde Vi es la fuerza cortante de diseño calculada en el i-ésimo entrepiso para la revisión del nivel de desempeño de interés y
Wpi el peso de la parte de la construcción situada encima de ese entrepiso, sin factor de carga.

                     Comentario:
                     Esta Norma usa la distorsión máxima para establecer cuándo deben considerarse los efectos geométricos de
                     segundo orden en el análisis estructural. El requerimiento actual es similar al que se establecía en ediciones
                     anteriores de la Norma, con la excepción de que ahora se establece explícitamente que el peso de la parte de la
                     construcción situada encima del entrepiso no debe considerar el factor de carga. En congruencia, estándares de
                     diseño sísmico, como el ASCE/SEI 7-22, indican que, durante el cálculo del coeficiente de estabilidad usado para
                     establecer la necesidad de considerar los efectos de segundo orden, el peso no debe considerar factores de carga
                     mayores que uno. Lo anterior debido a que la fuerza cortante de diseño calculada para el entrepiso ya considera
                     un factor de carga. En términos generales, la ecuación 2.4.1 se estableció con el fin de que el incremento en las
                     fuerzas internas producto de los efectos de segundo orden no exceda en más de 10 por ciento el valor de las fuerzas
                     internas estimadas sin tomar en cuenta dichos efectos.

2.5      Efectos bidireccionales

  Para el método estático o el dinámico modal espectral, los efectos de los dos componentes horizontales del movimiento del
terreno se deben combinar, tomando, en cada dirección en que se analice la estructura, 100 por ciento de los efectos del
```


## 3.1 Tabla 3.1.1 y ecuacion 3.1.1 (factor Ks)

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 1945-1985 del texto extraido.

```text
3.1         Espectros de diseño para el análisis dinámico modal y análisis estático

3.1.1       Espectros obtenidos del sistema de acciones sísmicas de diseño

  Cuando se emplee el método de análisis dinámico modal espectral definido en 7.2, las acciones sísmicas de diseño se
determinarán a partir de los espectros de diseño contenidos en el Sistema de Acciones Sísmicas de Diseño, denominado SASID,
para la ubicación específica del predio en estudio. La dirección de internet en la que se accede al SASID es
https://sasid.unam.mx/webNormasCDMX/. Se encuentran en esa base de datos para el sitio de la construcción y las
intensidades sísmicas base de diseño e infrecuente:

        •         Los espectros elásticos de seudo-aceleración y desplazamiento de peligro uniforme.
        •         Los espectros elásticos normativos, sin reducción, de seudo-aceleración y desplazamiento.
        •         El correspondiente espectro de diseño de seudo-aceleración afectado, en su caso, por los factores de reducción
                  por comportamiento sísmico, Q', y por sobre-resistencia, R', correspondientes al nivel de desempeño de
                  Seguridad de Vida.

  Cuando se emplee el método de análisis estático, las acciones de diseño correspondientes se obtendrán como se indica en el
capítulo 6, para lo cual los parámetros necesarios se obtendrán, para la intensidad sísmica de interés, del SASID.

  Para establecer las ordenadas espectrales para la intensidad sísmica frecuente para cualquier combinación de Q y R', se
establecen primero las correspondientes a la intensidad sísmica base de diseño, y se multiplican por el factor Ks, que se
determina como:

                                                                   1                          Zona A
                                                                 ⎧ �6
                                                                 ⎪
                                                                 ⎪
                                                             Ks = 1�[6-4(T -0.5)]             Zona B                                         (3.1.1)
                                                                 ⎨        s
                                                                 ⎪
                                                                 ⎪
                                                                   1                          Zona C
                                                                 ⎩ �4

 La tabla 3.1.1 resume como se establecen los espectros normativos para cada objetivo de diseño. Los valores de Q' y R' que
deben usarse para los diferentes casos se establecen de acuerdo con 3.2 y 3.3.

      Tabla 3.1.1 Determinación de espectros de diseño para los objetivos de diseño contemplados por esta Norma [1]
                                                                                Niveles de Desempeño
      Intensidad
                               No Estructural                                                  Estructural
```


## 3.2 Factor Q-prima y ecuacion 3.2.1

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 2256-2290 del texto extraido.

```text
3.2      Factores de reducción de las ordenadas espectrales

  Para el nivel de desempeño que corresponda, las ordenadas espectrales correspondientes al espectro elástico de seudo-
aceleración pueden dividirse con fines de diseño entre el factor de reducción por sobre-resistencia R' establecido de acuerdo
con 3.3, y el factor de reducción por comportamiento sísmico, Q', que se calcula como:
NORMA TÉCNICA COMPLEMENTARIA PARA EL DISEÑO POR SISMO                                                                                41




                                               ⎧             1T
                                                           �
                                               ⎪ 1+ (Q - 1) k Ta ;                 Si T ≤ Ta
                                               ⎪
                                               ⎪
                                          Q′ =              1                                                                   (3.2.1)
                                               ⎨1+ (Q - 1)� ;                Si Ta < T ≤ Tb
                                                            k
                                               ⎪
                                               ⎪            p
                                               ⎪
                                                 1+ (Q - 1)� ;                     Si T > Tb
                                               ⎩            k

donde Q es el factor de comportamiento sísmico. Mientras que para el nivel de desempeño de Ocupación Inmediata se deberá
considerar que Q = 1, para Seguridad de Vida se debe adoptar el valor que se especifica en las tablas 4.3.1, 4.3.2, 4.3.3 y 4.3.4
según la estructuración que se haya adoptado. Los valores de los parámetros k, Ta y Tb los proporciona el SASID para el valor
del amortiguamiento definido por el usuario y el parámetro p se calcula con la ecuación 3.1.2b.

                      Comentario:
                      Esta Norma prevé dos factores de reducción separados. El primero toma en cuenta la reducción en fuerzas por
                      efecto del comportamiento dúctil.
                      Para el nivel de desempeño de Seguridad de Vida, esta Norma acepta que la estructura exhiba comportamiento no
                      lineal. Esto permite limitar las demandas de fuerza en los elementos estructurales y, por lo tanto, utilizar
                      resistencias de diseño menores, a cambio de que se presenten demandas de ductilidad limitadas y cierto nivel de
```


## 3.3 Factor de sobre-resistencia R (3.3.1a, 3.3.1b) y R-prima (3.3.2a, 3.3.2b)

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 2332-2385 del texto extraido.

```text
3.3      Factor de sobre-resistencia

 El factor de sobre-resistencia total, R, debe determinarse para la dirección de interés con la ecuación siguiente:

                                                          R=k1 R0 + k2                                                      (3.3.1a)

donde R0 es un factor básico de sobre-resistencia del sistema estructural, que se tomará igual a:

 2.0      para estructuras de mampostería, y para sistemas estructurales de concreto, acero o compuestos que cumplen con
          los requisitos para adoptar un factor de comportamiento Q de 3 o mayor para el nivel de desempeño de Seguridad
          de Vida, según las reglas establecidas en el capítulo 4.

 1.75     para estructuras de madera, y para sistemas estructurales de concreto, acero o compuestos a los que se asigna Q
          menor que 3 para el nivel de desempeño de Seguridad de Vida, según las reglas establecidas en el capítulo 4.

 k1, factor de corrección por hiperestaticidad, que es igual a:

 0.8      para sistemas estructurales de concreto, acero o compuestos, incluidos los sistemas estructurales duales
          contemplados en las tablas 4.3.1 y 4.3.2, que tengan menos de tres crujías resistentes en al menos una dirección
          de análisis.

 1.0      para sistemas estructurales de concreto, acero o compuestos que tengan tres o más crujías resistentes a sismo en
          las dos direcciones de análisis, para estructuras de mampostería, y para estructuras de madera.

 1.25     para los sistemas estructurales duales incluidos en las tablas 4.3.1 y 4.3.2 que tengan tres o más crujías resistentes
          a sismo en las dos direcciones de análisis.

 k2, factor de incremento para estructuras pequeñas y rígidas, que se obtiene con la expresión:

                                                                         1
                                                                   T 2
                                                    k2 = 0.5 �1 - � � � > 0                                                 (3.3.1b)
                                                                   Ta

  Se usará R = 1 para el diseño de estructuras cuya resistencia a fuerzas laterales quede suministrada, parcial o totalmente, por
elementos o materiales diferentes de los especificados en las tablas 4.3.1, 4.3.2, 4.3.3 y 4.3.4.
NORMA TÉCNICA COMPLEMENTARIA PARA EL DISEÑO POR SISMO                                                                                  43



  Podrán emplearse valores más altos de R cuando se haga un estudio que demuestre, a satisfacción del Instituto y conforme
a 1.2.1 y 6.5, que esto es adecuado.

 El factor de reducción por sobre-resistencia, R', que debe usarse para establecer las acciones de diseño para el nivel de
desempeño de Seguridad de Vida debe determinarse como:

                                                               𝑹𝑹′ = R                                                           (3.3.2a)

 Para el nivel de desempeño de Ocupación Inmediata, R' debe determinarse como:

                                                             𝑹𝑹′ = 0.75R                                                         (3.3.2b)

                    Comentario:
                    El segundo factor reductivo, R', toma en cuenta explícitamente la sobre-resistencia estructural, que se define como
```


## 4.3.2 Tabla 4.3.2 (acero y compuestas), inicio

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 2884-2930 del texto extraido.

```text
4.3.2     Estructuras compuestas

 Los factores de comportamiento sísmico y las distorsiones límite para estructuras de acero y compuestas se presentan en la tabla 4.3.2.

                         Tabla 4.3.2 Factores de comportamiento sísmico y distorsiones límite para estructuras de acero y compuestas [1]
                    Estructuración               Ductilidad                             Condición                                 Q         γSV     γOI
                                                   Alta       -----                                                              4.0       0.030   0.0075
                                                   Media      -----                                                              3.0       0.020   0.0075
                                                   Baja       -----                                                              2.0       0.015   0.0075
        i) Marcos
                                                   Media      Vigas de alma abierta (armaduras) de ductilidad media              3.0       0.020   0.0075
                                                   Baja       Vigas de alma abierta (armaduras) de ductilidad baja               2.0       0.015   0.0075
                                                   Baja       Conexiones semirrígidas                                            2.0       0.015   0.0075
                                                   Alta       Contraventeos excéntricos                                          4.0       0.020   0.0050
        ii) Sistema dual [a], [b] formado por      Media      Contraventeos concéntricos de ductilidad alta [5]                  3.0       0.015   0.0050
        marcos de acero y contraventeos de
                                                   Baja       Contraventeos concéntricos de ductilidad media [5]                 2.0       0.010   0.0050
        acero [2], [3], [4]
                                                   Baja       Contraventeos concéntricos que trabajan solo en tensión            1.0       0.005   0.0030
                                                   Alta       Muros de placa de acero rellena de concreto de ductilidad alta     4.0       0.020   0.0050
        iii) Sistema dual [a], [b] formado por                                                                                                     0.0050
                                                   Alta       Muros compuestos de ductilidad alta                                4.0       0.020
        marcos de acero y muros [2], [4]
                                                   Alta       Muros de placa de acero de ductilidad alta                         4.0       0.020   0.0050
                                                   Alta       -----                                                              4.0       0.030   0.0075
                                                   Media      -----                                                              3.0       0.020   0.0075
                                                   Media      Vigas de alma abierta (armaduras) de ductilidad alta               3.0       0.020   0.0075
        iv) Marcos compuestos
                                                   Media      Conexiones semirrígidas compuestas de ductilidad media             3.0       0.020   0.0075
                                                   Baja       Vigas de alma abierta (armaduras) de ductilidad baja               2.0       0.015   0.0075
                                                   Baja       Marcos de ductilidad baja                                          2.0       0.015   0.0075
        v) Sistema dual [a], [b] formado por       Alta       Contraventeos excéntricos                                          4.0       0.020   0.0050
        marcos compuestos y contraventeos          Media      Contraventeos concéntricos de ductilidad alta [5]                  3.0       0.015   0.0050
        de acero [2], [3], [4]                     Baja       Contraventeos concéntricos de ductilidad media [5]                 2.0       0.010   0.0050
NORMA TÉCNICA COMPLEMENTARIA PARA EL DISEÑO POR SISMO                                                                                                          54
                 Tabla 4.3.2 Factores de comportamiento sísmico y distorsiones límite para estructuras de acero y compuestas [1] (continuación)
                      Estructuración                         Ductilidad                                            Condición                                               Q          γSV            γOI
                                                                 Alta           Muros de placa de acero rellena de concreto de ductilidad alta                            4.0        0.020          0.0050
                                                                 Alta           Muros compuestos de ductilidad alta                                                       4.0        0.020          0.0050
        vi) Sistema dual [a], [b] formado por                    Alta           Muros de placa de acero de ductilidad alta                                                4.0        0.020          0.0050
        marcos compuestos y muros [2], [4]                       Alta           Muros de concreto reforzado de ductilidad alta                                            4.0        0.020          0.0050
                                                                 Media          Muros de concreto reforzado de ductilidad media                                           3.0        0.015          0.0050
                                                                 Baja           Muros de concreto reforzado de ductilidad baja                                            2.0        0.010          0.0050
        vii) Columnas de acero compactas en
        voladizo, sin o con relleno de                            Baja          Columnas de ductilidad baja                                                               1.5        0.009          0.0075
        concreto
        viii) Sistema suspendido soportado
```


## 6.2 Requisitos de aplicacion del metodo estatico

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 4003-4010 del texto extraido.

```text
6.2      Requisitos de aplicación

  Puede utilizarse el método estático de análisis para estructuras regulares de altura no mayor que 30 m, y estructuras
irregulares de no más de 20 m de altura. Para edificios ubicados en la Zona A, los límites anteriores se amplían a 40 m y 30
m, respectivamente. El método estático de análisis no podrá usarse para estructuras que pertenezcan al Grupo A o que sean
fuertemente irregulares según 2.2.

                     Comentario:
```


## 6.3 Fuerzas laterales de diseno (ecuacion 6.3.1)

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 4022-4046 del texto extraido.

```text
6.3      Determinación de las fuerzas laterales de diseño

  Para calcular las fuerzas cortantes en los entrepisos de una estructura, se supondrá un conjunto de fuerzas horizontales
actuando sobre cada uno de los puntos donde se supongan concentradas las masas de los pisos. Cada una de estas fuerzas se
tomará igual al peso de la masa que corresponde, multiplicado por un coeficiente proporcional a hi, siendo hi la altura de la
masa en cuestión sobre la base de la estructura. Para establecer las fuerzas sísmicas de diseño, el coeficiente se tomará de tal
manera que la relación Vo/Wo sea igual a c/(Q'R'), donde c es un coeficiente que se consigna en 3.1.2, y Q' y R' son factores
de reducción que se establecen, para el nivel de desempeño de interés, de acuerdo con 3.2 y 3.3. De acuerdo con este requisito,
la fuerza lateral que actúa en el i-ésimo nivel, Fi, se determina como:

                                                               c            ∑ Wi
                                                       Fi =          Wi hi                                                       (6.3.1)
                                                              Q'𝑹𝑹 ′       ∑ Wi hi

donde Wi es el peso de la i-ésima masa; hi, la altura de la i-ésima masa sobre el desplante; y Q', el factor de reducción por
comportamiento sísmico definido en 3.2. Para estimar las fuerzas laterales con la ecuación 6.3.1, el valor de Q' debe evaluarse
con la ecuación 3.2.1 para el caso en que T este comprendido en el intervalo que va de Ta a Tb. El coeficiente c se obtendrá
del SASID. Las sumas deben llevarse a cabo sobre todos los niveles del sistema estructural.

                     Comentario:
                     La ecuación 6.3.1 resulta de la suposición de que la aceleración efectiva varía en forma lineal con la altura del
                     nivel de interés con respecto al nivel de desplante.
NORMA TÉCNICA COMPLEMENTARIA PARA EL DISEÑO POR SISMO                                                                            75


```


## 6.4 Periodo aproximado (ecuacion 6.4.1)

Origen: NTC Diseno por Sismo 2023 (sismo.txt), lineas 4048-4075 del texto extraido.

```text
6.4      Reducción de las fuerzas laterales en función del período fundamental

  Para establecer las fuerzas sísmicas de diseño, podrán adoptarse fuerzas laterales menores que las calculadas con la ecuación
6.3.1, siempre que se tome en cuenta el valor aproximado del periodo fundamental de vibrar de la estructura, T, de acuerdo
con lo siguiente:

                                                                      ∑ W X2
                                                          T = 2π� ∑ i i                                                     (6.4.1)
                                                                     g     Fi Xi


donde Xi es el desplazamiento del i-ésimo nivel, relativo al desplante en la dirección de la fuerza, g la aceleración de la
gravedad, y las sumatorias se llevan a cabo sobre todos los niveles.

  Si T es menor o igual que Tb, se procederá como en 6.3, pero de tal manera que la relación Vo/Wo sea igual a Sa (T, Q=1)/Q'R',
calculándose Sa (T, Q = 1) como se indica en 3.1.2, y Q' y R' como se especifica en 3.2 y 3.3.

 Si T es mayor que Tb, cada una de las fuerzas laterales se tomará igual a:

                                                                           Sa (T, Q=1)
                                                 Fi =Wi (k3 hi +k4 h2i )                                                  (6.4.2.a)
                                                                               𝑸𝑸′ 𝑹𝑹′

donde:

                                                                     ∑ Wi
                                                           k3 = p                                                         (6.4.2.b)
                                                                    ∑ Wi hi
```


# NTC Criterios y Acciones CDMX (compilacion cargada por el proyecto)


## 4.1.1 Desplazamientos (a: flecha vertical, b: desplazamiento horizontal relativo h/500 o h/250)

Origen: NTC Criterios y Acciones (ca.txt), lineas 323-345 del texto extraido.

```text
  4.1.1 En las edificaciones comunes sujetas a acciones permanentes o variables, la condición del estado límite de servicio en
términos de desplazamientos se cumplirá si se satisfacen las condiciones a) y b) siguientes:

    a) Los límites de desplazamiento vertical en el centro de vigas y en losas, en el que se incluyen efectos a largo plazo,
       establecidos en las Normas del material que corresponda al sistema de piso o techo y que dependen de la posible
       afectación a elementos no estructurales
    b) Un desplazamiento horizontal relativo entre dos niveles sucesivos de la estructura que no exceda al calculado como
       la altura del entrepiso dividido entre 500, para edificaciones en las cuales se hayan unido los elementos no
       estructurales capaces de sufrir daños bajo pequeños desplazamientos; en otros casos, el límite será igual a la altura
       del entrepiso dividido entre 250. Para diseño sísmico o por viento se observará lo dispuesto en las Normas
       correspondientes.

4.2 Vibraciones

  4.2.1 Las amplitudes tolerables de los desplazamientos debidos a vibraciones no podrán exceder los valores establecidos en
4.1. Además, deberán imponerse límites a las amplitudes máximas de las vibraciones, de acuerdo con su frecuencia, de manera
de evitar condiciones que afecten seriamente la comodidad de los ocupantes o que puedan causar daños a equipo sensible a
las excitaciones citadas. En la NTC-Acero, la NTC-Concreto y la NTC-Mampostería se establecen criterios particulares para
los sistemas de piso de concreto y compuestos.

4.3 Otros estados límite

  4.3.1 Además de lo estipulado en 4.1 y 4.2, se observará lo que dispongan las Normas relativas a los distintos tipos de
```


# NTC Diseno y Construccion de Estructuras de Acero CDMX 2020


## 2.3.2 Relaciones de esbeltez maximas (KL/r <= 200)

Origen: NTC-Acero (norma.txt), lineas 2312-2335 del texto extraido.

```text
2.3.2 Relaciones de esbeltez máximas

La relación de esbeltez K L/r de miembros en compresión no debe ser mayor que 200.

           Comentario:
           Los elementos estructurales con relaciones de esbeltez mayores a 100, para elementos en
           compresión, son muy poco eficientes, esto es, se requiere de mucha área para obtener
           resistencias bajas, por lo que no es recomendable.

La relación de esbeltez L/r de miembros en tensión puede tener cualquier valor, pero conviene que no pase de 240 en
miembros principales, ni de 300 en contraventeos y miembros secundarios, especialmente cuando estén sometidos a cargas
que puedan ocasionar vibraciones.

Si el miembro en tensión es una varilla, no se pone límite a su relación de esbeltez, pero se recomienda pretensarlo para
evitar vibraciones o deformaciones y desplazamientos excesivos.

           Comentario:
           Es importante garantizar que los elementos en tensión con esbelteces grandes (mayores a 200)
           queden permanentemente pretensados, dado que de lo contrario no cumplirían con la función
           para la cual fueron diseñados.
42                                       GACETA OFICIAL DE LA CIUDAD DE MÉXICO                               7 de julio de 2020



```


## Tabla 3.2.1 Valores maximos de la relacion ancho/grueso (compresion)

Origen: NTC-Acero (norma.txt), lineas 3247-3275 del texto extraido.

```text
                                       Tabla 3.2.1 Valores máximos de las relaciones ancho/grueso.
                                      Elementos que forman parte de miembros en compresión pura.

                                                                        λr (1)
                      Descripción del elemento               λ        Sección                            Ejemplos
                                                                    tipo 1, 2 o 3
                  Patines de secciones I o H
 Elementos no
  atiesados (3)




                  laminadas, placas que sobresalen de       b/t
                  esas secciones, alas exteriores de                         E
                                                             o        0.56
                  pares de ángulos conectados                                Fy
                  continuamente, patines de canales y      b / tp
                  de tés
      58                                                            GACETA OFICIAL DE LA CIUDAD DE MÉXICO                         7 de julio de 2020




                                                                                                           (2)
                                   Patines de secciones I o H formadas            b/t
                                   por placas soldadas, placas o alas de
                                                                                    o                kc E
                                   ángulos que sobresalen de ellas,                         0.64
```


## Tabla 3.2.2 Valores maximos de la relacion ancho/grueso (flexion)

Origen: NTC-Acero (norma.txt), lineas 3327-3355 del texto extraido.

```text
                                                        Tabla 3.2.2 Valores máximos de las relaciones ancho/grueso.
                                             Elementos comprimidos que forman parte de miembros en flexión o flexocompresión.

                                    Descripción del                      λpl                     λp                    λr
                                                          λ                                                                       Ejemplos
                                       elemento                    Sección tipo 1          Sección tipo 2        Sección tipo 3
no atiesados




                                   Patines de
 Elementos




                                   secciones                                 E                        E                    E
                                                        b / tp        0.30                    0.38                  1.00
                  (c)




                                   laminadas I, H,                           Fy                       Fy                   Fy
                                   canales y tés
   7 de julio de 2020                                   GACETA OFICIAL DE LA CIUDAD DE MÉXICO                                  59


```


## 4.4 Relaciones de esbeltez (en tension no hay limite obligatorio; 300 es recomendacion)

Origen: NTC-Acero (norma.txt), lineas 3746-3765 del texto extraido.

```text
4.4 Relaciones de esbeltez

           Comentario:
           El límite propuesto (kL/r<300) se basa en el juicio profesional y las consideraciones prácticas de
           economía, facilidad de manejo y cuidados necesarios para minimizar el daño accidental durante
           la fabricación, el transporte y la construcción. Este límite de esbeltez no es esencial para la
           integridad estructural de los miembros a tensión; simplemente asegura un grado de rigidez tal
           que sea improbable un movimiento lateral indeseable como vibración. La falta de rectitud
           dentro de tolerancias razonables no afecta la capacidad de un elemento para resistir fuerzas en
           tensión. En los casos donde hay imperfecciones; éstas tienden a disminuir ante cargas en tensión
           y tienden a incrementarse ante cargas en compresión.

Las relaciones de esbeltez de miembros en tensión pueden tener cualquier valor, sin límite superior.
66                                        GACETA OFICIAL DE LA CIUDAD DE MÉXICO                          7 de julio de 2020




            Nota: Se recomienda que la relación de esbeltez no exceda de 300 (inciso 2.3.1). Este límite no es
            aplicable a varillas, cables y tirantes en tensión.
```


## 11.4 Deflexiones (cuerpo; remite a las NTC de Criterios y Acciones)

Origen: NTC-Acero (norma.txt), lineas 11497-11522 del texto extraido.

```text
11.4 Deflexiones

Las deflexiones verticales de elementos estructurales y sus combinaciones, incluyendo pisos, techos, muros divisorios y
fachadas, producidas por cargas nominales, no deben exceder los valores máximos permisibles indicados en las Normas
Técnicas Complementarias sobre Criterios y Acciones para el Diseño Estructural de las Edificaciones.

           Nota: Las deflexiones verticales y los desalineamientos excesivos se deben principalmente a tres
           factores: (1) cargas gravitacionales muertas y vivas (2) efectos de temperatura y hundimientos
           diferenciales y (3) tolerancias de construcción y errores. Pueden ser inconvenientes visualmente
           ocasionar separaciones grietas o permitir el paso del agua de recubrimientos exteriores y causar daños
           a componentes interiores y acabados.
           En algunos sistemas de piso de claros grandes puede requerirse un límite de la deflexión máxima,
           independiente del claro, para minimizar la posibilidad de dañar elementos no estructurales adyacentes.

           Comentario:
           Las deflexiones verticales y rotaciones excesivas se desarrollan principalmente por: (1) las
           cargas de gravedad; (2) los efectos de temperatura, fluencia y asentamiento diferencial, y (3) las
           tolerancias y los errores de construcción. Dichas deformaciones pueden ser visualmente
           discutibles, causar separación, agrietamiento o daño en revestimientos, acabados y en
           componentes.

           Los límites de deflexión dependen en gran medida de la función de la estructura y la naturaleza
           de la construcción compatible. Los límites tradicionales expresados como una fracción de la
           longitud del tramo no deben extrapolarse más allá de la experiencia. El control apropiado de las
           deflexiones es un tema complejo que requiere de la cuidadosa aplicación de un criterio
198                                    GACETA OFICIAL DE LA CIUDAD DE MÉXICO                               7 de julio de 2020
```


# AISC 360-22 (texto aisc-360-22-16thedition)


## L2 Deflections (especificacion)

Origen: AISC 360-22 (aisc.txt), lineas 12347-12352 del texto extraido.

```text
L2.    DEFLECTIONS
       Deflections in structural members and structural systems shall be limited so as not to
       impair the serviceability of the structure.

L3.    DRIFT
       Drift shall be limited so as not to impair the serviceability of the structure.
```


## Comentario L2: 1/300 visible; limites tradicionales 1/360 y 1/240 (pag. 16.1-543)

Origen: AISC 360-22 (aisc.txt), lineas 29734-29765 del texto extraido.

```text
L2.   DEFLECTIONS
      Excessive vertical deflections and misalignment arise primarily from three sources:
      (a) gravity loads, such as dead, live, and snow loads; (b) effects of temperature,
      creep, and differential settlement; and (c) construction tolerances and errors. Such
      deformations may be visually objectionable; cause separation, cracking, or leak-
      age of exterior cladding, doors, windows, and seals; and cause damage to interior
      components and finishes. Appropriate limiting values of deformations depend
      on the type of structure, detailing, and intended use (Galambos and Ellingwood,
      1986). Historically, common deflection limits for horizontal members have been
      1/360 of the span for floors subjected to reduced live load and 1/240 of the span for
      roof members. Deflections of about 1/300 of the span (for cantilevers, 1/150 of the
      length) are visible and may lead to general architectural damage or cladding leak-
      age. Deflections greater than 1/200 of the span may impair operation of moveable
      components such as doors, windows, and sliding partitions.
      Deflection limits depend very much on the function of the structure and the nature
      of the supported construction. Traditional limits expressed as a fraction of the span
      length should not be extrapolated beyond experience. For example, the traditional
      limit of 1/360 of the span worked well for controlling cracks in plaster ceilings with
      spans common in the first half of the twentieth century. Many structures with more
      flexibility have performed satisfactorily with the now common, and more forgiv-
      ing, ceiling systems. On the other hand, with the advent of longer structural spans,
      serviceability problems have been observed with flexible grid ceilings where actual
      deflections were far less than 1/360 of the span, because the distance between parti-
      tions or other elements that may interfere with ceiling deflection are far less than
      the span of the structural member. Proper control of deflections is a complex sub-
      ject requiring careful application of professional judgment. AISC Design Guide 3,
      Serviceability Design Considerations for Steel Buildings, 2nd Edition (West et al.,
      2003), provides an extensive discussion of the issues.

                       Specification for Structural Steel Buildings, August 1, 2022
                        American Institute of Steel Construction
16.1-544                                     DEFLECTIONS                                [Comm. L2.
```


## Simbolo Kz: factor de longitud efectiva para pandeo torsional (E4)

Origen: AISC 360-22 (aisc.txt), lineas 1729-1729 del texto extraido.

```text
Kz           Effective length factor for torsional buckling about the longitudinal axis . . E4
```


## E4: no se requiere pandeo flexotorsional con b/t <= 0.71 sqrt(E/Fy)

Origen: AISC 360-22 (aisc.txt), lineas 5465-5465 del texto extraido.

```text
        E4. Flexural-torsional buckling need not be considered when b t ≤ 0.71 E Fy .
```
