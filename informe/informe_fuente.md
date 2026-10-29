
Resumen

Se estudia si la ausencia de conexión doméstica y un ratio contextual alto de alumnos por docente coinciden con mayor desfase de edad y grado. Se integraron 19,286 estudiantes de 6 a 17 años del corte 2025 del panel ENAHO con servicios educativos activos de ESCALE por distrito y área. Se compararon K-Means y mezclas gaussianas, y regresión logística frente a tres ensambles con validación por conglomerado. El XGBoost seleccionado obtuvo ROC-AUC 0.540, AP 0.416 y F1 macro 0.522 en test. La celda de doble desventaja contiene 24 casos y una tasa de desfase de 58,3 %, con gran incertidumbre. El contraste aditivo incluye cero en su intervalo bootstrap. Los resultados no confirman una acumulación generalizable y no justifican decisiones individuales. SHAP describe asociaciones del modelo, sin interpretación causal.

Palabras clave  brecha digital, contexto docente, desfase edad grado, validación agrupada, perfiles de recursos, SHAP.


1 Introducción y pregunta de investigación

Las condiciones tecnológicas del hogar y los recursos educativos del territorio pueden coincidir sin ser equivalentes. Un distrito con más alumnos por docente no identifica la escuela concreta del estudiante ni mide su tamaño de aula. Por ello, el análisis distingue exposición contextual, clasificación individual y descripción de perfiles.

La pregunta es si la coexistencia de ausencia de conexión doméstica y ratio docente alto presenta una asociación adicional con el desfase escolar. Se examinan también estudiantes sin desfase dentro de esa combinación. Estos casos se denominan trayectorias acordes a la edad en la medición disponible; no prueban resiliencia psicológica ni identifican sus causas.

El objetivo general es construir un análisis reproducible que contraste esa pregunta mediante integración relacional, clustering de recursos y clasificación explicable. Se anticipa la hipótesis de mayor desfase en la doble desventaja, pero se conserva la posibilidad de resultados negativos o inconclusos.


2 Datos y decisiones metodológicas

Se procesaron las selecciones originales 2025 de los módulos 100, 200, 300 y Sumaria incluidos en los archivos panel 2021–2025 [1]. Se verificó UTF-8 con BOM en estos CSV; no se impuso latin1 solo por la advertencia general de la guía. Las llaves se leyeron como texto, se conservaron sus ceros y se normalizaron espacios. Los hashes SHA-256 registran la procedencia y permiten reconstruir las selecciones desde los ZIP originales.

Son residentes habituales los miembros no ausentes durante 30 días o más, y los no miembros presentes durante al menos 30 días, según P204–P206. Se retienen matriculados en primaria o secundaria con grado válido. La unión 200–300 es uno a uno por CONGLOME, VIVIENDA, HOGAR y CODPERSO; vivienda y Sumaria se vinculan muchos a uno por hogar. No se detectaron duplicados en esas llaves ni pérdidas en los tres cruces para la cohorte final.

ESCALE aporta 54,038 servicios activos B0/F0 [2]. El ratio contextual es la suma de TALUM dividida por la suma de TDOC, sobre servicios con alumnos válidos y docentes positivos, por CODGEO y área. Se calcula también proporción pública y coordenadas medias válidas. Padlocal verifica CODLOCAL; aparece una discrepancia geográfica, que se registra conservando CODGEO del padrón. La cobertura contextual es 98.1%; los 369 estudiantes no vinculados permanecen con faltantes.


2 1 Definición del resultado y las exposiciones

En primaria el grado actual procede de P308C; en secundaria se suma seis al año P308B. La edad normativa aproximada es grado acumulado + 5. El objetivo principal vale uno cuando la edad declarada supera esa edad, conforme a la opción amplia de la guía. No hay fecha de nacimiento usable para reconstruir la edad al 31 de marzo [3]. Se reporta por separado sensibilidad de dos o más años, cercana al umbral de atraso de ESCALE [4]; ambas definiciones no son intercambiables.

P1144 y P1121 son selecciones múltiples: 1 identifica la opción seleccionada y 0 la opción no seleccionada. P314A usa 1 sí y 2 no. Se preservan faltantes. P314D resume frecuencia ordinal, no horas ni competencias. Ingreso y gasto anuales se dividen entre miembros del hogar y 12; se aplica log1p. Los códigos de lengua y pobreza se mantienen como categorías.


2 2 Separación y prevención de fuga

GroupShuffleSplit reserva 3,788 casos de 941 conglomerados para test y 15,498 casos para entrenamiento. Cinco folds GroupKFold, todos disjuntos por CONGLOME, ajustan medianas, escalado, categorías y pesos de balance únicamente dentro de cada train [5]. Edad, grado, normativa, desfase, identificadores, factores y clusters se excluyen de X. Se usa semilla 42 y umbral 0,5.

FACTOR07 se conserva como peso del hogar; no se utiliza como si fuera individual. FACPOB07 se emplea en sensibilidad de evaluación. Ninguno convierte automáticamente el corte del panel en una estimación nacional. Padron y Padlocal suministrados no contienen altitud ni medidas completas de conexión escolar: se declaran ausencias y no se inventan indicadores.


3 Acumulación de desventajas y perfiles

Ratio alto significa ratio contextual mayor o igual a 18.36, percentil 75 calculado en train. No es un estándar de sobrecarga MINEDU. La clasificación 2 × 2 utiliza conexión doméstica y este umbral; el test no fija cortes ni modifica la hipótesis. Las tasas son descriptivas de la muestra y excluyen filas sin ambas exposiciones.

La combinación de ambas desventajas presenta 14 de 24 estudiantes con desfase y 10 sin él. La diferencia de diferencias de las cuatro tasas es 16.0 puntos porcentuales, IC95 % [-4.3; 35.3], con 1 000 réplicas agrupadas. Este intervalo incluye cero. El resultado es compatible con diversas magnitudes y no demuestra sinergia ni protección del acceso a Internet. La celda pequeña obliga a evitar recomendaciones dirigidas a individuos.


3 1 Clustering de recursos

Se compararon K-Means y GMM para k de 2 a 6, con imputación y escalado ajustados en train. La selección por silueta sobre una muestra fija de 1 800 registros favoreció GMM con k = 6, silueta 0.357, Davies–Bouldin 1.066 y Calinski–Harabasz 538.1. El máximo se alcanza en el límite explorado: seis no se presenta como número óptimo universal.

Los nombres completos describen ruralidad, conexión y ratio, evitando categorías de valor sobre los estudiantes. Se proponen verificaciones territoriales de acceso para perfiles con poca conexión y de acompañamiento para perfiles con conexión pero poco uso. Son hipótesis de intervención, no conclusiones de impacto.


4 Comparación predictiva y análisis de errores

La logística es la línea base y se compara con Random Forest, XGBoost y LightGBM. Se prueban dos configuraciones por familia con los mismos cinco folds; 40 ajustes en total. C se prueba en 0,1 y 1; mínimo de hoja en 5 y 20; profundidad en 2 y 4; hojas LightGBM en 7 y 15. La mayor AP media de validación elige familia y parámetros. El test se consulta después de cerrar esa selección.

XGBoost alcanza AUC 0.540, IC95 % [0.516; 0.563]. AP se calcula como average precision, no como área trapezoidal. La referencia de AP es la prevalencia test 0.386; la mejora es pequeña. Se entregan todas las corridas para evitar presentar solo el mejor resultado.

Se observan 771 falsos negativos y 987 falsos positivos. Los primeros omiten estudiantes con desfase; los segundos generan alertas innecesarias. El balance de clases no asegura calibración: las probabilidades se concentran cerca de 0,5. El Brier de 0,248 supera el de predecir siempre la prevalencia test, aproximadamente 0,237; este último es una referencia descriptiva calculada a posteriori, no un modelo seleccionado.

La separación adicional por distrito obtiene AUC 0.527. Con FACPOB07, AUC 0.555. Al redefinir atraso como dos o más años, el mismo tipo de modelo con parámetros fijados obtiene AUC 0.634 y AP 0.107; esa tarea distinta no reemplaza el resultado principal ni rescata su rendimiento.


5 Explicabilidad global y dependencias

Se aplica SHAP al XGBoost ganador [6], usando 80 observaciones de entrenamiento como fondo y 350 de test para explicación. Las contribuciones se expresan en margen del modelo, no en puntos porcentuales de probabilidad. El error máximo de reconstrucción de la salida es menor que 0,000001. Las variables mostradas se restituyen a sus unidades originales después del escalado; los logaritmos conservan su escala documentada.

Latitud, proporción pública, frecuencia TIC e ingreso encabezan las contribuciones. El patrón refleja asociaciones dentro de este modelo débil. Que una coordenada sea importante sugiere estructura territorial compartida o variables omitidas; no convierte la localización en causa del desfase. La magnitud SHAP tampoco indica que una intervención sobre esa variable produciría el cambio predicho.

La dependencia de Internet toma dos valores y no representa una curva dosis respuesta. Los colores permiten examinar heterogeneidad por contexto, pero no constituyen valores formales de interacción SHAP. En el ratio, la dispersión vertical indica que otros predictores también intervienen. La escasez de casos sin conexión reduce la estabilidad de los patrones; un contraste visual no reemplaza una prueba de interacción.

La explicación lingüística se interpreta con prudencia: la codificación one hot conserva categorías, pero el tamaño de cada grupo varía. La ausencia de una lengua en las diez variables principales no demuestra ausencia de desigualdad. Tampoco corresponde ordenar grupos étnicos por su contribución al riesgo.


5 1 Dos predicciones individuales

El caso alto tiene clase real 1 y probabilidad 0.623; el bajo tiene clase real 0 y probabilidad 0.372. Son extremos relativos del conjunto explicado, no probabilidades cercanas a certeza ni casos representativos. Las barras descomponen el margen alrededor del valor base. Estos ejemplos ilustran el funcionamiento del modelo y no autorizan diagnósticos escolares.


6 Discusión y conclusiones

La hipótesis de acumulación recibe una señal descriptiva positiva en una celda pequeña, pero su contraste agrupado es impreciso e incluye cero. No se confirma una asociación adicional estable. Los diez casos sin desfase bajo doble desventaja abren preguntas sobre acompañamiento, acceso alternativo y trayectoria previa que estos datos no permiten responder; no se atribuyen mecanismos que no fueron medidos.

Los perfiles principales se construyen sin desfase para evitar que la comparación de rezago sea definitoria. Como sensibilidad exigida por las variables sugeridas en la guía, se repite la comparación de ambos algoritmos incluyendo años de desfase. Se entrega la tabla alternativa y su concordancia con los perfiles de recursos; ningún cluster entra en el clasificador. Toda interpretación del perfil alternativo reconoce la participación del resultado en su construcción.

Las limitaciones incluyen corte panel sin equivalencia certificada con la anual, edad declarada sin referencia al 31 de marzo, ratio territorial que no mide carga individual, ausencia de altitud y de detalles completos de equipamiento escolar, y pocos casos en la doble desventaja. La separación por conglomerado reduce fuga por vecindario, pero no garantiza independencia espacial total. SHAP explica el ajuste y no identifica efectos causales.

Se concluye que la integración y la evaluación agrupada son reproducibles, mientras que la predicción disponible es insuficiente para priorizar personas. Se recomienda verificar localmente las barreras identificadas, recolectar trayectoria temporal y nacimiento con referencia escolar, y validar en otra cohorte antes de evaluar intervenciones. Se conserva el resultado negativo de predicción como evidencia, sin añadir edad o grado para inflar métricas.


Referencias

[1] INEI. ENAHO panel 2021–2025. Diccionario de datos, secciones del corte 2025, pp. 588–594 y 657–666. ZIP originales 1041, módulos 1474, 1479, 1475 y 1478. Procedencia y hashes en docs/manifiesto_fuentes.json.

[2] MINEDU ESCALE. Padron.dbf y Padlocal.dbf. Padrón de servicios educativos, actualización 29 de octubre de 2025. Distribución original suministrada para el curso.

[3] MINEDU. Edades normativas. Referencia al 31 de marzo. https://www.gob.pe/institucion/minedu/informes-publicaciones/2742610-edades-normativas

[4] MINEDU ESCALE. Alumnos con atraso escolar. Metadatos del indicador. https://escale.minedu.gob.pe/tendencias-2016-portlet/servlet/tendencias/archivo?idCuadro=14&tipo=meta

[5] scikit-learn. Common pitfalls and recommended practices. https://scikit-learn.org/stable/common_pitfalls

[6] S. Lundberg y S. I. Lee. A Unified Approach to Interpreting Model Predictions. NeurIPS 30, 2017. https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html