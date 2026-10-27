# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Pipeline Medallion (Silver y Gold)
# MAGIC Este notebook transforma las tablas Bronze de E-commerce (creadas por el setup) en tablas Silver (limpias) y tablas Gold (consolidadas para el Agente).

# COMMAND ----------

# Variables de entorno (Asegúrate de que sean las mismas que usaste en el setup)
CATALOG = "workspace"
SCHEMA = "reto_ecommerce"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Creación de Tablas Silver (Limpieza básica)

# COMMAND ----------

from pyspark.sql.functions import col, upper, trim, round

# 1.1 Silver Clientes (Estandarizar correos y nombres)
df_clientes = spark.table("bronze_clientes")
df_clientes_silver = df_clientes.withColumn("nombre", upper(trim(col("nombre")))) \
                                .withColumn("email", trim(col("email")))

df_clientes_silver.write.mode("overwrite").saveAsTable("silver_clientes")

# 1.2 Silver Productos (Precios redondeados y nombres limpios)
df_productos = spark.table("bronze_productos")
df_productos_silver = df_productos.withColumn("nombre", trim(col("nombre"))) \
                                  .withColumnRenamed("nombre", "nombre_producto") \
                                  .withColumn("precio", round(col("precio"), 2))

df_productos_silver.write.mode("overwrite").saveAsTable("silver_productos")

# 1.3 Silver Pedidos (Estandarizar estado)
df_pedidos = spark.table("bronze_pedidos")
df_pedidos_silver = df_pedidos.withColumn("estado", upper(trim(col("estado")))) \
                              .withColumn("total", round(col("total"), 2))

df_pedidos_silver.write.mode("overwrite").saveAsTable("silver_pedidos")

# 1.4 Silver Detalle Pedidos
df_detalle = spark.table("bronze_detalle_pedidos")
df_detalle_silver = df_detalle.withColumn("precio_unitario", round(col("precio_unitario"), 2))
df_detalle_silver.write.mode("overwrite").saveAsTable("silver_detalle_pedidos")

# 1.5 Silver Reviews
df_reviews = spark.table("bronze_reviews")
df_reviews_silver = df_reviews.withColumn("comentario", trim(col("comentario")))
df_reviews_silver.write.mode("overwrite").saveAsTable("silver_reviews")

print("Tablas Silver creadas exitosamente.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Creación de Tablas Gold (Vistas de Negocio para el Agente)

# COMMAND ----------

# 2.1 Gold: Resumen de Clientes (Útil para tool de perfil de cliente)
# Queremos saber el total gastado por el cliente y su cantidad de pedidos
gold_clientes_resumen = spark.sql(f"""
    SELECT 
        c.cliente_id,
        c.nombre,
        c.email,
        c.ciudad,
        c.segmento,
        COUNT(p.pedido_id) as total_pedidos,
        SUM(p.total) as total_gastado
    FROM silver_clientes c
    LEFT JOIN silver_pedidos p ON c.cliente_id = p.cliente_id
    GROUP BY c.cliente_id, c.nombre, c.email, c.ciudad, c.segmento
""")
gold_clientes_resumen.write.mode("overwrite").saveAsTable("gold_clientes_resumen")

# 2.2 Gold: Estado de Pedidos Consolidado (Útil para tool de estado de pedido)
# Queremos el pedido, cliente asociado y los items comprados
gold_pedidos_estado = spark.sql(f"""
    SELECT 
        p.pedido_id,
        p.fecha_pedido,
        p.estado,
        p.total as total_pedido,
        c.nombre as cliente_nombre,
        c.email as cliente_email,
        collect_list(prod.nombre_producto) as productos_incluidos
    FROM silver_pedidos p
    JOIN silver_clientes c ON p.cliente_id = c.cliente_id
    JOIN silver_detalle_pedidos d ON p.pedido_id = d.pedido_id
    JOIN silver_productos prod ON d.producto_id = prod.producto_id
    GROUP BY p.pedido_id, p.fecha_pedido, p.estado, p.total, c.nombre, c.email
""")
gold_pedidos_estado.write.mode("overwrite").saveAsTable("gold_pedidos_estado")

# 2.3 Gold: Inventario y Reviews (Útil para tool de consulta de productos)
gold_productos_stock = spark.sql(f"""
    SELECT 
        p.producto_id,
        p.nombre_producto,
        p.categoria,
        p.precio,
        p.stock,
        AVG(r.puntaje) as puntaje_promedio,
        COUNT(r.review_id) as total_reviews
    FROM silver_productos p
    LEFT JOIN silver_reviews r ON p.producto_id = r.producto_id
    GROUP BY p.producto_id, p.nombre_producto, p.categoria, p.precio, p.stock
""")
gold_productos_stock.write.mode("overwrite").saveAsTable("gold_productos_stock")

print("Tablas Gold creadas exitosamente.")
