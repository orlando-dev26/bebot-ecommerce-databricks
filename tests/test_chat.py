"""Pruebas locales de regresión, sin llamadas ni credenciales de Databricks."""
import ast
import logging
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace
from typing import Generator
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]

class State(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc
    def __setattr__(self, name, value):
        self[name] = value

class Context:
    def __enter__(self): return self
    def __exit__(self, *args): return False

class FakeStreamlit(ModuleType):
    def __init__(self, state, clicked=None, typed=None):
        super().__init__("streamlit")
        self.session_state = state
        self.sidebar = Context()
        self.clicked, self.typed = clicked, typed
        self.input_count = 0
        self.errors = []
    def set_page_config(self, **kwargs): pass
    def markdown(self, *args, **kwargs): pass
    def subheader(self, *args): pass
    def button(self, text, **kwargs): return text == self.clicked
    def chat_message(self, *args, **kwargs): return Context()
    def spinner(self, *args): return Context()
    def cache_resource(self, fn): return fn
    def chat_input(self, *args, **kwargs):
        self.input_count += 1
        return self.typed
    def error(self, text): self.errors.append(text)

class ChatTests(unittest.TestCase):
    def run_app(self, state, response, clicked=None, typed=None):
        st = FakeStreamlit(state, clicked, typed)
        calls = []
        def create(**kwargs):
            calls.append(kwargs)
            if isinstance(response, Exception): raise response
            return response
        sdk = ModuleType("databricks_openai")
        sdk.DatabricksOpenAI = lambda: SimpleNamespace(responses=SimpleNamespace(create=create))
        with patch.dict(sys.modules, {"streamlit": st, "databricks_openai": sdk}), patch.object(logging, "exception"):
            runpy.run_path(str(BASE / "App_Web/app.py"))
        return st, calls
    def ok(self, text="Respuesta real"):
        return SimpleNamespace(error=None, output_text=text)
    def test_input_present_when_example_clicked(self):
        state = State()
        st, calls = self.run_app(state, self.ok(), clicked="¿Cuál es el estado de mi pedido 15?")
        self.assertEqual(st.input_count, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["input"][0]["content"], "¿Cuál es el estado de mi pedido 15?")
    def test_typed_question_and_history_sent(self):
        state = State()
        self.run_app(state, self.ok("El pedido está enviado"), typed="Consulta el pedido 15")
        st, calls = self.run_app(state, self.ok(), typed="¿Qué productos incluye?")
        self.assertEqual([m["role"] for m in calls[0]["input"]], ["user", "assistant", "user"])
        self.assertEqual(st.input_count, 1)
        self.assertEqual(len(state.contexto_agente), 4)
    def test_none_is_error_and_not_sent_as_context(self):
        state = State()
        st, calls = self.run_app(state, None, typed="Hola")
        self.assertIn("No pude completar", st.errors[0])
        self.assertEqual(state.contexto_agente, [])
        self.assertTrue(state.mensajes[-1]["error"])
        _, calls = self.run_app(state, self.ok(), typed="Reintento")
        self.assertEqual(calls[0]["input"], [{"role": "user", "content": "Reintento"}])
    def test_empty_response_is_not_success(self):
        state = State()
        st, _ = self.run_app(state, self.ok("  "), typed="Hola")
        self.assertTrue(st.errors)
        self.assertEqual(state.contexto_agente, [])
    def test_service_error_keeps_input_available(self):
        st, _ = self.run_app(State(), RuntimeError("Permission denied"), typed="Hola")
        self.assertEqual(st.input_count, 1)
        self.assertNotIn("Permission denied", st.errors[0])
        self.assertIn("No pude completar", st.errors[0])
    def test_new_conversation_clears_context(self):
        state = State(mensajes=[{"role":"user", "content":"Anterior"}], contexto_agente=[{"role":"user", "content":"Anterior"}])
        st, calls = self.run_app(state, self.ok(), clicked="Nueva conversación")
        self.assertEqual(state.mensajes, [])
        self.assertEqual(state.contexto_agente, [])
        self.assertEqual(calls, [])
        self.assertEqual(st.input_count, 1)

class AgentTests(unittest.TestCase):
    def test_missing_arguments_do_not_invoke_uc(self):
        tree = ast.parse((BASE / "agente_ecommerce_template.py").read_text(encoding="utf-8"))
        funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in {"validar_argumentos", "proteger_tool"}]
        ns = {"StructuredTool": SimpleNamespace(from_function=lambda **kw: kw["func"])}
        exec(compile(ast.Module(body=funcs, type_ignores=[]), "tool_guard", "exec"), ns)
        calls = []
        original = SimpleNamespace(name="workspace__reto__consultar_perfil_cliente",
            description="Perfil", args_schema=object,
            invoke=lambda args: calls.append(args) or "Perfil real")
        tool = ns["proteger_tool"](original)
        for args in ({}, {"correo": None}, {"correo": ""}, {"correo": "  "}):
            self.assertIn("correo", tool(**args))
        self.assertEqual(calls, [])
        self.assertEqual(tool(correo="cliente@example.com"), "Perfil real")
        self.assertEqual(calls, [{"correo": "cliente@example.com"}])
        for pedido in (None, 0, -1, True):
            self.assertIsNotNone(ns["validar_argumentos"]("consultar_estado_pedido", {"id_pedido": pedido}))
        self.assertIsNone(ns["validar_argumentos"]("consultar_estado_pedido", {"id_pedido": 15}))
        for segmento in ("VIP", "Recurrente", "Nuevo"):
            self.assertIsNone(ns["validar_argumentos"]("calcular_beneficios_segmento", {"segmento_cliente": segmento}))
        for args in ({}, {"segmento_cliente": None}, {"segmento_cliente": ""}):
            self.assertIsNotNone(ns["validar_argumentos"]("calcular_beneficios_segmento", args))

    def test_wrapper_preserves_history_and_returns_output_items(self):
        tree = ast.parse((BASE / "agente_ecommerce_template.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        sent = []
        class Graph:
            def stream(self, data, **kwargs):
                sent.append(data)
                yield "updates", {"agent": {"messages": ["respuesta final"]}}
        def output_events(messages):
            for text in messages:
                yield SimpleNamespace(type="response.output_item.done", item={"type":"message", "text":text})
        ns = {"ResponsesAgent": object, "ResponsesAgentRequest": object,
              "ResponsesAgentResponse": lambda **kw: kw, "ResponsesAgentStreamEvent": object,
              "Generator": Generator, "to_chat_completions_input": lambda items: items,
              "output_to_responses_items_stream": output_events}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), "agent_wrapper", "exec"), ns)
        messages = [{"role":"user", "content":"Pedido 15"}, {"role":"assistant", "content":"Enviado"}, {"role":"user", "content":"¿Productos?"}]
        request = SimpleNamespace(input=[SimpleNamespace(model_dump=lambda m=m:m) for m in messages], custom_inputs=None)
        result = ns[cls.name](Graph()).predict(request)
        self.assertEqual(sent[0]["messages"], messages)
        self.assertEqual(result["output"][0]["text"], "respuesta final")

if __name__ == "__main__": unittest.main()
