# Guía de sustentación

## Explicación inicial

La pregunta del proyecto es si la combinación de falta de conexión en el hogar y un ratio territorial alto de alumnos por docente coincide con mayor desfase escolar. Integro las fuentes por persona y hogar, agrego contexto escolar por distrito y área, descubro perfiles de recursos y comparo clasificadores. La principal conclusión es que los datos no permiten confirmar una acumulación estable ni obtener una buena predicción individual.

## Recorrido sugerido de ocho minutos

1. Pregunta y diferencia del enfoque, un minuto. Dibujar cuatro celdas: conexión sí/no y ratio alto/menor. Explicar que ratio alto es percentil 75 de train, no una norma oficial.
2. Datos e integración, un minuto. Mostrar flujo de población y cardinalidades; justificar el corte del panel y el filtro de residentes habituales.
3. Etiqueta y prevención de fuga, un minuto y medio. Primaria usa P308C; secundaria P308B +6. La normativa es grado acumulado +5. Mostrar la lista de exclusiones y cómo Pipeline se ajusta dentro de cada fold.
4. Clustering, un minuto. Comparar K-Means y GMM. Justificar silueta, Davies–Bouldin y PCA. Recordar que k=6 fue el mejor dentro de 2..6, no el óptimo universal.
5. Modelos y errores, un minuto y medio. Mostrar AP CV y test. La elección se hizo en validación, aunque otro modelo tenga mejor test. AUC 0,540 es bajo; confusión y calibración confirman límites prácticos.
6. Acumulación y explicación, un minuto. Hay 24 casos de doble desventaja en test; 10 sin desfase. El intervalo del contraste incluye cero. Mostrar SHAP global y un caso individual como explicación del modelo, no como causa.
7. Conclusión, un minuto. Proponer validación externa y mejor medición temporal antes de intervenir. Aclarar ausencias de altitud y de datos directos de la escuela de cada persona.

## Preguntas que debes poder responder

**¿Por qué no usar train_test_split?** Porque miembros del mismo conglomerado comparten condiciones. Una separación individual puede repetir vecindarios entre train y test e inflar el rendimiento.

**¿Por qué no incluir edad y grado?** Porque construyen la etiqueta. Incluirlos permitiría reconstruir la respuesta y no evaluar la señal de las condiciones digitales y socioeconómicas.

**¿Un AUC bajo significa que el proyecto está mal?** No necesariamente. Puede indicar poca señal, objetivo aproximado o predictores incompletos. Sí impide afirmar que existe una buena herramienta predictiva. La validez del procedimiento y la utilidad del modelo son cosas diferentes.

**¿Qué significa AP 0,416?** Average precision resume precisión y sensibilidad para distintas fronteras. Debe compararse con la prevalencia test 0,386. La diferencia pequeña indica poca mejora sobre esa referencia.

**¿Por qué no escoger el modelo con mayor AUC de test?** Porque convertiría test en instrumento de selección. La regla fijada es mayor AP media en cinco folds del entrenamiento; el test se reserva para evaluar la selección terminada.

**¿El ratio mide sobrecarga del profesor del alumno?** No. Es razón de sumas de servicios educativos por distrito y área. No conocemos la escuela individual del estudiante ni la distribución de sus aulas.

**¿Los diez estudiantes sin desfase son resilientes?** Solo sabemos que no tienen desfase en esta medición pese a ambas condiciones. No medimos resiliencia ni sus mecanismos.

**¿Hay interacción o causalidad demostrada?** No. El contraste aditivo descriptivo tiene un intervalo que incluye cero. Ni la tabla 2×2 ni SHAP identifican efectos causales.

**¿Por qué no usar FACTOR07 para cada alumno?** Es peso del hogar. Se conserva y se distingue de FACPOB07 poblacional. La sensibilidad ponderada no certifica representatividad nacional del corte panel.

**¿Qué diferencia hay entre desfase y atraso de dos años?** El objetivo principal usa edad declarada mayor que normativa, como aproximación amplia. El indicador de dos años es más estricto y se evalúa por separado. Sin nacimiento no reproducimos exactamente edad al 31 de marzo.

**¿Qué significa una barra SHAP positiva?** Que eleva el margen de ese modelo respecto de su fondo de entrenamiento. No significa que cambiar la variable causaría el mismo cambio en la probabilidad o en la realidad.

## Ejecución que debes practicar

Abrir el notebook y revisar cada celda. Ejecutar `python src/verificar.py`, localizar las 26 pruebas, explicar una cardinalidad, un fold, una curva PR y un waterfall. Leer las limitaciones antes de formular recomendaciones. Revisar las reglas del curso sobre declaración del uso de herramientas de asistencia.
