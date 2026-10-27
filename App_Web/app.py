"""Databricks App: chat de E-commerce BeBot.

Consume el Model Serving endpoint del agente con DatabricksOpenAI —
client.responses.create(), el cliente correcto para un endpoint que sirve un
ResponsesAgent (no WorkspaceClient().serving_endpoints.query(), que asume
formato chat completions). Se autentica solo con la identidad de servicio de
la App, sin credenciales a mano.
"""

import os
import logging

import streamlit as st
from databricks_openai import DatabricksOpenAI

SERVING_ENDPOINT_NAME = os.environ.get(
    "SERVING_ENDPOINT_NAME", "ecommerce_agent_endpoint_v5"
)

PREGUNTAS_EJEMPLO = [
    "¿Cuál es el estado de mi pedido 15?",
    "Quiero consultar mi perfil de cliente. ¿Qué dato necesitas?",
    "¿Qué beneficios tengo por ser cliente VIP?",
    "¿Cuál es la política de envíos si mi producto llega dañado?",
    "¿Qué productos se incluyen en el pedido 15?",
]

st.set_page_config(page_title="BeBot E-commerce", page_icon="🛒", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background: #1a1a2e; }
    .bebot-header {
        background: linear-gradient(135deg, #e74c3c, #8e44ad);
        padding: 28px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
    }
    .bebot-header h1 { margin: 0; font-size: 26px; }
    .bebot-header p { margin: 6px 0 0 0; color: #ffeef0; font-size: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="bebot-header">
        <h1>🛒 BeBot - Asistente de E-commerce</h1>
        <p>Pedidos, clientes, beneficios VIP y políticas de la tienda.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_openai_client() -> DatabricksOpenAI:
    return DatabricksOpenAI()


def consultar_agente(mensajes: list[dict]) -> str:
    client = get_openai_client()
    respuesta = client.responses.create(
        model=SERVING_ENDPOINT_NAME,
        input=mensajes,
        stream=False,
    )
    if respuesta is None:
        raise RuntimeError(
            "El endpoint no devolvió una respuesta compatible con Responses API. "
            "Comprueba la versión desplegada con 07_Diagnostico_Endpoint.py y "
            "registra el agente con el archivo 04 actualizado."
        )
    if respuesta.error:
        raise RuntimeError(f"El agente devolvió un error: {respuesta.error.message}")
    texto = respuesta.output_text
    if not texto or not texto.strip():
        raise RuntimeError(
            "El agente devolvió una respuesta sin texto. Revisa las trazas del endpoint."
        )
    return texto


with st.sidebar:
    st.subheader("Preguntas de ejemplo")
    for pregunta in PREGUNTAS_EJEMPLO:
        if st.button(pregunta, use_container_width=True):
            st.session_state.setdefault("mensajes", [])
            st.session_state["pregunta_pendiente"] = pregunta
    if st.button("Nueva conversación"):
        st.session_state.mensajes = []
        st.session_state.contexto_agente = []
        st.session_state.pop("pregunta_pendiente", None)

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "contexto_agente" not in st.session_state:
    st.session_state.contexto_agente = []

for mensaje in st.session_state.mensajes:
    avatar = "🧑‍💼" if mensaje["role"] == "user" else "🛒"
    with st.chat_message(mensaje["role"], avatar=avatar):
        if mensaje.get("error"):
            st.error(mensaje["content"])
        else:
            st.markdown(mensaje["content"])

texto_escrito = st.chat_input(
    "Escribe tu pregunta y presiona Enter o la flecha para enviarla",
    key="entrada_chat",
)
pregunta_ejemplo = st.session_state.pop("pregunta_pendiente", None)
pregunta = texto_escrito or pregunta_ejemplo

if pregunta:
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(pregunta)

    with st.chat_message("assistant", avatar="🛒"):
        fallo = False
        with st.spinner("Consultando al agente..."):
            try:
                contexto = st.session_state.contexto_agente + [
                    {"role": "user", "content": pregunta}
                ]
                respuesta_texto = consultar_agente(contexto)
            except Exception:
                logging.exception("Fallo consultando el endpoint %s", SERVING_ENDPOINT_NAME)
                fallo = True
                respuesta_texto = (
                    "No pude completar la consulta en este momento. Inténtalo nuevamente. "
                    "Si el problema continúa, contacta al soporte."
                )
        if fallo:
            st.error(respuesta_texto)
        else:
            st.markdown(respuesta_texto)
            st.session_state.contexto_agente = contexto + [
                {"role": "assistant", "content": respuesta_texto}
            ]

    st.session_state.mensajes.append(
        {"role": "assistant", "content": respuesta_texto, "error": fallo}
    )
