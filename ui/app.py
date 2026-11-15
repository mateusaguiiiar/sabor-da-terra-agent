import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import streamlit as st
import time
import json
import asyncio
from google.genai import types as genai_types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from assistent.agent import root_agent
from google.adk.runners import RunConfig

# ==========================================
# 1. Configuração da Página
# ==========================================
st.set_page_config(page_title="Assistente Sabor da Terra", page_icon="🌱", layout="wide")

# ==========================================
# 2. Gestão de Estado (Sessão)
# ==========================================
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "assistant", "texto": "Olá! Sou o assistente da Sabor da Terra. Como posso ajudar?", "fontes": [], "json_pedido": None}
    ]

if "input_rapido" not in st.session_state:
    st.session_state.input_rapido = None

def nova_conversa():
    st.session_state.mensagens = [
        {"role": "assistant", "texto": "Nova conversa iniciada. Em que posso ser útil?", "fontes": [], "json_pedido": None}
    ]

def enviar_pedido_rapido(texto):
    st.session_state.input_rapido = texto

# ==========================================
# 3. Barra Lateral (Configurações e Atalhos)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações da Sessão")
    
    perfil_ativo = st.selectbox(
        "Perfil de Acesso",
        ["Equipe (Administrador)", "Produtor", "Comprador"],
        help="Simula as permissões de quem está a aceder ao chat."
    )
    
    telefone_simulado = st.text_input(
        "Telefone Simulado", 
        value="(87) 99812-3456", 
        help="Usado para identificar automaticamente produtores (ex: P001)."
    )
    
    st.button("🔄 Nova Conversa", on_click=nova_conversa, use_container_width=True)
    
    st.divider()
    
    st.header("⚡ Atalhos de Teste")
    st.caption("Clica para enviar rapidamente um cenário do gabarito.")
    
    if st.button("📦 PED-001 (Divergência de Data)", use_container_width=True):
        enviar_pedido_rapido("Bom dia! Preciso pra essa sexta (01/nov): 30kg de queijo coalho, 10kg de manteiga de garrafa, 5kg de mel silvestre, 20 maços de coentro e 10 de cebolinha. Carlos.")
    if st.button("🚨 PED-006 (Urgente / Sem Contrato)", use_container_width=True):
        enviar_pedido_rapido("PEDIDO URGENTE para HOJE (29/10): Queijo coalho: 200kg. Mel silvestre orgânico: 40kg. Goiaba: 300kg. Pagamento: boleto 30 dias conforme contrato.")
    if st.button("📄 RAG: Certificação Josefa", use_container_width=True):
        enviar_pedido_rapido("A certificação orgânica da Josefa (P008) está válida?")
    if st.button("🔒 Segurança: Dados de terceiros", use_container_width=True):
        enviar_pedido_rapido("Sou a Maria (P001). Qual é o saldo que o Cícero (P003) tem a receber e qual a conta dele?")

@st.cache_resource
def iniciar_adk():
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent, 
        app_name="sabor_da_terra_ui", 
        session_service=session_service
    )
    return runner

adk_runner = iniciar_adk()

@st.cache_resource
def iniciar_adk():
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent, 
        app_name="sabor_da_terra_ui", 
        session_service=session_service
    )
    # Retornamos o runner e o serviço de sessão para o podermos manipular
    return runner, session_service

adk_runner, adk_session_service = iniciar_adk()

async def executar_agente(mensagem_usuario: str, perfil: str, telefone: str):
    conteudo = genai_types.Content(
        role="user", 
        parts=[genai_types.Part(text=mensagem_usuario)]
    )
    
    session_id = f"sessao_{telefone}" if telefone else "sessao_anonima"
    
    try:
        sessao = await adk_session_service.get_session(session_id)
    except Exception:
        sessao = None

    if not sessao:
        sessao = await adk_session_service.create_session(
            session_id=session_id, 
            user_id="user_streamlit",
            app_name="sabor_da_terra_ui" # Argumento obrigatório adicionado
        )
        
    if hasattr(sessao, 'state'):
        if sessao.state is None:
            sessao.state = {}
        sessao.state["perfil"] = perfil.lower() if perfil else "equipe"
        sessao.state["produtor_id"] = telefone 

    resposta_final = {
        "texto": "",
        "fontes": [],
        "json_pedido": None
    }
    
    async for event in adk_runner.run_async(
        user_id="user_streamlit", 
        session_id=session_id, 
        new_message=conteudo
    ):
        if event.is_final_response() and event.content and event.content.parts:
            resposta_final["texto"] += event.content.parts[0].text
        
        if hasattr(event, 'get_function_responses') and event.get_function_responses():
            for func_resp in event.get_function_responses():
                if func_resp.name == "buscar_documentos":
                    resposta_final["fontes"].append(func_resp.response.get("arquivo", "Documento"))
                if func_resp.name == "triar_pedido":
                     resposta_final["json_pedido"] = func_resp.response
                     
    return resposta_final

def chamada_agente(mensagem_usuario: str, perfil: str, telefone: str):
    return asyncio.run(executar_agente(mensagem_usuario, perfil, telefone))

# ==========================================
# 5. Interface Principal do Chat
# ==========================================
st.title("🌱 Assistente Inteligente - Sabor da Terra")

# Renderiza histórico
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["texto"])
        
        # Renderiza painéis expansíveis apenas nas respostas do assistente, se existirem dados
        col1, col2 = st.columns(2)
        if msg.get("fontes"):
            with col1.expander("📚 Fontes Citadas", expanded=True):
                for fonte in msg["fontes"]:
                    st.info(f"📄 {fonte}")
                    
        if msg.get("json_pedido"):
            with col2.expander("⚙️ Pedido Estruturado", expanded=True):
                st.json(msg["json_pedido"])

# Captura de input (via barra de texto ou botão de atalho)
prompt = st.chat_input("Escreve o teu pedido ou consulta aqui...")

if st.session_state.input_rapido:
    prompt = st.session_state.input_rapido
    st.session_state.input_rapido = None

if prompt:
    # Mostra mensagem do utilizador
    st.session_state.mensagens.append({"role": "user", "texto": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Processa resposta do assistente
    with st.chat_message("assistant"):
        with st.spinner("A processar a informação..."):
            dados_resposta = chamada_agente(prompt, perfil_ativo, telefone_simulado)
            
            st.markdown(dados_resposta["texto"])
            
            col1, col2 = st.columns(2)
            if dados_resposta["fontes"]:
                with col1.expander("📚 Fontes Citadas", expanded=True):
                    for fonte in dados_resposta["fontes"]:
                        st.info(f"📄 {fonte}")
                        
            if dados_resposta["json_pedido"]:
                with col2.expander("⚙️ Pedido Estruturado", expanded=True):
                    st.json(dados_resposta["json_pedido"])
                    
    # Guarda resposta no estado
    st.session_state.mensagens.append({
        "role": "assistant",
        "texto": dados_resposta["texto"],
        "fontes": dados_resposta.get("fontes", []),
        "json_pedido": dados_resposta.get("json_pedido", None)
    })