from typing import Dict, List, Optional
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from data_loader import ItemDataLoader
from api_client import AlbionApiClient

# --- INICIALIZAÇÃO DE SERVIÇOS ---
try:
    llm = OllamaLLM(model="gemma3:4b")
    LLM_ENABLED = True
    print("🤖 Assistente de IA inicializado.")
except Exception as e:
    print(f"⚠️  Não foi possível inicializar o assistente de IA: {e}")
    LLM_ENABLED = False

# --- PROMPTS PARA A IA ---
PROMPT_IDENTIFICACAO = PromptTemplate.from_template(
    'Você é um especialista em Albion Online. Extraia o nome base do item do pedido do usuário. '
    'Responda APENAS com o nome do item. Se não entender, responda "ERRO". '
    'Pedido: "{user_input}"'
)

PROMPT_ANALISTA_HIBRIDO = PromptTemplate.from_template(
    'Você é um trader mestre de Albion Online. Sua tarefa é analisar os dados de mercado e a descrição de um item para responder à pergunta do usuário. '
    'Seja direto e recomende se o item é uma boa oportunidade de arbitragem (flipping) ou não, explicando o porquê em 2-3 frases.\n\n' 
    '--- DADOS DO ITEM ---\n' 
    'Nome: {item_name}\n' 
    'Descrição: {item_description}\n\n' 
    '--- ANÁLISE DE MERCADO (TEMPO REAL) ---\n' 
    '{market_summary}\n\n' 
    '--- PERGUNTA DO USUÁRIO ---\n' 
    '"{user_question}"\n\n' 
    '--- SUA RECOMENDAÇÃO PROFISSIONAL ---\n' 
    'Resposta:'
)

# --- CLASSES DE ANÁLISE ---
class MarketAnalyzer:
    """Analisa os dados de mercado para um único item."""
    def __init__(self, api_client: AlbionApiClient):
        self.api_client = api_client

    def analyze_single_item_market(self, item_id: str) -> Optional[Dict]:
        """Busca preços e calcula a melhor oportunidade de arbitragem para um item."""
        prices = self.api_client.fetch_prices([item_id])
        if not prices:
            return None

        cheapest_buy, cheapest_price = None, float('inf')
        for city, city_prices in prices.items():
            if item_id in city_prices:
                sell_price = city_prices[item_id]["sell_min"]
                if 0 < sell_price < cheapest_price:
                    cheapest_price = sell_price
                    cheapest_buy = {"city": city, "price": sell_price}
        
        if not cheapest_buy:
            return None

        best_sell, best_price = None, 0
        for city, city_prices in prices.items():
            if city == cheapest_buy["city"]: continue
            if item_id in city_prices:
                buy_price = city_prices[item_id]["buy_max"]
                if buy_price > best_price:
                    best_price = buy_price
                    best_sell = {"city": city, "price": buy_price}

        if not best_sell or best_sell["price"] <= cheapest_buy["price"]:
            return None

        profit = best_sell["price"] - cheapest_buy["price"]
        profit_percent = (profit / cheapest_buy["price"]) * 100

        return {
            "buy_location": cheapest_buy,
            "sell_location": best_sell,
            "profit": profit,
            "profit_percent": profit_percent
        }

# --- FUNÇÕES PRINCIPAIS ---
def get_ai_recommendation(item_id: str, item_name: str, item_description: str, market_summary: str, user_question: str) -> str:
    """Monta o prompt e consulta a IA para obter uma recomendação estratégica."""
    if not LLM_ENABLED:
        return "O modo IA está desativado. Não é possível gerar recomendação."

    prompt = PROMPT_ANALISTA_HIBRIDO.format(
        item_name=item_name,
        item_description=item_description or "Nenhuma descrição disponível.",
        market_summary=market_summary,
        user_question=user_question
    )
    
    print("\n🧠 A IA está analisando a oportunidade de mercado...")
    try:
        response = llm.invoke(prompt).strip()
        return response
    except Exception as e:
        return f"❌ Erro ao contatar a IA: {e}"

def main():
    """Função principal que executa o loop da aplicação."""
    item_loader = ItemDataLoader()
    if not item_loader.items_dict:
        print("Encerrando o programa devido à falha no carregamento dos itens.")
        return
        
    api_client = AlbionApiClient()
    market_analyzer = MarketAnalyzer(api_client)
    
    print("\n📈 ANALISTA DE MERCADO DE ALBION ONLINE 📈")
    print("Faça uma pergunta sobre um item ou categoria (ex: 'qual a melhor espada para flipar?')")

    while True:
        user_question = input("\n> ").strip()
        if user_question.lower() in ['sair', 'exit', 'quit']:
            print("👋 Até mais!")
            break
        if not user_question:
            continue

        # 1. Usar IA para identificar o item base da pergunta
        search_term = user_question
        if LLM_ENABLED:
            try:
                prompt = PROMPT_IDENTIFICACAO.format(user_input=user_question)
                llm_response = llm.invoke(prompt).strip()
                if "ERRO" not in llm_response and llm_response:
                    search_term = llm_response
                    print(f"🤖 Item base identificado pela IA: {search_term}")
            except Exception as e:
                print(f"⚠️  Não foi possível usar a IA para identificação: {e}")

        # 2. Buscar todas as variantes do item
        search_results = item_loader.search_item_by_name(search_term)
        if not search_results:
            print(f"❌ Nenhum item encontrado para '{search_term}'. Tente novamente.")
            continue
        
        variants = search_results[0]['variants']
        base_name = search_results[0]['base_name']
        print(f"\n🔄 Analisando {len(variants)} variantes de '{base_name}' em segundo plano...")

        # 3. Analisar todas as variantes e coletar oportunidades
        all_opportunities = []
        for item_id in variants:
            analysis = market_analyzer.analyze_single_item_market(item_id)
            if analysis:
                all_opportunities.append({
                    "item_id": item_id,
                    "item_name": item_loader.get_item_name(item_id),
                    "analysis": analysis
                })
        
        if not all_opportunities:
            print(f"\n❌ Nenhuma oportunidade de arbitragem encontrada para '{base_name}'.")
            continue

        # 4. Ordenar as oportunidades pela margem de lucro
        all_opportunities.sort(key=lambda x: x['analysis']['profit_percent'], reverse=True)

        # 5. Apresentar as 3 melhores oportunidades
        print(f"\n{'='*80}\n🎯 AS 3 MELHORES OPORTUNIDADES PARA '{base_name.upper()}'\n{'='*80}")
        TOP_N = 3
        for i, opp in enumerate(all_opportunities[:TOP_N], 1):
            item_id = opp['item_id']
            item_name = opp['item_name']
            analysis = opp['analysis']
            
            print(f"\n{i}. {item_name} ({item_id})")
            
            market_summary_text = (
                f"- Rota de Compra e Venda: {analysis['buy_location']['city']} -> {analysis['sell_location']['city']}\n"
                f"- Preço de Compra: {analysis['buy_location']['price']:,} silver\n"
                f"- Preço de Venda: {analysis['sell_location']['price']:,} silver\n"
                f"- Lucro Potencial: {analysis['profit']:,} silver\n"
                f"- Margem de Lucro: {analysis['profit_percent']:.2f}%"
            )
            print(market_summary_text)

            item_description = item_loader.get_item_description(item_id)
            recommendation = get_ai_recommendation(
                item_id, item_name, item_description, market_summary_text, user_question
            )
            print(f"\n💡 Recomendação da IA:\n{recommendation}")
            print("-" * 50)

if __name__ == "__main__":
    main()
