# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - Desplegar la versión evaluada y probar el endpoint
# MAGIC Sigue la sesión 6 y el proyecto integrador. El paso 05 asigna champion
# MAGIC únicamente a la versión que supera la evaluación.

# COMMAND ----------
# MAGIC %pip install databricks-agents databricks-openai "mlflow>=3.1.0"

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
import mlflow
from datetime import timedelta
from databricks import agents
from databricks.sdk import WorkspaceClient
from databricks_openai import DatabricksOpenAI

MODEL_NAME = "workspace.reto_ecommerce.ecommerce_agent_model"
# Endpoint separado: v4 conserva versiones LangChain con firma incompatible.
ENDPOINT_NAME = "ecommerce_agent_endpoint_v5"
usuario_actual = spark.sql("SELECT current_user()").first()[0]
mlflow.set_experiment(f"/Users/{usuario_actual}/ecommerce_agente_experiment_v1")
client = mlflow.MlflowClient(registry_uri="databricks-uc")
version = client.get_model_version_by_alias(MODEL_NAME, "champion").version
metadata = client.get_model_version(MODEL_NAME, version)
if metadata.tags.get("evaluacion_aprobada") != "true":
    raise RuntimeError("La versión champion no tiene evaluación aprobada. Ejecuta 05 primero.")
print(f"Versión que se desplegará: {MODEL_NAME}/{version}")

# COMMAND ----------
deployment_info = agents.deploy(
    model_name=MODEL_NAME, model_version=version, endpoint_name=ENDPOINT_NAME,
    scale_to_zero_enabled=True, workload_size="Small",
)
w = WorkspaceClient()
w.serving_endpoints.wait_get_serving_endpoint_not_updating(
    name=ENDPOINT_NAME, timeout=timedelta(minutes=30),
)
endpoint = w.serving_endpoints.get(ENDPOINT_NAME)
print("Estado del endpoint:", endpoint.state)
print("Endpoint:", endpoint.name)
print("Distribución de tráfico:", endpoint.config.traffic_config)
for entity in endpoint.config.served_entities or []:
    print("Entidad:", entity.entity_name, "Versión:", entity.entity_version)

# COMMAND ----------
respuesta = DatabricksOpenAI().responses.create(
    model=ENDPOINT_NAME, input=[{"role": "user", "content": "Hola"}], stream=False,
)
if respuesta is None or not respuesta.output_text:
    raise RuntimeError("El endpoint no devolvió texto. Ejecuta 07_Diagnostico_Endpoint.py.")
print(respuesta.output_text)
print("Luego redespliega App_Web y confirma CAN_QUERY para la identidad de la App.")
