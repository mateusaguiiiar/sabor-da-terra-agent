import asyncio
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from assistent.agent import root_agent
from tools import dados

APP_NAME = "sabor_da_terra_ui"
USER_ID = "user_streamlit"

# ==========================================
# 1. Configuração da Página
# ==========================================
st.set_page_config(page_title="Assistente Sabor da Terra", page_icon="🌱", layout="wide")

# ==========================================
# 2. Gestão de Estado (Sessão)
# ==========================================
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {
            "role": "assistant",
            "texto": "Olá! Sou o assistente da Sabor da Terra. Como posso ajudar?",
            "fontes": [],
            "json_pedido": None,
        }
    ]

if "input_rapido" not in st.session_state:
    st.session_state.input_rapido = None

if "session_nonce" not in st.session_state:
    st.session_state.session_nonce = 0


def nova_conversa():
    st.session_state.session_nonce += 1
    st.session_state.mensagens = [
        {
            "role": "assistant",
            "texto": "Nova conversa iniciada. Em que posso ser útil?",
            "fontes": [],
            "json_pedido": None,
        }
    ]


def enviar_pedido_rapido(texto):
    st.session_state.input_rapido = texto


def normalizar_perfil(perfil_label: str) -> str:
    mapa = {
        "Equipe (Administrador)": "equipe",
        "Produtor": "produtor",
        "Comprador": "comprador",
    }
    return mapa.get(perfil_label, "equipe")


def resolver_produtor_id(identificador: str) -> str:
    valor = (identificador or "").strip()
    if not valor:
        return ""
    if re.fullmatch(r"[Pp]\d{3}", valor):
        return valor.upper()

    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return ""

    try:
        df = dados.produtores()
        for _, row in df.iterrows():
            for cell in row.values:
                if digitos in re.sub(r"\D", "", str(cell)):
                    return str(row.get("id", "")).strip().upper()
    except Exception:
        pass
    return ""


# ==========================================
# 3. Barra Lateral (Configurações e Atalhos)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações da Sessão")

    perfil_ativo = st.selectbox(
        "Perfil de Acesso",
        ["Equipe (Administrador)", "Produtor", "Comprador"],
        help="Simula as permissões de quem está acessando o chat.",
    )

    telefone_simulado = st.text_input(
        "Telefone ou ID do Produtor",
        value="(87) 99812-3456",
        help="Usado para identificar produtores (ex: (87) 99812-3456 ou P001).",
    )

    st.button("🔄 Nova Conversa", on_click=nova_conversa, use_container_width=True)

    st.divider()

    st.header("⚡ Atalhos de Teste")
    st.caption("Clique para enviar rapidamente um cenário do gabarito.")

    if st.button("📦 PED-001 (Divergência de Data)", use_container_width=True):
        enviar_pedido_rapido(
            "Bom dia! Preciso pra essa sexta (01/nov): 30kg de queijo coalho, 10kg de manteiga de garrafa, 5kg de mel silvestre, 20 maços de coentro e 10 de cebolinha. Carlos."
        )
    if st.button("🚨 PED-006 (Urgente / Sem Contrato)", use_container_width=True):
        enviar_pedido_rapido(
            "PEDIDO URGENTE para HOJE (29/10): Queijo coalho: 200kg. Mel silvestre orgânico: 40kg. Goiaba: 300kg. Pagamento: boleto 30 dias conforme contrato."
        )
    if st.button("📄 RAG: Certificação Josefa", use_container_width=True):
        enviar_pedido_rapido("A certificação orgânica da Josefa (P008) está válida?")
    if st.button("🔒 Segurança: Dados de terceiros", use_container_width=True):
        enviar_pedido_rapido(
            "Sou a Maria (P001). Qual é o saldo que o Cícero (P003) tem a receber e qual a conta dele?"
        )


# ==========================================
# 4. Inicialização e Execução do ADK
# ==========================================
@st.cache_resource
def iniciar_adk():
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    return runner, session_service


adk_runner, adk_session_service = iniciar_adk()


async def executar_agente(mensagem_usuario: str, perfil: str, telefone: str, nonce: int):
    conteudo = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=mensagem_usuario)],
    )

    perfil_norm = normalizar_perfil(perfil)
    produtor_id = resolver_produtor_id(telefone)
    session_id = f"sessao_{perfil_norm}_{produtor_id or 'anon'}_{nonce}"

    sessao = await adk_session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    if not sessao:
        sessao = await adk_session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state={
                "perfil": perfil_norm,
                "produtor_id": produtor_id,
            },
        )

    resposta_final = {
        "texto": "",
        "fontes": [],
        "json_pedido": None,
    }

    async for event in adk_runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=conteudo,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    resposta_final["texto"] += part.text

        if hasattr(event, "get_function_responses") and event.get_function_responses():
            for func_resp in event.get_function_responses():
                resp = func_resp.response or {}
                if func_resp.name == "buscar_documentos" and isinstance(resp, dict):
                    trechos = resp.get("trechos") or resp.get("resultados") or []
                    if isinstance(trechos, list) and trechos:
                        for t in trechos:
                            if isinstance(t, dict) and t.get("arquivo"):
                                if t["arquivo"] not in resposta_final["fontes"]:
                                    resposta_final["fontes"].append(t["arquivo"])
                    elif resp.get("arquivo"):
                        resposta_final["fontes"].append(resp["arquivo"])
                if func_resp.name == "triar_pedido":
                    resposta_final["json_pedido"] = resp

    return resposta_final


def chamada_agente(mensagem_usuario: str, perfil: str, telefone: str, nonce: int):
    return asyncio.run(executar_agente(mensagem_usuario, perfil, telefone, nonce))


# ==========================================
# 5. Interface Principal do Chat
# ==========================================
st.title("🌱 Assistente Inteligente - Sabor da Terra")

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["texto"])

        col1, col2 = st.columns(2)
        if msg.get("fontes"):
            with col1.expander("📚 Fontes Citadas", expanded=True):
                for fonte in msg["fontes"]:
                    st.info(f"📄 {fonte}")

        if msg.get("json_pedido"):
            with col2.expander("⚙️ Pedido Estruturado", expanded=True):
                st.json(msg["json_pedido"])

prompt = st.chat_input("Escreva seu pedido ou consulta aqui...")

if st.session_state.input_rapido:
    prompt = st.session_state.input_rapido
    st.session_state.input_rapido = None

if prompt:
    st.session_state.mensagens.append({"role": "user", "texto": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processando a informação..."):
            dados_resposta = chamada_agente(
                prompt,
                perfil_ativo,
                telefone_simulado,
                st.session_state.session_nonce,
            )

            st.markdown(dados_resposta["texto"])

            col1, col2 = st.columns(2)
            if dados_resposta["fontes"]:
                with col1.expander("📚 Fontes Citadas", expanded=True):
                    for fonte in dados_resposta["fontes"]:
                        st.info(f"📄 {fonte}")

            if dados_resposta["json_pedido"]:
                with col2.expander("⚙️ Pedido Estruturado", expanded=True):
                    st.json(dados_resposta["json_pedido"])

    st.session_state.mensagens.append(
        {
            "role": "assistant",
            "texto": dados_resposta["texto"],
            "fontes": dados_resposta.get("fontes", []),
            "json_pedido": dados_resposta.get("json_pedido", None),
        }
    )