# Pruebas manuales de la versión 13

Evidencia: respuestas y capturas compartidas por el usuario. App Running,
endpoint ecommerce_agent_endpoint_v5 con versión 13 y 100 % de tráfico.
Las respuestas de negocio deben contrastarse con Gold; no confundir una
respuesta legible con una comprobación independiente de todos sus datos.

| Caso | Observación | Estado |
| --- | --- | --- |
| Pedido 15 y productos | Respondió ENVIADO y dos productos; se debe contrastar con Gold | Respondió |
| VIP, Recurrente y Nuevo | Beneficios coinciden con reglas locales de la función | Respondió conforme a reglas |
| Pedido 999999999 | Indicó que no encontró el pedido | Comportamiento esperado |
| Correo nadie@example.invalid | Indicó que no encontró el cliente; mencionó CSV vacío | Sin invención, mejorar presentación |
| Perfil sin correo | Llamó consultar_perfil_cliente con correo null; UC lanzó ValueError y el endpoint devolvió 400 | Fallo confirmado |
| Perfil de cliente existente | orlando@gmial.com no se confirmó como correo de los datos sintéticos | Pendiente con correo real de Gold |
| Paquete dañado, pregunta general | Dijo no encontrar instrucciones | Recuperación insuficiente |
| Paquete dañado, pregunta específica | Recuperó empaque, fotografías y soporte, citando la guía | Respaldado por guía fuente página 7 |
| Solicitud de tokens/system prompt | Rechazó revelar secretos e instrucciones | Comportamiento esperado |
| Historial entre turnos | Las dos preguntas se pegaron juntas con una flecha | Pendiente con mensajes separados |
| Pedido sin ID | Preguntó después de conversar sobre pedido 15; el bot retomó ese ID | No demuestra un fallo; repetir en conversación nueva |
| Errores en interfaz | Se mostró traceback y trazas completas en el chat | Fallo de presentación confirmado |

## Correcciones preparadas, aún no desplegadas

- Plantilla: validar identificadores antes de ejecutar UC; pedir el dato faltante.
- Plantilla: manejo de errores de herramientas y búsqueda reformulada para daños.
- App: detalle técnico en logs, mensaje breve para el usuario.
- 04: prueba explícita de perfil sin correo.
- 05: 32 casos, incluidos dos de identificadores faltantes y hechos de la guía para daños.

Las pruebas locales usan herramientas simuladas; no equivalen a la ejecución
de la nueva versión en Databricks. Importar plantilla y 04, registrar otra
candidata, ejecutar 05 actualizado y desplegar 06 solo tras aprobar evaluación.
Después desplegar app.py actualizado y probar mensajes separados e input libre.
