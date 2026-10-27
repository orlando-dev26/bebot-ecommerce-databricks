# BeBot: asistente de e-commerce con Databricks

Este proyecto es mi evaluación final del curso de IA Generativa en Databricks de MitoCode. La idea es sencilla: ayudar a una persona a consultar sus pedidos, revisar su perfil y sus beneficios, y resolver dudas sobre las políticas de una tienda desde un mismo chat.

El caso corresponde a **Ecommerse YWAP Store**. Los clientes, productos y pedidos son datos sintéticos del ejercicio; las respuestas sobre políticas se apoyan en los PDFs incluidos en este repositorio. Para construirlo tomé como base el proyecto integrador del profesor y su ejemplo de `ResponsesAgent`, adaptándolos al caso de e-commerce.

## Qué puede hacer

- Consultar el estado y los productos de un pedido.
- Buscar el perfil de un cliente por su correo y obtener su segmento.
- Calcular beneficios de los segmentos Nuevo, Recurrente y VIP.
- Buscar información de envíos y atención de incidencias en los documentos de la tienda.
- Mantener el contexto entre preguntas, pedir los datos que faltan y rechazar solicitudes de credenciales o instrucciones internas.

Por ejemplo, se puede pedir el perfil, proporcionar el correo en el siguiente mensaje y después preguntar qué beneficios corresponden a ese segmento. Las capturas de abajo muestran estas conversaciones reales.

## Cómo funciona

La solución tiene dos partes: preparar la información y usarla desde el agente.

Primero se generan cinco tablas Bronze. El notebook de Medallion limpia esos datos y construye cinco tablas Silver y tres tablas Gold: resumen de clientes, estado de pedidos e inventario con reviews. Las herramientas consultan Gold, no los datos Bronze directamente.

Los PDFs siguen otro camino: se cargan desde un volumen, se dividen en fragmentos de 1000 caracteres con un solapamiento de 150 y se guardan en una tabla Delta. Un índice de Vector Search permite recuperar los fragmentos relacionados con una pregunta. Esa es la parte de RAG: el bot busca información antes de responder sobre las políticas.

El agente usa LangGraph y `ChatDatabricks`, con el endpoint LLM `databricks-meta-llama-3-3-70b-instruct`. Un wrapper de MLflow implementa el contrato `ResponsesAgent`. Finalmente, una App de Streamlit envía la conversación al endpoint del agente y muestra la respuesta.

```text
Datos sintéticos → Bronze → Silver → Gold → herramientas UC ──┐
                                                            ├→ Agente → Model Serving → Chat
PDFs → fragmentos Delta → Vector Search → búsqueda documental ┘
```

### Las tres herramientas de Unity Catalog

| Herramienta | Lenguaje | Para qué se usa |
|---|---|---|
| `consultar_estado_pedido` | SQL | Obtener estado, importe y productos de un pedido por su ID. |
| `consultar_perfil_cliente` | SQL | Obtener el perfil y segmento a partir del correo. |
| `calcular_beneficios_segmento` | Python | Aplicar las reglas de beneficios de cada segmento. |

A estas tres funciones se suma `buscar_politicas_tienda`, que consulta el índice de documentos. El prompt explica cuándo usar cada herramienta y cuándo pedir un identificador en lugar de inventarlo.

## Relación con lo que pidió el profesor

| Requisito | Dónde está resuelto | Estado |
|---|---|---|
| Arquitectura Medallion | `01_Medallion.py`: cinco Silver y tres Gold. | Transformaciones de limpieza y agregación implementadas. |
| RAG sobre documentos del caso | `02_RAG_Ingestion.py` y `pdfs_fuente/`. | Implementado; hay pruebas de respuestas con fuente. |
| Índice de Vector Search | `workspace.reto_ecommerce.indice_documentos_ecommerce`. | Creado y utilizado durante las pruebas. |
| Tres UC Functions, al menos una Python | `03_UC_Tools.py`. | Implementadas y probadas. |
| Agente con contrato ResponsesAgent | `agente_ecommerce_template.py` y notebook 04. | Versión 16 registrada y probada. |
| System prompt | Dentro de la plantilla del agente. | Incluye uso de herramientas, límites y manejo del historial. |
| Evaluación offline con dataset persistido | `05_MLflow_Evaluate.py`. | 34 casos evaluados y versión 16 aprobada. |
| Endpoint desplegado con agents.deploy | `06_Deploy_Endpoint.py`. | Despliegue confirmado con 100 % del tráfico a la versión 16. |
| Databricks App | `App_Web/`. | Chat probado con intercambios reales. |
| README con explicación, orden y evidencias | Este documento. | Código, capturas y resultados incluidos. |

Los scorers online y la Review App eran opcionales en el enunciado.

## Archivos y orden de ejecución

| Orden | Archivo | Qué hace |
|---|---|---|
| 00 | `00_Setup_DatosSinteticos_Ecommerce_Modificado.ipynb` | Genera los datos sintéticos y las cinco tablas Bronze. |
| 01 | `01_Medallion.py` | Limpia Silver y construye las tablas Gold. |
| 02 | `02_RAG_Ingestion.py` | Carga los PDFs, crea fragmentos y prepara Vector Search. |
| 03 | `03_UC_Tools.py` | Registra las dos funciones SQL y la función Python. |
| 04 | `04_Agente_MLflow.py` | Genera el archivo del agente, registra una candidata y ejecuta pruebas. |
| Soporte de 04 | `agente_ecommerce_template.py` | Contiene el agente, las herramientas, el prompt y el wrapper ResponsesAgent. |
| 05 | `05_MLflow_Evaluate.py` | Evalúa la candidata, guarda resultados y asigna champion si aprueba. |
| 06 | `06_Deploy_Endpoint.py` | Despliega la versión aprobada y prueba una consulta al endpoint. |
| App | `App_Web/app.py`, `app.yaml`, `requirements.txt` | Interfaz de chat y configuración de la aplicación. |
| Pruebas locales | `tests/test_chat.py` | Comprueba la lógica del chat con dependencias simuladas. |

También se conservaron dos notebooks de diagnóstico: `07_Diagnostico_Endpoint.py` revisa el endpoint y `08_Diagnostico_Conversacion.py` reproduce un fallo histórico de la versión 15. No forman parte del orden normal de despliegue. El 07 incluye una comparación histórica con la versión 12; el 08 debe ajustarse si se quiere consultar otra versión. `get_logs.py` es un auxiliar antiguo que apunta al endpoint v4.

## Cómo preparar el entorno

Se necesita un workspace de Databricks con Unity Catalog, acceso a compute, Model Serving, Vector Search, Databricks Apps y los modelos usados. Este repositorio contiene el código y las evidencias, no una copia de las tablas ni de los artefactos MLflow del workspace.

1. Importar 00–06 como notebooks. Subir `agente_ecommerce_template.py` como **archivo Python**, junto al notebook 04.
2. Revisar catálogo y esquema. En las pruebas se usaron `workspace` y `reto_ecommerce`.
3. Ejecutar 00 y 01. Para el requisito de automatización, configurar un Job con una tarea que ejecute 01 y conservar una corrida correcta.
4. Crear el volumen `pdfs_ecommerce` y cargar los tres PDFs de `pdfs_fuente/` en `/Volumes/workspace/reto_ecommerce/pdfs_ecommerce`.
5. Ejecutar 02 y 03 para preparar la búsqueda documental y las funciones.
6. Ejecutar 04 y después 05. Revisar las métricas y cualquier caso rechazado antes de desplegar.
7. Ejecutar 06, que toma la versión champion y la despliega en `ecommerce_agent_endpoint_v5`.
8. Subir los tres archivos de `App_Web/` a la carpeta fuente de una Databricks App. Añadir el endpoint v5 como recurso con permiso **Can query**, conservando la clave `serving-endpoint`, y desplegar la App.

Cada notebook instala sus dependencias. La App se autentica con su identidad de servicio; no es necesario pegar tokens en el código. El nombre v5 identifica el endpoint, no la versión del modelo que sirve.

## Evaluación y resultado obtenido

La evaluación usa el dataset persistido `workspace.reto_ecommerce.eval_dataset_bebot`. Tiene **34 casos** que cubren pedidos y perfiles reales de Gold, beneficios, documentos, identificadores ausentes, registros inexistentes, solicitudes de secretos y cambios de tema con historial.

Se combinaron jueces de relevancia, seguridad y cumplimiento de las reglas con una comprobación de términos esperados. El juez de alcance recibe también resultados de herramientas para contrastar las afirmaciones. La comprobación de términos ayuda a detectar omisiones, pero no mide por sí sola toda la exactitud de una respuesta.

La última evaluación aprobada corresponde a la **versión 16**, con run `e92f4fbc814945ad83bc2d94c2fc3892`:

| Métrica | Media |
|---|---:|
| Relevancia de la respuesta | 0.9705882352941176 |
| Seguridad | 1.0 |
| Alcance y no inventar | 1.0 |
| Datos esperados presentes | 0.9705882352941176 |

Las cuatro medias superaron el umbral de 0.80. El notebook también bloquea la promoción si encuentra errores en los resultados. Estos valores no significan que todas las respuestas sean perfectas: queda por revisar individualmente el caso con términos faltantes y el caso rechazado por relevancia, que pueden ser distintos.

El CSV completo se generó en Databricks como `evidencias/evaluacion_version_16_e92f4fbc814945ad83bc2d94c2fc3892.csv`, pero no se descargó a este repositorio. Se conserva la captura de las métricas, que cumple la alternativa de evidencia mediante capturas indicada en el reto.

![Evaluación de 34 casos de la versión 16](evidencias/v16_evaluacion_metricas.png)

## Evidencia del chat funcionando

Las siguientes capturas corresponden a conversaciones reales, no a un diseño de ejemplo.

**Perfil y beneficios.** Primero el bot pide el correo; al recibirlo devuelve el perfil y luego usa el segmento Recurrente para explicar los beneficios. Esta prueba se recogió con la versión 15.

![Perfil y beneficios en varios turnos](evidencias/v15_app_beneficios_contexto.png)

**Consulta de documentos.** Para un paquete dañado indica conservar el empaque y preparar fotografías. En el siguiente turno identifica la guía que respalda la recomendación. Prueba recogida con la versión 15.

![Respuesta documental y fuente](evidencias/v15_app_fuente_documental.png)

**Corrección final del cambio de tema.** En la versión 15 encontramos un fallo: después de un pedido inexistente, el agente repetía esa respuesta cuando se le pedían secretos. Se ajustó el prompt, se añadieron pruebas con historial y se registró la versión 16. La captura final muestra el rechazo correcto, después del despliegue de esa versión.

![Versión 16: rechazo de secretos después de una consulta de pedido](evidencias/v16_app_secretos_tras_pedido_aprobada.png)

## Pruebas del proyecto

Las pruebas del chat cubrieron consultas de pedidos, perfiles, beneficios y políticas de la tienda. También se comprobó que el agente pidiera los identificadores necesarios, mantuviera el contexto entre mensajes y rechazara solicitudes de credenciales e instrucciones internas.

La versión 16 superó la evaluación de 34 casos y se desplegó en el endpoint `ecommerce_agent_endpoint_v5`. Las métricas y las capturas de este README muestran los resultados obtenidos.

Para ejecutar las pruebas locales desde la carpeta del proyecto:

```bash
python -m unittest discover -s tests -v
```

Las ocho pruebas locales comprueban el envío del historial, la entrada de preguntas, el inicio de una conversación nueva y el manejo de respuestas vacías o errores. Se ejecutan con versiones simuladas de Streamlit y del SDK, sin necesitar una conexión a Databricks.

## Galería completa de capturas conservadas

Esta galería reúne 16 capturas de las pruebas, la evaluación y el proceso de diagnóstico. Las imágenes de errores corresponden a versiones anteriores; los resultados de la versión 16 se presentan primero.

### Resultado final — versión 16

<details>
<summary>Versión 16: corrección comprobada en la App</summary>

![Versión 16: corrección comprobada en la App](evidencias/v16_app_secretos_tras_pedido_aprobada.png)

</details>

<details>
<summary>Versión 16: métricas de evaluación de 34 casos</summary>

![Versión 16: métricas de evaluación de 34 casos](evidencias/v16_evaluacion_metricas.png)

</details>

<details>
<summary>Versión 16: prueba de regresión en MLflow</summary>

![Versión 16: prueba de regresión en MLflow](evidencias/v16_regresion_secretos_tras_pedido_aprobada.png)

</details>

### Pruebas funcionales anteriores — versión 15

<details>
<summary>Perfil y beneficios según el contexto</summary>

![Perfil y beneficios según el contexto](evidencias/v15_app_beneficios_contexto.png)

</details>

<details>
<summary>Respuesta RAG y documento que la respalda</summary>

![Respuesta RAG y documento que la respalda](evidencias/v15_app_fuente_documental.png)

</details>

<details>
<summary>Recomendaciones para un paquete dañado</summary>

![Recomendaciones para un paquete dañado](evidencias/v15_app_paquete_danado.png)

</details>

<details>
<summary>Pedido y productos en turnos separados</summary>

![Pedido y productos en turnos separados](evidencias/v15_app_pedido_contexto.png)

</details>

<details>
<summary>Pedido inexistente sin inventar un estado</summary>

![Pedido inexistente sin inventar un estado](evidencias/v15_app_pedido_inexistente.png)

</details>

<details>
<summary>Solicitud de correo y consulta del perfil</summary>

![Solicitud de correo y consulta del perfil](evidencias/v15_app_perfil_dos_turnos.png)

</details>

<details>
<summary>Rechazo de credenciales y solicitud del ID</summary>

![Rechazo de credenciales y solicitud del ID](evidencias/v15_app_rechazo_credenciales_pedido_sin_id.png)

</details>

<details>
<summary>App desplegada en estado Running</summary>

![App desplegada en estado Running](evidencias/v15_app_running.png)

</details>

<details>
<summary>Seguridad al inicio y cambio de tema</summary>

![Seguridad al inicio y cambio de tema](evidencias/v15_app_seguridad_inicio_cambio_tema.png)

</details>

### Errores y diagnóstico histórico — versión 15

<details>
<summary>Fallo histórico: repetición de respuesta ante secretos</summary>

![Fallo histórico: repetición de respuesta ante secretos](evidencias/v15_app_fallo_cambio_tema_seguridad.png)

</details>

<details>
<summary>Reproducción del fallo de conversación en la versión 15</summary>

![Reproducción del fallo de conversación en la versión 15](evidencias/v15_app_fallo_reproducido_secretos_tras_pedido.png)

</details>

<details>
<summary>Diagnóstico: rechazo correcto sin historial</summary>

![Diagnóstico: rechazo correcto sin historial](evidencias/v15_traza_control_secretos_sin_historial.png)

</details>

<details>
<summary>Diagnóstico: consulta incorrecta del pedido tras solicitar secretos</summary>

![Diagnóstico: consulta incorrecta del pedido tras solicitar secretos](evidencias/v15_traza_tools_tras_secretos.png)

</details>

