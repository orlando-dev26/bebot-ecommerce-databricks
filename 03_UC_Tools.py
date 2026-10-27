# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Creación de Unity Catalog Tools
# MAGIC Este notebook crea 3 funciones (tools) registradas directamente en Unity Catalog.
# MAGIC Estas son las herramientas que el Agente usará para interactuar con la base de datos de "Be Store".

# COMMAND ----------

CATALOG = "workspace"
SCHEMA = "reto_ecommerce"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Tool 1: Consultar Estado de Pedido (SQL)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION consultar_estado_pedido(id_pedido INT)
RETURNS TABLE (pedido_id INT, estado STRING, total_pedido DOUBLE, cliente_nombre STRING, productos_incluidos ARRAY<STRING>)
COMMENT 'Busca y retorna el estado actual de un pedido, el total pagado y los productos incluidos basándose en el ID del pedido (ej. 1, 15, 20).'
RETURN SELECT pedido_id, estado, total_pedido, cliente_nombre, productos_incluidos 
       FROM gold_pedidos_estado 
       WHERE pedido_id = id_pedido
""")

print("Tool 1 (SQL) creada: consultar_estado_pedido")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Tool 2: Consultar Perfil de Cliente (SQL)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION consultar_perfil_cliente(correo STRING)
RETURNS TABLE (email STRING, nombre STRING, ciudad STRING, segmento STRING, total_pedidos BIGINT, total_gastado DOUBLE)
COMMENT 'Busca el perfil de un cliente usando su correo electrónico. Retorna su segmento (Nuevo/Recurrente/VIP), cantidad de pedidos históricos y total gastado.'
RETURN SELECT email, nombre, ciudad, segmento, total_pedidos, total_gastado
       FROM gold_clientes_resumen 
       WHERE email = correo
""")

print("Tool 2 (SQL) creada: consultar_perfil_cliente")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Tool 3: Calcular Beneficios por Segmento (Python)
# MAGIC *Nota: Requisito de evaluación: Al menos 1 tool debe ser en Python.*

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION calcular_beneficios_segmento(segmento_cliente STRING)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Calcula los beneficios aplicables para la próxima compra de un cliente basándose en su segmento (VIP, Recurrente, Nuevo). Retorna el % de descuento y si tiene envío gratis.'
AS $$
    segmento = segmento_cliente.strip().upper()
    
    if segmento == "VIP":
        return "El cliente tiene 20% de descuento en toda la tienda y envío GRATIS prioritario."
    elif segmento == "RECURRENTE":
        return "El cliente tiene 10% de descuento en compras mayores a $50 y envío estándar a mitad de precio."
    elif segmento == "NUEVO":
        return "El cliente tiene un cupón de 5% de descuento de bienvenida (código: BIENVENIDA5). El envío se cobra a tarifa normal."
    else:
        return "Segmento no reconocido. Sin beneficios aplicables."
$$
""")

print("Tool 3 (Python) creada: calcular_beneficios_segmento")

# COMMAND ----------
print("¡Las 3 herramientas (Tools) han sido registradas exitosamente en Unity Catalog!")

# COMMAND ----------
# Comprobar el perfil con un correo real de Gold y la columna email añadida.
muestra = spark.table(f"{CATALOG}.{SCHEMA}.gold_clientes_resumen").select("email", "segmento").first()
if muestra is None:
    raise RuntimeError("Gold no tiene clientes para probar la herramienta de perfil.")
correo_sql = muestra.email.replace("'", "''")
perfil_prueba = spark.sql(
    f"SELECT * FROM {CATALOG}.{SCHEMA}.consultar_perfil_cliente('{correo_sql}')"
).first()
if perfil_prueba is None or perfil_prueba.email != muestra.email or perfil_prueba.segmento != muestra.segmento:
    raise RuntimeError("El perfil consultado no coincide con el correo y segmento de Gold.")
print("Perfil verificado con Gold:", perfil_prueba)
