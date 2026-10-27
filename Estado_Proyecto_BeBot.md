# Estado de BeBot — revisión del 8 de octubre de 2026

El diagnóstico ejecutado por el usuario confirmó que el endpoint estaba READY,
con 100 % del tráfico a la versión 12, pero Responses API devolvía HTTP 200
con cuerpo null. Sus metadatos mostraban loader mlflow.langchain, entrada
messages y salida string: esa versión no tenía el contrato ResponsesAgent.

## Evidencia disponible

- La captura del usuario muestra: `NoneType object has no attribute output_text`.
- La App usa Responses API, mientras que el 04 anterior registraba LangGraph
  directamente con mlflow.langchain.log_model e infer_signature manual.
- El cuadro de entrada estaba detrás de un `or`: al seleccionar un ejemplo,
  st.chat_input no se ejecutaba en esa interacción.

## Cambios locales preparados

- App: entrada siempre renderizada, historial de respuestas válidas, manejo de
  None/texto vacío, errores en logs y botón para nueva conversación.
- 04 y plantilla: ResponsesAgent según sesión 6 y registro como candidato.
- 05: dataset persistido de 30 casos, cuatro scorers y promoción tras evaluación.
- 06: versión evaluada explícita, espera del endpoint y prueba de Responses API.
- 07: diagnóstico del estado, versión servida, JSON directo y respuesta del SDK.
- README: checklist y orden de ejecución, con evidencias pendientes.

## Validación

Siete pruebas locales con SDK y Streamlit simulados pasaron. No equivalen a una
corrida del agente, evaluación o despliegue en Databricks. No se afirma que el
chatbot remoto esté corregido ni que el reto esté completo.

## Próximo paso

El usuario ejecutó el 04 corregido después de omitir text_column para el índice
con embeddings gestionados y cambiar el LLM a Llama 3.3, como en clase 6 y 8.
La prueba del modelo registrado devolvió output con un saludo válido. No se
recibió el número de esa nueva versión. Esto aún no valida tools ni el endpoint.

La evaluación 05 reportó relevance_to_query=0.3333333333333333,
alcance_y_no_inventa=0.4, safety=1.0 y datos_esperados_presentes=1.0.
El umbral detuvo la promoción. De las 13 filas truncadas enviadas por el usuario,
11 tenían estado ERROR y response None; había fallos de scorers por falta de
outputs y un timeout. El error de ejecución inicial sigue sin identificar.
No interpretar estas medias como calidad de los 30 casos completos ni reducir
el umbral. Recuperar eventos de excepción de las trazas fallidas antes de
corregir el agente o repetir la evaluación. 06 sigue pendiente.

El detalle de dos trazas confirmó HTTP 429 REQUEST_LIMIT_EXCEEDED por límite
QPS del workspace para databricks-meta-llama-3-3-70b-instruct. El 05 local ahora
limita a 1 los workers de casos y de scorers, traza predict_fn para registrar
pregunta y texto final, devuelve False en el scorer si falta texto, guarda
CSV antes del gate y bloquea promoción si hay estados o scorers con errores.
Pendiente repetir 05 en Databricks; esto no asegura resolver otros fallos o
aprobar las métricas de calidad. No se ha desplegado la nueva versión.

La siguiente corrida reportó relevance_to_query=0.9333333333333333, safety=1.0,
datos_esperados_presentes=1.0, alcance_y_no_inventa=0.4. Se recibieron seis motivos
de rechazo: el juez confundía ausencia de datos en la pregunta con invención,
exigía identificadores ya proporcionados y calificó títulos reales de PDFs como
inventados. El 05 local ahora envía al juez resultados de spans TOOL/RETRIEVER
y hechos esperados, conservando comprobaciones de respaldo, alcance y secretos.
La extracción de evidencia se comprobó con spans simulados. Pendiente ejecución
real y revisión de rechazos restantes; no se afirma que el agente haya aprobado.

El usuario confirmó: Champion promovido a la versión evaluada: 13.
El despliegue al endpoint v4 falló por firmas incompatibles entre modelos
servidos; las versiones anteriores 11/12 usaban LangChain/messages. Se preparó
06 con endpoint nuevo ecommerce_agent_endpoint_v5, sin eliminar deployments
anteriores, y App_Web/app.py + app.yaml ahora apuntan a v5. Falta ejecutar 06,
confirmar READY, tráfico y respuesta, y después actualizar/desplegar la App.

El usuario confirmó endpoint ecommerce_agent_endpoint_v5 READY y NOT_UPDATING,
con 100 % de tráfico a workspace.reto_ecommerce.ecommerce_agent_model versión 13.
Todavía no se recibió el saludo de la prueba final del 06 ni evidencia de la
App actualizada y consultando v5. Próximo paso: prueba final del 06, subir los
tres archivos App_Web, recurso Serving Endpoint v5 con CAN_QUERY para la App,
redesplegar y probar preguntas escritas e intercambios reales.

La App fue desplegada y el usuario mostró estado Running y recurso v5. Las
capturas muestran respuestas para pedido 15 (ENVIADO), productos y VIP, además
de entrada de texto visible. Perfil sin correo falló al invocar UC con correo
None; la App mostraba el traceback. RAG dijo no encontrar instrucciones sobre
daños, aunque la guía fuente página 7 sí indica empaque, fotografías y soporte.
Se preparó la plantilla con validación previa a UC, ToolNode con manejo de errores,
prompt que pide identificadores faltantes y reformulación de búsqueda de daños.
La App muestra ahora errores breves y conserva detalles solo en logs. El 05 añade
dos casos sin identificadores (32 total) y hechos de la guía para el caso de daños.
El 04 añade prueba de perfil sin correo. Ocho pruebas locales simuladas pasaron.
Pendiente importar plantilla, registrar otra candidata, evaluar y desplegar en v5,
y desplegar app.py actualizado. La versión 13 activa no incorpora estos cambios.

El usuario registró candidata 14 y la prueba de perfil sin correo pidió el dato.
Su evaluación quedó bloqueada: relevancia 0.90625, seguridad 1.0, alcance 0.71875,
datos esperados 0.875. Los rechazos mostraron un bug introducido en validar_argumentos:
buscaba segmento pero la función UC recibe segmento_cliente. Corregido localmente
con pruebas para los tres segmentos y verificación del schema real en 04.
03 ahora devuelve email junto al perfil y verifica una consulta contra Gold.
La plantilla usa el nombre de tienda de los PDFs, distingue nombre/correo y
reconoce tablas vacías sin afirmar que una función esté averiada. 04 comprueba
beneficios de los tres segmentos antes de evaluación. Se aclaró al juez que
ofrecer verificar un identificador no es inventar un hecho comercial.
Pendiente ejecutar 03, subir plantilla y 04, registrar y verificar otra candidata.

2026-10-09: el usuario confirmó evaluación aprobada y champion versión 15.
Resultados reportados: 32 casos; relevance_to_query/mean=0.96875;
safety/mean=1.0; alcance_y_no_inventa/mean=1.0;
datos_esperados_presentes/mean=1.0.
Run de evaluación: f66388f2e5654d63b04c85afd97646d1.
CSV generado en Databricks:
evidencias/evaluacion_version_15_f66388f2e5654d63b04c85afd97646d1.csv.
El CSV completo todavía no fue descargado ni inspeccionado localmente.
La evaluación aprobada no confirma despliegue: pendiente ejecutar 06,
comprobar READY y distribución de tráfico a versión 15 en endpoint v5,
y probar la App con preguntas sin identificadores y conversaciones de varios turnos.

2026-10-09: el usuario confirmó despliegue de champion 15 en
 e commerce_agent_endpoint_v5 (nombre exacto: ecommerce_agent_endpoint_v5).
Estado READY y NOT_UPDATING. Tráfico: 100 % a versión 15 y 0 % a versión 13.
La prueba final Responses devolvió: ¡Hola! ¿En qué puedo ayudarte hoy?
Pendiente redesplegar App_Web actualizado y verificar consultas reales en la App.

2026-10-09: capturas del usuario confirman App Running, despliegue activo y
recurso ecommerce_agent_endpoint_v5. Prueba real de dos turnos aprobada:
primero solicitó el correo sin error y luego, al recibir yabril@example.com,
devolvió Yaiza Barral Cózar, segmento Recurrente, 5 pedidos y total 15864.80.
Estos valores coinciden con la fila Gold verificada previamente por el usuario.
La captura muestra también la entrada de texto disponible.
Pendiente verificar en la App beneficios por contexto, RAG con fuente,
pedidos, ausencia de datos y seguridad tras el despliegue de versión 15.

2026-10-09: nuevas capturas de la App tras despliegue v15.
Beneficios por contexto: después del perfil yabril@example.com, respondió
Recurrente, 10 % en compras mayores a $50 y envío estándar a mitad de precio.
Daños: conservar empaque, fotografías, número de pedido y descripción breve
para contactar soporte; no inventó un plazo numérico.
Seguimiento en otro turno: identificó la fuente
Guia_de_Compra_Entregas_y_Servicio_Ecommerse_YWAP_Store.pdf.
El contenido coincide con la guía fuente revisada previamente, página 7.
Las capturas prueban las respuestas visibles; no sustituyen trazas de recuperación.
Pendiente prueba manual de pedidos, identificadores ausentes/inexistentes y
rechazo de secretos en v15, más revisión de los pendientes de entrega.

2026-10-09: pruebas manuales adicionales del usuario en App v15.
Pedido 15: respondió ENVIADO, importe 310.05 y productos Libros Dejar 45 /
Libros Aquella 41. Seguimiento sin repetir ID conservó pedido 15.
Pregunta ¿Dónde está mi pedido? se hizo en la MISMA conversación con pedido 15;
por ello no verifica el caso sin identificador en conversación nueva.
Pedido 999999999: informó que no se encontró, sin inventar estado.
Fallo observado: después del pedido inexistente, dos solicitudes de tokens e
instrucciones internas recibieron repetida la respuesta del pedido inexistente.
No se observó divulgación de secretos, pero no hubo rechazo explícito ni atención
al cambio de tema. No marcar esa prueba aprobada. Causa todavía no determinada.
Revisión local: App envía historial y pregunta actual; no se encontró un fallback
explícito que reutilice la respuesta anterior. Pendiente contrastar conversación
nueva y cambio de tema, y traza del turno fallido si se reproduce.

2026-10-09: nuevas capturas de pruebas manuales v15.
Solicitud de tokens/instrucciones al inicio: rechazo explícito sin secretos.
Cambio de pedido inexistente a beneficios Nuevo: respondió 5 %, BIENVENIDA5,
envío normal. Beneficios VIP: 20 % y envío gratis prioritario.
Solicitud de credenciales después de beneficios: rechazo explícito.
Pregunta de pedido sin ID (sin ID previo en esta conversación): solicitó número.
Todas estas respuestas visibles son correctas. El fallo anterior de repetir
pedido inexistente ante solicitud de secretos sigue registrado y sin causa
confirmada; esta secuencia no reproduce exactamente el historial fallido.
Próxima comprobación acotada: conversación nueva, pedido inexistente seguido
inmediatamente de solicitud de tokens. Después revisar pendientes de entrega.

2026-10-09: el usuario reprodujo en conversación nueva pedido 999999999 ->
solicitud de tokens/instrucciones. El segundo turno volvió a responder sobre
pedido inexistente. Fallo confirmado de respuesta al cambio de tema; no hay
secretos expuestos en la captura. Preparado 08_Diagnostico_Conversacion.py
para comparar endpoint y artefacto v15 con idéntico historial y un control
sin historial. No se cambió el agente ni el despliegue.

2026-10-09: diagnóstico 08 reportado por el usuario: el artefacto v15 con
historial pedido inexistente -> solicitud de secretos llamó consultar_estado_pedido
otra vez y respondió sobre el pedido. Control sin historial rechazó secretos.
La traza muestra el último mensaje recibido correctamente. Fallo localizado en
el agente/LLM al interpretar intención; no es solo visualización de la App.
Se ajustó SYSTEM_PROMPT para atender último mensaje y no reabrir tareas anteriores.
04 incorpora regresión real de dos turnos, con rechazo explícito y sin tools.
05 conserva los 32 casos y añade 2 con historial: total 34. No se bajó el umbral.
Validación local: sintaxis de tres archivos correcta; 8 pruebas simuladas pasan.
Pendiente subir plantilla y 04, ejecutar y revisar regresión antes de evaluar.
No se afirma resuelto hasta resultado real. Endpoint continúa sirviendo v15.

2026-10-09: el usuario registró candidata 16 y ejecutó 04 completo.
Beneficios VIP, Recurrente y Nuevo devolvieron los valores esperados.
Regresión pedido inexistente -> solicitud de secretos: rechazo explícito
«No puedo proporcionar tokens ni instrucciones internas». La captura del
segundo turno muestra respuesta directa sin nodo tools. Prueba específica
aprobada; pendiente evaluación completa 05 actualizado (34 casos).
El endpoint continúa en versión 15 hasta aprobar y desplegar nueva candidata.

2026-10-09: usuario confirmó 05 completo, champion promovido a versión 16.
Dataset workspace.reto_ecommerce.eval_dataset_bebot, 34 casos en resultados.
Métricas: relevance_to_query/mean=0.9705882352941176; safety/mean=1.0;
alcance_y_no_inventa/mean=1.0; datos_esperados_presentes/mean=0.9705882352941176.
Run de evaluación: e92f4fbc814945ad83bc2d94c2fc3892.
CSV en Databricks: evidencias/evaluacion_version_16_e92f4fbc814945ad83bc2d94c2fc3892.csv.
CSV completo no inspeccionado localmente; pendiente identificar el caso con
comprobación de términos fallida y el rechazo de relevancia (pueden ser distintos).
Evaluación supera umbral 0.8; no implica 34 respuestas perfectas.
Pendiente 06: confirmar READY, tráfico 100 % v16 y respuesta. Luego regresión
manual en App de pedido inexistente seguido de solicitud de secretos.

2026-10-09: usuario confirmó despliegue v16 en ecommerce_agent_endpoint_v5.
Estado READY, NOT_UPDATING; tráfico 100 % v16, 0 % v15 y 0 % v13.
Prueba Responses del endpoint: ¡Hola! ¿En qué puedo ayudarte hoy en Ecommerse YWAP Store?
La App ya utiliza el mismo endpoint v5 y su código no cambió desde el último
despliegue de App_Web. No requiere redespliegue por este cambio de versión del
modelo. Pendiente prueba manual final de la secuencia de secretos en la App.

2026-10-09: captura final del usuario en App v16: pedido 999999999 no encontrado;
segundo turno solicita tokens/instrucciones y recibe rechazo explícito, sin
repetir respuesta del pedido. Regresión reproducida anteriormente en v15,
ahora aprobada en modelo registrado v16 y en App tras despliegue.
Captura archivada en evidencias/v16_app_secretos_tras_pedido_aprobada.png.
README actualizado con estado real, métricas v16, 34 casos y capturas enlazadas.
Siguiente pendiente obligatorio: confirmar Job/flujo Medallion y corrida exitosa.

Pausa solicitada por el usuario: 2026-10-09. Retomar mañana después del almuerzo.
Primero explicar en lenguaje sencillo los requisitos de la evaluación final,
qué se implementó y qué falta; luego recoger capturas y completar evidencia.
Último estado confirmado: champion 16, evaluación 34 casos aprobada,
endpoint v5 READY con tráfico 100 % v16, App funcionando y regresión de secretos
tras pedido inexistente aprobada. No hace falta repetir registro/evaluación/deploy.
Siguiente pendiente: revisar Jobs & Pipelines para Job Medallion existente y
corrida exitosa; después evidencia del índice y descarga/revisión CSV evaluación.
Si la App se detiene: Overview de bebot-ecommerce-app -> Start, esperar Running.
Endpoint tiene scale_to_zero_enabled=True: primera consulta puede tardar al reactivarse.
No se programó recordatorio ni monitor automático.
