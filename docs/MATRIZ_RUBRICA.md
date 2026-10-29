# Correspondencia con la rúbrica

La matriz informa evidencias y límites; no equivale a una nota ni sustituye la evaluación del docente.

| Criterio | Evidencia implementada | Archivo para comprobar |
|---|---|---|
| Ingeniería y prevención de fuga 5 puntos | Llaves texto, normalización de espacios, cardinalidad 1:1 y N:1, cruces de los cuatro módulos, distrito y área, test por conglomerado, cinco folds agrupados, imputación y escalado dentro de cada fold | src/datos.py, src/analisis.py, resultados/particiones.csv y verificacion_integridad.csv |
| Clustering 4 puntos | K-Means y GMM, k=2..6, escalado, silueta, Davies–Bouldin, Calinski–Harabasz, PCA, gráfico de siluetas, tamaños y nombres de perfiles | comparacion_clustering.csv, perfiles_clusters.csv, figuras/seleccion_clusters.png y pca_siluetas.png |
| Clasificación 5 puntos | Logística baseline, Random Forest, XGBoost y LightGBM; dos configuraciones por familia y cinco folds, balance por fold, ROC-AUC, AP, F1 macro, confusión, calibración, sensibilidad geográfica y muestral | experimentos_folds.csv, comparacion_validacion.csv, comparacion_test.csv y resumen_modelos.json |
| SHAP 3 puntos | Global con diez predictores, dos dependencias, waterfall de dos casos correctamente clasificados, fondo exclusivamente train y aditividad comprobada | figuras/shap_*.png, resumen_shap.json, importancia_shap.csv |
| Redacción código y defensa 3 puntos | Artículo editable de seis páginas, repositorio organizado, semilla 42, dependencias, notebook ejecutado y guía de defensa | informe/, README.md, requirements.txt, notebooks/ y docs/SUSTENTACION.md |

## Detalles de la especificación

- Población escolar 6–17 años; residentes habituales y matriculados con nivel/grado válido.
- Módulos 100, 200, 300, Sumaria y ESCALE integrados; ceros preservados.
- UTF-8 con BOM verificado en los CSV concretos. La advertencia latin1 de la guía no describe estos archivos panel; se usa la codificación comprobada.
- Dataset `dataset_enaho_escale_2025` en CSV y Parquet con diccionario de todas sus columnas.
- Se resuelve la opción A de rezago aproximado de edad y grado. No se afirma medir notas, competencias digitales ni pronóstico futuro.
- FACTOR07 se conserva; FACPOB07 sirve como sensibilidad de evaluación sin inferencia nacional.
- Transformaciones aprendidas solo dentro de train de cada fold, no antes de la validación cruzada.
- Edad, nivel/grado, normativa y años de desfase quedan fuera del clasificador.
- Los perfiles principales usan recursos sin resultado para evitar caracterización tautológica. La comparación alternativa que incorpora años de desfase cubre la variable sugerida en la guía y se entrega en `sensibilidad_clustering_con_desfase.csv`; no se usa como predictor.
- El número de grupos se justifica dentro del rango ensayado. Al resultar k=6 en el límite, no se afirma que sea el óptimo global.
- El análisis central 2×2 y el bootstrap agrupado del contraste se reproducen en `src/complementos.py`.
- No se generan UMAP ni modelos adicionales solo para aumentar la cantidad de archivos: PCA y tres modelos avanzados cubren las alternativas requeridas.

## Límites que deben declararse

1. Se suministró ENAHO panel, no la anual completa. Los originales y su condición se documentan.
2. No hay fecha de nacimiento usable para el 31 de marzo. Se explicita la aproximación y se reporta sensibilidad de dos o más años.
3. No hay altitud, ratio por computadora ni conexión escolar completos en Padrón/Padlocal. No se fabrican esas variables.
4. La relación ENAHO–ESCALE es contextual, por distrito y área. No se asigna a cada estudiante una escuela que ENAHO no identifica.
5. El modelo tiene rendimiento bajo y el contraste de acumulación es incierto. No se sustituyen resultados por valores deseados.
6. La defensa oral requiere que el estudiante ejecute y explique el trabajo. La guía de sustentación es material de estudio, no evidencia de una defensa ya realizada.
