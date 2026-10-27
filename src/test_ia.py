"""Prueba de la configuracion del proveedor de IA (vault.get_client, vault.pedir_estructurado y su modo de respaldo JSON)
con un cliente SIMULADO: no llama a ningun servicio ni necesita ninguna clave.

Lo que se comprueba es que src/ no esta atado a OpenAI: el mismo codigo funciona con cualquier servidor compatible con su
API (Ollama, LM Studio, OpenRouter, Azure...) y con modelos que no soportan la salida estructurada nativa.

Uso (desde src/):  python test_ia.py
"""

import os
import sys
import types

from pydantic import BaseModel

import vault

ENTORNO = ("CEREBRO_MODELO", "CEREBRO_BASE_URL", "CEREBRO_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_KEY", "CEREBRO_SALIDA",
           "CEREBRO_EMBEDDINGS_BASE_URL", "CEREBRO_EMBEDDINGS_API_KEY", "CEREBRO_MODELO_EMBEDDINGS")
GET_CLIENT_REAL = vault.get_client


class Saludo(BaseModel):
    texto: str
    veces: int


def limpiar_entorno() -> None:
    for nombre in ENTORNO:
        os.environ.pop(nombre, None)
    vault._clients.clear()
    vault.get_client = GET_CLIENT_REAL


def esperar(excepcion, funcion, *args):
    try:
        funcion(*args)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


class OpenAIFalso:
    """Sustituye a openai.OpenAI: solo anota con que se creo."""
    creados: list[tuple] = []

    def __init__(self, api_key=None, base_url=None):
        OpenAIFalso.creados.append((api_key, base_url))


class Completaciones:
    def __init__(self, contenidos=()):
        self.contenidos = list(contenidos)
        self.llamadas: list[tuple[str, dict]] = []

    def parse(self, **kw):
        self.llamadas.append(("parse", kw))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(parsed=Saludo(texto="hola", veces=2)))])

    def create(self, **kw):
        self.llamadas.append(("create", kw))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=self.contenidos.pop(0)))])


def cliente_con(completaciones: Completaciones):
    return types.SimpleNamespace(chat=types.SimpleNamespace(completions=completaciones))


def probar_cliente() -> None:
    sys.modules["openai"] = types.SimpleNamespace(OpenAI=OpenAIFalso)
    try:
        limpiar_entorno()
        assert "OPENAI_API_KEY" in esperar(RuntimeError, vault.get_client)                     # sin clave ni servidor propio: error claro
        os.environ["OPENAI_API_KEY"] = "sk-openai"
        vault.get_client()
        assert OpenAIFalso.creados[-1] == ("sk-openai", None)                                   # como siempre: solo la clave de OpenAI
        os.environ["CEREBRO_API_KEY"] = "clave-cerebro"
        vault._clients.clear()
        vault.get_client()
        assert OpenAIFalso.creados[-1] == ("clave-cerebro", None)                               # CEREBRO_* manda sobre OPENAI_*
        print("1. clave: OPENAI_API_KEY como siempre, CEREBRO_API_KEY la sustituye, y sin ninguna hay un error que dice cual definir -- OK")

        limpiar_entorno()
        os.environ["CEREBRO_BASE_URL"] = "http://localhost:11434/v1"                             # p. ej. Ollama: no pide clave
        vault.get_client()
        assert OpenAIFalso.creados[-1] == ("sin-clave", "http://localhost:11434/v1")
        limpiar_entorno()
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        os.environ["OPENAI_API_KEY"] = "sk-x"
        vault.get_client()
        assert OpenAIFalso.creados[-1] == ("sk-x", "https://openrouter.ai/api/v1")
        print("2. servidor propio: CEREBRO_BASE_URL u OPENAI_BASE_URL apuntan a cualquier servidor compatible, y uno local no exige clave -- OK")

        limpiar_entorno()
        os.environ.update({"CEREBRO_BASE_URL": "https://chat.ejemplo/v1", "CEREBRO_API_KEY": "k-chat"})
        antes = len(OpenAIFalso.creados)
        assert vault.get_client() is vault.get_client() and len(OpenAIFalso.creados) == antes + 1           # un cliente por rol, reutilizado
        vault.get_client("embeddings")
        assert OpenAIFalso.creados[-1] == ("k-chat", "https://chat.ejemplo/v1")                              # sin variables propias: las mismas
        vault._clients.clear()
        os.environ.update({"CEREBRO_EMBEDDINGS_BASE_URL": "https://emb.ejemplo/v1", "CEREBRO_EMBEDDINGS_API_KEY": "k-emb"})
        vault.get_client("embeddings")
        vault.get_client()
        assert OpenAIFalso.creados[-2:] == [("k-emb", "https://emb.ejemplo/v1"), ("k-chat", "https://chat.ejemplo/v1")]
        print("3. el modelo de chat y el de embeddings pueden ser de proveedores distintos (CEREBRO_EMBEDDINGS_*) -- OK")
    finally:
        limpiar_entorno()
        del sys.modules["openai"]


def probar_salida() -> None:
    limpiar_entorno()
    completaciones = Completaciones()
    vault.get_client = lambda para="llm": cliente_con(completaciones)
    try:
        assert vault.pedir_estructurado("sistema", "usuario", Saludo) == Saludo(texto="hola", veces=2)
        tipo, kw = completaciones.llamadas[-1]
        assert tipo == "parse" and kw["model"] == "gpt-4o" and kw["response_format"] is Saludo            # por defecto: como siempre
        os.environ["CEREBRO_MODELO"] = "mi-modelo-local"
        vault.pedir_estructurado(None, "usuario", Saludo)
        assert completaciones.llamadas[-1][1]["model"] == "mi-modelo-local" and completaciones.llamadas[-1][1]["messages"] == [{"role": "user", "content": "usuario"}]
        print("4. salida estructurada nativa por defecto, y CEREBRO_MODELO cambia el modelo sin tocar el codigo -- OK")

        os.environ["CEREBRO_SALIDA"] = "json"
        completaciones.contenidos = ['Claro:\n```json\n{"texto": "hola", "veces": 2}\n```\nListo.']
        assert vault.pedir_estructurado("Eres un asistente.", "usuario", Saludo) == Saludo(texto="hola", veces=2)
        tipo, kw = completaciones.llamadas[-1]
        assert tipo == "create" and kw["response_format"] == {"type": "json_object"}
        sistema = kw["messages"][0]["content"]
        assert sistema.startswith("Eres un asistente.") and "veces" in sistema and "JSON" in sistema        # el esquema va en el prompt
        os.environ["CEREBRO_SALIDA"] = "texto"
        completaciones.contenidos = ['{"texto": "hola", "veces": 2}']
        vault.pedir_estructurado(None, "usuario", Saludo)
        assert "response_format" not in completaciones.llamadas[-1][1] and completaciones.llamadas[-1][1]["messages"][0]["role"] == "system"
        print("5. sin salida estructurada (CEREBRO_SALIDA=json|texto): el esquema va en el prompt y la respuesta, aunque venga con texto o ```, se valida aqui -- OK")

        antes = len(completaciones.llamadas)
        completaciones.contenidos = ["esto no es JSON", '{"texto": "x", "veces": "muchas"}', '{"texto": "ok", "veces": 3}']
        assert vault.pedir_estructurado(None, "usuario", Saludo) == Saludo(texto="ok", veces=3)
        assert len(completaciones.llamadas) == antes + 3                                                     # 2 reintentos, y los usa
        ultimo = completaciones.llamadas[-1][1]["messages"]
        assert ultimo[-1]["role"] == "user" and "no es valida" in ultimo[-1]["content"] and ultimo[-2] == {"role": "assistant", "content": '{"texto": "x", "veces": "muchas"}'}
        completaciones.contenidos = ["nada", "nada", "nada"]
        mensaje = esperar(ValueError, vault.pedir_estructurado, None, "usuario", Saludo)
        assert "Saludo" in mensaje and "3 intentos" in mensaje
        print("6. una respuesta invalida se corrige mostrandole el error al modelo (2 reintentos); si no, un error claro -- OK")

        os.environ["CEREBRO_SALIDA"] = "xml"
        assert "estructurada, json, texto" in esperar(ValueError, vault.pedir_estructurado, None, "usuario", Saludo)
        print("7. un valor invalido de CEREBRO_SALIDA da un error que lista los validos -- OK")
    finally:
        limpiar_entorno()


def probar_extraccion() -> None:
    assert vault._extraer_json('texto {"a": {"b": "}"}, "c": "com\\"illa"} y luego {"otro": 1}') == {"a": {"b": "}"}, "c": 'com"illa'}
    assert vault._extraer_json('{"x": [1, 2, {"y": "z"}]}') == {"x": [1, 2, {"y": "z"}]}
    assert "ningun objeto" in esperar(ValueError, vault._extraer_json, "sin json")
    assert "incompleto" in esperar(ValueError, vault._extraer_json, '{"a": "sin cerrar')
    print("8. _extraer_json: encuentra el objeto entre texto, respeta llaves y comillas dentro de cadenas, y rechaza lo incompleto -- OK")


def main() -> None:
    probar_cliente()
    probar_salida()
    probar_extraccion()
    print("TODO OK -- el proveedor de IA se configura por variables de entorno y funciona con o sin salida estructurada nativa.")


if __name__ == "__main__":
    main()
