# Doble desventaja digital y contexto docente

**Jose Guillermo Ticona Lipa** · Inteligencia Artificial · Corte ENAHO–ESCALE 2025

¿La ausencia de conexión doméstica y un ratio territorial alto de alumnos por docente coinciden con mayor desfase de edad y grado? El proyecto contrasta esa pregunta, identifica perfiles de recursos y explica un clasificador de rezago. No asume que una asociación sea causal.

## Entrega

- [Artículo editable en Word](informe/Informe_Jose_Guillermo_Ticona_Lipa.docx).
- [Notebook ejecutado con análisis y figuras](notebooks/01_proyecto_completo.ipynb).
- [Dataset CSV](data/processed/dataset_enaho_escale_2025.csv), [Parquet](data/processed/dataset_enaho_escale_2025.parquet) y [diccionario](data/processed/diccionario_variables.csv).
- [Correspondencia con la rúbrica](docs/MATRIZ_RUBRICA.md) y [guía de sustentación](docs/SUSTENTACION.md).
- Resultados completos de validación, prueba, perfiles, SHAP y auditorías en `resultados/`.

## Resultado principal

La base contiene **19 286 estudiantes**, 4 701 conglomerados y 1 186 distritos. La cobertura del contexto escolar es 98,1 %. El XGBoost seleccionado por AP de validación obtuvo en test ROC-AUC **0,540**, AP **0,416** y F1 macro **0,522**. Su capacidad predictiva es baja; no se presenta como herramienta para decidir sobre estudiantes.

La doble desventaja reúne solo 24 estudiantes de test: 14 presentan desfase y 10 no. El contraste aditivo de cuatro tasas es 16,0 puntos porcentuales, IC95 % de -4,3 a 35,3. **No se confirma una acumulación generalizable**. Los intervalos se calculan mediante remuestreo de conglomerados.

Se comparan K-Means y GMM para 2 a 6 grupos. GMM con seis perfiles obtiene la mayor silueta del rango explorado (0,357); no se afirma un óptimo universal. SHAP incluye gráfico global, dos dependencias y dos casos individuales correctamente clasificados.

## Reproducir

Python 3.12. Crear un entorno virtual en la raíz del proyecto e instalar las versiones verificadas:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python pipeline.py
python src/generar_informe.py
```

Como alternativa, ejecutar de principio a fin `notebooks/01_proyecto_completo.ipynb`. Sus celdas importan las funciones de `src/` y conservan las salidas de una ejecución real. El artículo se genera después de los resultados. Su paginación se verificó en Microsoft Word; otros motores pueden introducir variaciones.

Para comprobar la entrega sin volver a entrenar:

```bash
python src/verificar.py
```

El pipeline ejecuta integración, clasificación, clustering, SHAP, análisis complementarios y contratos de integridad. La semilla es 42. Todas las transformaciones aprendidas se ajustan dentro de cada fold; test no selecciona algoritmos ni hiperparámetros. No se utiliza partición aleatoria individual.

## Procedencia y reconstrucción

`data/raw/` contiene **selecciones de columnas originales 2025**, no las bases procesadas de otros trabajos. Se incluyeron los dos ZIP MINEDU y las selecciones ENAHO para que el proyecto sea ejecutable sin descargar los paneles completos.

Para extraer de nuevo desde los seis ZIP originales, colocarlos en una carpeta y ejecutar:

```bash
python src/extraer_fuentes.py --originales RUTA_A_LA_CARPETA
python pipeline.py
```

Se requieren `1041-Modulo1474.zip`, `1041-Modulo1479.zip`, `1041-Modulo1475.zip`, `1041-Modulo1478.zip`, `00_Padron.zip` y `00_Padlocal.zip`, distribuidos para el curso. `docs/manifiesto_fuentes.json` conserva nombres, hashes, columnas y tamaños de selección. No se incorporan historiales Git, informes, notebooks ni código de otros estudiantes. No se redistribuyen sus nombres o documentos personales.

## Decisiones y límites

- Es un corte 2025 del **panel 2021–2025**; no se certifica equivalencia con toda la ENAHO anual.
- El objetivo principal es edad declarada mayor que grado acumulado + 5. Sin nacimiento usable no reproduce exactamente la referencia al 31 de marzo. Se entrega sensibilidad de dos o más años como objetivo separado.
- P1144 y P1121 son selecciones múltiples 0/1. P314A es sí/no 1/2. Los faltantes no se convierten automáticamente en no.
- El ratio es suma de alumnos / suma de docentes de servicios activos de primaria y secundaria, agregado por distrito y área. No es carga laboral individual ni tamaño de aula.
- Ratio alto es el percentil 75 de train (18,36), no una norma MINEDU.
- Edad, grado, normativa, desfase, identificadores y factores se excluyen de los predictores. Los clusters tampoco entran al clasificador.
- FACTOR07 se conserva como peso de hogar; FACPOB07 se utiliza en sensibilidad. No se calculan totales nacionales del panel.
- No hay altitud ni datos completos de equipos o conexión escolar en los archivos suministrados. Se documentan estas limitaciones.
- SHAP describe el modelo y no identifica efectos de intervenciones. La rareza de la doble desventaja limita la estabilidad de sus tasas.

## Estructura

```text
data/raw/          Selecciones originales y ZIP MINEDU
data/processed/    Maestro, contexto y diccionario
notebooks/         Ejecución documentada
src/               Extracción, integración, análisis y artículo
resultados/        Experimentos, particiones, métricas y figuras
informe/           Artículo Word y texto fuente
docs/              Procedencia, rúbrica y sustentación
```

