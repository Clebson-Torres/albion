from typing import Dict, List
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from data_loader import ItemDataLoader
from api_client import AlbionApiClient

# --- Inicialização de Serviços ---
try:
    llm = OllamaLLM(model="gemma3:4b")
    PROMPT_TEMPLATE = PromptTemplate.from_template(
        'Você é um assistente especialista em Albion Online. Extraia até 6 variantes do nome do item do pedido do usuário. '
        'Responda APENAS com o nome do item. Se não entender, responda com "ERRO". '
        'Pedido do usuário: "{user_input}"'
    )
    LLM_ENABLED = True
    print("🤖 Assistente de IA inicializado.")
except Exception as e:
    print(f"⚠️  Não foi possível inicializar o assistente de IA: {e}")
    print("   O programa continuará em modo de busca simples.")
    LLM_ENABLED = False

class AlbionArbitrageAnalyzer:
    """Analisa e apresenta oportunidades de arbitragem no Albion Online."""
    def __init__(self, item_loader: ItemDataLoader, api_client: AlbionApiClient):
        self.item_loader = item_loader
        self.api_client = api_client

    def analyze_arbitrage(self, item_ids: List[str]) -> List[Dict]:
        """Coordena a busca de preços e a análise de oportunidades de arbitragem."""
        prices = self.api_client.fetch_prices(item_ids)
        if not prices:
            return []

        opportunities = []
        for item_id in item_ids:
            item_name = self.item_loader.get_item_name(item_id)
            if not item_name:
                continue

            # 1. Encontrar o local de compra mais barato
            cheapest_buy, cheapest_price = None, float('inf')
            for city, city_prices in prices.items():
                if item_id in city_prices:
                    sell_price = city_prices[item_id]["sell_min"]
                    if 0 < sell_price < cheapest_price:
                        cheapest_price = sell_price
                        cheapest_buy = {"city": city, "price": sell_price}
            
            if not cheapest_buy:
                continue
            
            # 2. Encontrar as melhores oportunidades de venda
            best_sells = []
            for city, city_prices in prices.items():
                if city == cheapest_buy["city"]:
                    continue
                if item_id in city_prices:
                    buy_price = city_prices[item_id]["buy_max"]
                    profit = buy_price - cheapest_price
                    if profit > 0:
                        best_sells.append({
                            "city": city,
                            "price": buy_price,
                            "profit": profit,
                            "profit_percent": (profit / cheapest_price) * 100
                        })
            
            # 3. Se houver vendas lucrativas, registrar a oportunidade
            if best_sells:
                best_sells.sort(key=lambda x: x["profit"], reverse=True)
                opportunities.append({
                    "item_name": item_name,
                    "item_id": item_id,
                    "buy_location": cheapest_buy,
                    "sell_opportunities": best_sells[:3]  # Pega as 3 melhores
                })
        
        return opportunities

    def print_arbitrage_results(self, opportunities: List[Dict]):
        """Formata e exibe os resultados da análise de arbitragem."""
        if not opportunities:
            print("❌ Nenhuma oportunidade de arbitragem encontrada.")
            return
        
        print(f"\n{'='*80}\n🎯 OPORTUNIDADES DE ARBITRAGEM ENCONTRADAS: {len(opportunities)}\n{'='*80}")
        for i, opp in enumerate(opportunities, 1):
            print(f"\n📦 {i}. {opp['item_name']} ({opp['item_id']})")
            print(f"💰 Comprar em: {opp['buy_location']['city']} por {opp['buy_location']['price']:,} silver")
            print("🎯 Melhores locais para vender:")
            for j, sell in enumerate(opp['sell_opportunities'], 1):
                print(f"   {j}. {sell['city']}: {sell['price']:,} silver "
                      f"(+{sell['profit']:,} | +{sell['profit_percent']:.1f}%) ")
            print("-" * 50)

def get_search_term_from_user(user_input: str) -> str:
    """Usa o LLM para extrair um termo de busca do input do usuário, se disponível."""
    if LLM_ENABLED:
        prompt = PROMPT_TEMPLATE.format(user_input=user_input)
        print("🧠 Analisando seu pedido com a IA...")
        try:
            llm_response = llm.invoke(prompt).strip()
            if "ERRO" in llm_response or not llm_response:
                print("❌ A IA não conseguiu identificar um item. Usando busca simples.")
                return user_input
            
            print(f"🤖 Item identificado pela IA: {llm_response}")
            return llm_response
        except Exception as e:
            print(f"❌ Erro ao contatar a IA: {e}. Usando busca simples.")
    return user_input

def main():
    """Função principal que executa o loop da aplicação."""
    # Inicialização dos componentes
    item_loader = ItemDataLoader()
    if not item_loader.items_dict:
        print("Encerrando o programa devido à falha no carregamento dos itens.")
        return
        
    api_client = AlbionApiClient()
    analyzer = AlbionArbitrageAnalyzer(item_loader, api_client)
    
    print("\n🔍 BUSCA DE ITENS PARA ARBITRAGEM")
    print("Digite o nome de um item (ou 'sair' para terminar)")

    while True:
        user_input = input("\n> ").strip()
        if user_input.lower() in ['sair', 'exit', 'quit']:
            print("👋 Até mais!")
            break
        if not user_input:
            continue

        # Obter o termo de busca (com ou sem IA)
        search_term = get_search_term_from_user(user_input)

        # Buscar os itens correspondentes
        search_results = item_loader.search_item_by_name(search_term)
        if not search_results:
            print(f"❌ Nenhum item encontrado para '{search_term}'. Tente novamente.")
            continue
        
        # Por enquanto, vamos analisar apenas o primeiro resultado encontrado
        # TODO: Permitir que o usuário escolha qual item analisar se houver múltiplos resultados
        first_result = search_results[0]
        variants = first_result['variants']
        print(f"\n🔄 Analisando {len(variants)} variantes de '{first_result['base_name']}'...")
        
        # Analisar e imprimir as oportunidades
        opportunities = analyzer.analyze_arbitrage(variants)
        analyzer.print_arbitrage_results(opportunities)

if __name__ == "__main__":
    main()
