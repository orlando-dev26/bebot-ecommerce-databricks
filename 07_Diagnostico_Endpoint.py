# Databricks notebook source
# MAGIC %md
# MAGIC # 07 - Identificar la versión y el formato real del endpoint
# MAGIC Ejecuta ANTES de registrar o desplegar una versión nueva.
# MAGIC No modifica recursos. La prueba Hola realiza una petición de inferencia.

# COMMAND ----------
# MAGIC %pip install databricks-sdk databricks-openai

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
from databricks.sdk import WorkspaceClient
from databricks_openai import DatabricksOpenAI

ENDPOINT_NAME = "ecommerce_agent_endpoint_v5"
w = WorkspaceClient()
endpoint = w.serving_endpoints.get(ENDPOINT_NAME)
print("Endpoint:", endpoint.name)
print("Estado:", endpoint.state)
config = endpoint.config
entities = (getattr(config, "served_entities", None)
            or getattr(config, "served_models", None) or [])
for entity in entities:
    print("Entidad:", entity.name)
    print("Modelo:", getattr(entity, "entity_name", None) or getattr(entity, "model_name", None))
    print("Versión:", getattr(entity, "entity_version", None) or getattr(entity, "model_version", None))
print("AI Gateway / inferencia:", getattr(endpoint, "ai_gateway", None))
print("Distribución de tráfico:", getattr(config, "traffic_config", None))

# COMMAND ----------
# Inspecciona la respuesta HTTP sin que el SDK normalice null/vacío a {}.
# Usa la ruta Responses documentada, equivalente al cliente de la App.
import requests

raw = None
http_response = requests.post(
    f"{w.config.host.rstrip('/')}/serving-endpoints/responses",
    headers={**w.config.authenticate(), "Content-Type": "application/json"},
    json={"model": ENDPOINT_NAME,
          "input": [{"role": "user", "content": "Hola"}], "stream": False},
    timeout=(10, 180),
)
# No imprimir las cabeceras de autenticación.
print("Distribución de tráfico:", getattr(endpoint.config, "traffic_config", None))
print("HTTP:", http_response.status_code)
print("Content-Type:", http_response.headers.get("content-type"))
print("Bytes recibidos:", len(http_response.content))
print("Cuerpo de respuesta:", repr(http_response.text[:6000]))
if http_response.ok:
    try:
        raw = http_response.json()
    except ValueError:
        print("La respuesta no contiene un JSON válido.")
    if not isinstance(raw, dict) or not isinstance(raw.get("output"), list):
        print("No se recibió output como lista. Conserva esta salida para investigar; "
              "todavía no determina qué versión o componente causa el problema.")
else:
    print("La petición falló. El código HTTP y el cuerpo anterior permiten diagnosticarla.")

# COMMAND ----------
if isinstance(raw, dict) and isinstance(raw.get("output"), list):
    response = DatabricksOpenAI().responses.create(
        model=ENDPOINT_NAME, input=[{"role": "user", "content": "Hola"}], stream=False,
    )
    if response is None:
        print("El cliente devolvió None. Esta segunda petición puede haber recibido "
              "otra versión si el tráfico está repartido; compara con la salida HTTP.")
    else:
        print("Texto del SDK:", getattr(response, "output_text", None))
else:
    print("Prueba del SDK omitida: primero revisa la respuesta HTTP de la celda anterior.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Comparación histórica: revisar el registro anterior de la versión 12
# MAGIC En v4 se observó: versión 12 con 100 % de tráfico, HTTP 200 y cuerpo null.
# MAGIC La versión 12 no es la versión nueva que se pretende servir en v5.
# MAGIC Esta celda consulta metadatos; no carga ni ejecuta el modelo, ni cambia el endpoint.
# MAGIC Si falta MLflow, instala con `%pip install "mlflow>=3.1.0"`, reinicia Python
# MAGIC y ejecuta esta celda de forma independiente.

# COMMAND ----------
import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")
MODEL_NAME = "workspace.reto_ecommerce.ecommerce_agent_model"
VERSION_A_REVISAR = "12"
client = MlflowClient()
version = client.get_model_version(MODEL_NAME, VERSION_A_REVISAR)
info = mlflow.models.get_model_info(f"models:/{MODEL_NAME}/{VERSION_A_REVISAR}")
print("Modelo:", version.name)
print("Versión revisada:", version.version)
print("Run ID:", version.run_id)
print("Flavors / configuración:", info.flavors)
print("Firma de entrada y salida:", info.signature)
print("Estos metadatos ayudan a identificar el registro; por sí solos no prueban "
      "que predict devuelva correctamente una respuesta.")
