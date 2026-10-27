# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Ingestión RAG y Vector Search
# MAGIC Este notebook lee los PDFs de la tienda desde un Volumen, los divide en fragmentos (chunks), 
# MAGIC guarda los chunks en una tabla Delta, y finalmente crea un Índice de Vector Search.

# COMMAND ----------
# MAGIC %pip install databricks-vectorsearch langchain langchain-core langchain-community langchain-text-splitters pypdf unstructured "protobuf>=6.33.5"

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

CATALOG = "workspace"
SCHEMA = "reto_ecommerce"
VOLUME = "pdfs_ecommerce"
TABLA_CHUNKS = f"{CATALOG}.{SCHEMA}.documentos_chunks"

# Ruta del volumen en Databricks
ruta_volumen = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

print(f"Leyendo PDFs desde: {ruta_volumen}")

# 1. Cargar PDFs usando LangChain
loader = PyPDFDirectoryLoader(ruta_volumen)
documentos = loader.load()

print(f"Se cargaron {len(documentos)} páginas en total.")

# COMMAND ----------

# 2. Dividir el texto en Chunks (Fragmentos)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " ", ""]
)

chunks = text_splitter.split_documents(documentos)
print(f"Se generaron {len(chunks)} chunks.")

# 3. Preparar los datos para la tabla Delta
datos_chunks = []
for i, chunk in enumerate(chunks):
    # Extraer el nombre del archivo de la metadata
    fuente = chunk.metadata.get("source", "desconocido").split("/")[-1]
    
    datos_chunks.append({
        "id_chunk": f"chunk_{i}",
        "fuente": fuente,
        "contenido": chunk.page_content
    })

df_chunks = spark.createDataFrame(pd.DataFrame(datos_chunks))

# Guardar como tabla Delta
df_chunks.write.mode("overwrite").saveAsTable(TABLA_CHUNKS)

# Habilitar Change Data Feed (Requisito para Vector Search)
spark.sql(f"ALTER TABLE {TABLA_CHUNKS} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

print(f"Tabla de chunks guardada exitosamente en {TABLA_CHUNKS} con Change Data Feed habilitado.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Creación del Endpoint y el Índice de Vector Search
# MAGIC Para esto usaremos el SDK de Databricks. (NOTA: Crear el endpoint puede tardar unos 10-15 minutos si no existe uno previo).

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()

# Nombre de nuestro endpoint e índice
ENDPOINT_NAME = "ecommerce_vs_endpoint"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.indice_documentos_ecommerce"

# 1. Verificar si el endpoint existe, si no, crearlo
endpoints_existentes = [e["name"] for e in vsc.list_endpoints().get("endpoints", [])]

if ENDPOINT_NAME not in endpoints_existentes:
    print(f"Creando endpoint de Vector Search '{ENDPOINT_NAME}'... Esto puede tardar 10-15 min.")
    vsc.create_endpoint(name=ENDPOINT_NAME, endpoint_type="STANDARD")
else:
    print(f"El endpoint '{ENDPOINT_NAME}' ya existe.")

# Esperar a que el endpoint esté listo
print("Esperando a que el endpoint esté ONLINE...")
vsc.wait_get_endpoint_cluster_ready(ENDPOINT_NAME)
print("¡Endpoint ONLINE y listo!")

# COMMAND ----------

# 2. Crear el índice vectorial (Usando el modelo BGE embebido de Databricks que es gratuito/incluido)
# Nota: "databricks-bge-large-en" es el modelo de embedding por defecto en Databricks Serverless
indices_existentes = [i["name"] for i in vsc.list_indexes(ENDPOINT_NAME).get("vector_indexes", [])]

if INDEX_NAME not in indices_existentes:
    print(f"Creando el índice '{INDEX_NAME}'... Esto tardará un par de minutos.")
    vsc.create_delta_sync_index(
        endpoint_name=ENDPOINT_NAME,
        source_table_name=TABLA_CHUNKS,
        index_name=INDEX_NAME,
        pipeline_type="TRIGGERED",
        primary_key="id_chunk",
        embedding_source_column="contenido",
        embedding_model_endpoint_name="databricks-bge-large-en"
    )
else:
    print(f"El índice '{INDEX_NAME}' ya existe.")
    print("Sincronizando índice con los últimos datos...")
    vsc.get_index(ENDPOINT_NAME, INDEX_NAME).sync()

print("¡Proceso de Vector Search completado!")
print(f"Tu índice para el RAG es: {INDEX_NAME}")
