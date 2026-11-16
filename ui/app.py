import streamlit as st
import time
import json

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

# ==========================================
# 4. Mock do Agente (Estrutura Avançada)
# ==========================================
def agente_mock_resposta(mensagem_usuario, perfil, telefone):
    """Simula a devolução de um objeto complexo pelo orquestrador."""
    time.sleep(1.5) # Simula latência
    
    resposta = {
        "texto": "Recebi a tua mensagem. O backend real será ligado em breve.",
        "fontes": [],
        "json_pedido": None
    }
    
    mensagem_lower = mensagem_usuario.lower()
    
    if "certificação" in mensagem_lower and "josefa" in mensagem_lower:
        resposta["texto"] = "Não. A certificação orgânica da Josefa venceu em 30/09/2026. A renovação está protocolada, mas até à auditoria não pode vender como orgânico."
        resposta["fontes"] = ["cert_organica_josefa_souza_P008.txt (Secção: Dados do Produtor)"]
        
    elif "urgente" in mensagem_lower and "200kg" in mensagem_lower:
        resposta["texto"] = "⚠️ **Atenção:** Este pedido contém alertas críticos de negócio e exige revisão humana."
        resposta["json_pedido"] = {
            "tipo_mensagem": "pedido de compra",
            "urgencia": "alta (para hoje)",
            "itens": [{"produto": "queijo coalho", "qtd": 200}],
            "problemas_identificados": [
                "Volume (200kg) excede a capacidade diária padrão.",
                "Não existe contrato cadastrado para 'Rede SuperBom' (pagamento via boleto não validado)."
            ]
        }
        
    elif "saldo" in mensagem_lower and "cícero" in mensagem_lower:
        if perfil != "Equipa (Administrador)":
            resposta["texto"] = "🔒 **Acesso Negado:** Não tenho permissão para partilhar dados financeiros ou informações pessoais de outros produtores. Posso ajudar apenas com o teu próprio histórico de vendas."
        else:
            resposta["texto"] = "Como administrador, podes consultar estes dados. O saldo pendente do Cícero..."
            
    return resposta

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
            dados_resposta = agente_mock_resposta(prompt, perfil_ativo, telefone_simulado)
            
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