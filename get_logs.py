import os
from databricks.sdk import WorkspaceClient

# Configurar el cliente
w = WorkspaceClient()

ENDPOINT_NAME = "ecommerce_agent_endpoint_v4"

print(f"Buscando los logs de error del endpoint {ENDPOINT_NAME}...\n")

try:
    events = w.serving_endpoints.get_events(name=ENDPOINT_NAME)
    for event in events:
        print(f"[{event.timestamp}] {event.event_type}: {event.message}")
except Exception as e:
    print("Error obteniendo eventos:", e)

try:
    logs = w.serving_endpoints.get_build_logs(name=ENDPOINT_NAME, served_model_name="workspace-reto_ecommerce-ecommerce_agent_model_8")
    print("\n--- BUILD LOGS ---")
    print(logs.logs)
except Exception as e:
    print("\nNo se pudieron obtener los build logs detallados:", e)
