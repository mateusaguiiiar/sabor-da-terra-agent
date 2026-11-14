import streamlit as st
import time

# Configuração inicial da página
st.set_page_config(page_title="Assistente Sabor da Terra", page_icon="🌱", layout="centered")

st.title("🌱 Assistente Sabor da Terra")
st.caption("Interface de testes (Fatia Vertical - M1)")

# Inicialização do histórico de mensagens na sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "assistant", "content": "Olá! Sou o assistente da Sabor da Terra. Como posso ajudar hoje?"}
    ]

# Renderizar o histórico de mensagens
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Função Mock do Agente (a ser substituída pela ligação real ao Vertex AI / ADK do Integrante 1)
def agente_mock_resposta(mensagem_usuario):
    """Simula o tempo de processamento e a resposta do orquestrador."""
    time.sleep(1.5) # Simula latência da API
    
    if "certificação da josefa" in mensagem_usuario.lower():
        return "Não. A certificação orgânica venceu em 30/09/2026.\n\n**Fonte:** `cert_organica_josefa_souza_P008.txt`"
    
    return f"Recebi a sua mensagem: '{mensagem_usuario}'. O orquestrador real será ligado em breve!"

# Captura a entrada do utilizador
if prompt := st.chat_input("Escreva a sua mensagem ou pedido aqui..."):
    # Adiciona a mensagem do utilizador ao ecrã e ao estado
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Exibe indicador de carregamento enquanto o agente processa
    with st.chat_message("assistant"):
        with st.spinner("A processar..."):
            resposta = agente_mock_resposta(prompt)
            st.markdown(resposta)
    
    # Guarda a resposta do assistente no estado
    st.session_state.mensagens.append({"role": "assistant", "content": resposta})