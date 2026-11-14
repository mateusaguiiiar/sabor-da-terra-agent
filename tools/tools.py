from typing import List, Dict, Any, Optional

# --- Módulo 2: RAG ---
def buscar_documentos(pergunta: str, tipo_doc: Optional[str] = None, produtor_id: Optional[str] = None, k: int = 3) -> List[Dict[str, Any]]:
    """Busca trechos relevantes nos documentos de texto."""
    return [{"trecho": "Certificação orgânica válida até 12/2027.", "arquivo": "cert_organica_mock.txt", "secao": "Corpo", "score": 0.95}]

# --- Módulo 3: Triagem ---
def triar_pedido(texto: str, canal: str, remetente: str) -> Dict[str, Any]:
    """Transforma mensagem livre em JSON estruturado."""
    return {
        "tipo_mensagem": "pedido de compra",
        "comprador": "Restaurante Teste",
        "itens": [{"produto": "queijo coalho", "quantidade": 10, "unidade": "kg", "exige_organico": False}],
        "prazo": "2026-11-15",
        "urgencia": "baixa",
        "problemas": [],
        "perguntas_de_esclarecimento": ""
    }

# --- Módulo 4: Dados e Comunicação ---
def consultar_produtores(produto: str, municipio: Optional[str] = None, organico: bool = False, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
    """Lista produtores ativos (sem dados sensíveis)."""
    return [{"produtor_id": "P001", "nome": "Maria das Graças", "municipio": "Garanhuns"}]

def verificar_certificacao(produtor_id: str, produto: str, data_ref: str) -> Dict[str, Any]:
    """Verifica se a certificação orgânica está válida na data de referência."""
    return {"valida": True, "validade": "2027-08-01", "motivo": "Certificação ativa."}

def verificar_sazonalidade(produto: str, mes: str) -> Dict[str, Any]:
    """Retorna o nível de safra de um produto."""
    return {"nivel": "alta", "observacao": "Em safra", "alerta": False}

def obter_preco(produto: str, organico: bool, quantidade_kg: float) -> Dict[str, Any]:
    """Calcula o preço com base na tabela vigente."""
    return {"preco_unitario": 32.0, "desconto_atacado": 0.0, "total": 320.0}

def vendas_do_produtor(produtor_id: str, periodo: str) -> Dict[str, Any]:
    """Calcula o total de vendas do produtor."""
    return {"produtor_id": produtor_id, "total_vendas": 1500.00}

def saldo_a_receber(produtor_id: str, periodo: str) -> Dict[str, Any]:
    """Calcula o saldo pendente de pagamento do produtor."""
    return {"produtor_id": produtor_id, "saldo_pendente": 500.00}

def rastrear_lote(lote_id: str) -> Dict[str, Any]:
    """Busca a origem de um lote entregue."""
    return {"produtor": "P003", "produto": "queijo coalho", "quantidade": 45, "comprador": "Restaurante Raízes", "validade": "2026-10-02"}

def sugerir_alocacao(itens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sugere produtores aptos para os itens solicitados."""
    return [{"produto": "queijo coalho", "produtores_aptos": ["P001", "P003"], "lacuna_kg": 0}]

def gerar_resumo_produtor(produtor_id: str, periodo: str) -> str:
    """Gera texto de resumo financeiro redigido pelo LLM (Mock)."""
    return f"Resumo simulado para {produtor_id} no período {periodo}. Vendas: R$ 1500,00."

def gerar_notificacao_novo_pedido(produtor_id: str, pedido: Dict[str, Any]) -> str:
    """Gera notificação de novo pedido redigida pelo LLM (Mock)."""
    return "Você tem um novo pedido simulado de 10kg de queijo coalho."

def mascarar(texto: str) -> str:
    """Oculta CPF, conta bancária e chaves PIX."""
    return texto.replace("123.456.789-00", "***.***.***-**")