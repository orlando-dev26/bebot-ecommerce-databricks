# Revisión para entrega — 26 de octubre de 2026

Se contrastó el código con `EVALUACION_FINAL/reto_alumno/README.md`, sin modificar
los materiales del profesor. Esta revisión distingue el funcionamiento probado
el 9 de octubre de la disponibilidad actual de la cuenta, que no se ha comprobado.

## Dictamen

El proyecto se puede publicar como avance funcional con evidencias reales.
No se puede afirmar todavía que los nueve requisitos obligatorios estén
acreditados: falta confirmar el Job o flujo de Medallion y su ejecución.
El notebook de transformaciones existe, pero no se encontró una definición
de Job guardada en esta carpeta ni evidencia de su ejecución en Databricks.
Esto no prueba que el Job no exista en el workspace.

| Requisito del reto | Resultado de la revisión |
|---|---|
| Job/flujo Bronze → Silver → Gold | 01 procesa las cinco tablas Bronze, genera cinco Silver y tres Gold. Job y corrida pendientes de acreditar. |
| RAG documental | 02 carga PDFs, genera chunks de 1000 caracteres con solapamiento de 150 y guarda Delta. Hay respuestas reales con fuente documental. |
| Vector Search | 02 crea índice Delta Sync con embeddings gestionados; la recuperación funcionó. No se exige una captura específica del índice en el README del reto. |
| Tres UC tools, una Python | 03 incluye dos funciones SQL y una Python; se probaron pedidos, perfiles y beneficios. |
| ResponsesAgent | Plantilla con LangGraph y wrapper MLflow; versión 16 registrada y desplegada. |
| System prompt | Incluye selección de tools, datos faltantes, respaldo documental, secretos y cambio de tema. Regresión de conversación corregida y probada. |
| Evaluación offline persistida | Dataset UC de 34 casos; versión 16 aprobada. Captura de métricas disponible. |
| Endpoint agents.deploy | Salida compartida: v5 READY, 100 % de tráfico al modelo 16 y saludo correcto. Evidencia histórica, no comprobación en vivo del 26 de octubre. |
| Databricks App | Capturas de intercambios reales, entrada libre y seguimiento de conversación. |
| README y evidencias | Descripción, orden de ejecución, capturas del chat y captura de evaluación incluidos. |

## Resultado de evaluación conservado

- Versión: 16; run: `e92f4fbc814945ad83bc2d94c2fc3892`.
- Relevancia: 0.9705882352941176.
- Seguridad: 1.0.
- Alcance y no inventar: 1.0.
- Datos esperados: 0.9705882352941176.
- Los casos con valoraciones negativas aún no se revisaron individualmente.
- El CSV completo no está en la carpeta local. La captura de métricas sí cumple
  la alternativa de evidencia «capturas o export» del enunciado; descargar el CSV
  mejoraría el diagnóstico, pero no es un requisito adicional del profesor.

## Preparación del repositorio

Publicar el contenido de `Resolviendo Proyecto Final`, no toda la carpeta del
curso. Se añadieron los tres PDFs en `pdfs_fuente/` como copias de los documentos
del reto, y `.gitignore` para excluir configuración local, entornos y scratch.
Para reproducir el RAG, cargar esos PDFs en el volumen indicado por 02.
Los notebooks requieren una cuenta Databricks con los recursos y permisos
necesarios; el repositorio no incluye los artefactos MLflow ni las tablas UC.

Antes de declarar entrega completa:

1. Confirmar si ya existe un Job que ejecute 01 y conservar la evidencia disponible.
2. Si no existe, configurarlo y ejecutar cuando se disponga de acceso a compute.
   No marcar esa ejecución como realizada a partir del código solamente.
3. Crear el repositorio y comprobar que README y capturas se visualizan.
4. Verificar con MitoCode la recepción fuera de plazo: el enunciado conservado
   indica «fecha máxima: 30 de septiembre». No hay evidencia de una prórroga.

La vigencia de la prueba gratuita no determina por sí sola si la cuenta conserva
acceso o tiene facturación activa. Eso debe comprobarse en la cuenta del alumno;
no se cambió ningún ajuste de suscripción ni se inició ningún recurso remoto.

## Validación local

Las ocho pruebas simuladas de `tests/test_chat.py` pasan. Estas pruebas verifican
la lógica local y no sustituyen una nueva ejecución en Databricks.
