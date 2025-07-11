import requests
import json
import os
from typing import Dict, List, Optional
import unicodedata

# Configurações
ITEMS_JSON_PATH = "json\items.json"
PRICE_API = "https://west.albion-online-data.com/api/v2/stats/prices"



CITIES = ["Martlock", "Bridgewatch", "Fort Sterling", "Lymhurst", "Thetford", "Caerleon"]

def normalize(text: str) -> str:    
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

class AlbionArbitrageAnalyzer:
    def __init__(self):
        self.items_dict = self.load_items_json()
        print(f"✅ Carregados {len(self.items_dict)} itens do JSON")
    
    def load_items_json(self) -> Dict:
    
        if not os.path.exists(ITEMS_JSON_PATH):
            print(f"❌ Arquivo '{ITEMS_JSON_PATH}' não encontrado.")
            return {}

        try:
            with open(ITEMS_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            items_dict = {}
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    print(f"⚠️ Ignorando item inválido na posição {idx}: {item}")
                    continue

                try:
                    item_id = item.get("UniqueName", "")
                    if not item_id:
                        continue

                    localized_names = item.get("LocalizedNames", {})
                    localized_descriptions = item.get("LocalizedDescriptions", {})

                    name = (localized_names.get("PT-BR") or
                            localized_names.get("EN-US") or
                            item_id)

                    description = (localized_descriptions.get("PT-BR") or
                                localized_descriptions.get("EN-US") or
                                "")

                    items_dict[item_id] = {
                        "name": name,
                        "description": description
                    }
                except Exception as e:
                    print(f"⚠️ Erro ao processar item na posição {idx}: {e}")

            return items_dict
        except Exception as e:
            print(f"❌ Erro ao carregar JSON: {e}")
            return {}

    

    def search_item_by_name(self, search_term: str) -> List[Dict]:
        """Busca itens por nome ou descrição, retorna variantes T1-T6"""
        results = []
        search_norm = normalize(search_term)
        
        matching_items = []
        for item_id, data in self.items_dict.items():
            name = data.get("name", "")
            description = data.get("description", "")
            
            combined_text = f"{name} {description}"
            combined_norm = normalize(combined_text)
            
            if search_norm in combined_norm:
                matching_items.append(item_id)

        # Agrupa por base
        processed_bases = set()
        for item_id in matching_items:
            base_id = self.extract_base_id(item_id)
            if base_id in processed_bases:
                continue
            processed_bases.add(base_id)

            variants = self.find_all_variants(base_id)
            if variants:
                results.append({
                    "base_name": self.items_dict.get(variants[0], {}).get("name", base_id),
                    "base_id": base_id,
                    "variants": variants
                })
        
        return results
    def extract_base_id(self, item_id: str) -> str:
        """Extrai o ID base removendo tier (T1-T8) e enchantment (@1-@3)"""
        # Remove enchantment (@1, @2, @3)
        base = item_id.split('@')[0]
        
        # Remove tier (T1_, T2_, etc.) se presente
        if base.startswith('T') and '_' in base:
            parts = base.split('_', 1)
            if len(parts) > 1 and parts[0][1:].isdigit():
                return parts[1]  # Remove o T1_, T2_, etc.
        
        return base
    
    def find_all_variants(self, base_id: str) -> List[str]:
        """Encontra todas as variantes T1-T6 (com e sem enchantment) de um item"""
        variants = []
        
        # Testa T1 a T6
        for tier in range(1, 7):
            tier_id = f"T{tier}_{base_id}"
            
            # Variante normal
            if tier_id in self.items_dict:
                variants.append(tier_id)
            
            # Variantes encantadas (@1, @2, @3)
            for enchant in range(1, 4):
                enchanted_id = f"{tier_id}@{enchant}"
                if enchanted_id in self.items_dict:
                    variants.append(enchanted_id)
        
        return variants
    
    def fetch_prices(self, item_ids: List[str]) -> Dict:
        """Busca preços de múltiplos itens"""
        if not item_ids:
            return {}
        
        # Filtra apenas IDs que existem no nosso dicionário
        valid_ids = [id for id in item_ids if id in self.items_dict]
        if not valid_ids:
            return {}
        
        url = f"{PRICE_API}/{','.join(valid_ids)}?locations={','.join(CITIES)}&qualities=1"

        print(f"[API] Consultando preços para {len(valid_ids)} itens...")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            prices = {}
            for entry in data:
                city = entry["city"]
                item_id = entry["item_id"]
                
                if city not in prices:
                    prices[city] = {}
                
                prices[city][item_id] = {
                    "buy_max": entry.get("buy_price_max", 0),
                    "sell_min": entry.get("sell_price_min", 0),
                    "buy_max_date": entry.get("buy_price_max_date", ""),
                    "sell_min_date": entry.get("sell_price_min_date", "")
                }
            
            return prices
        except Exception as e:
            print(f"❌ Erro ao buscar preços: {e}")
            return {}
    
    def analyze_arbitrage(self, item_ids: List[str]) -> List[Dict]:
        """Analisa oportunidades de arbitragem para os itens"""
        prices = self.fetch_prices(item_ids)
        print(prices)
        opportunities = []
        
        for item_id in item_ids:
            if item_id not in self.items_dict:
                continue
            
            item_name = self.items_dict[item_id]["name"]
            
            # Encontra a cidade mais barata para comprar
            cheapest_buy = None
            cheapest_price = float('inf')
            
            for city in CITIES:
                if city in prices and item_id in prices[city]:
                    price_data = prices[city][item_id]
                    sell_price = price_data["sell_min"]
                    
                    if sell_price > 0 and sell_price < cheapest_price:
                        cheapest_price = sell_price
                        cheapest_buy = {
                            "city": city,
                            "price": sell_price,
                            "date": price_data["sell_min_date"]
                        }
            
            if not cheapest_buy:
                continue
            
            # Encontra as melhores cidades para vender
            best_sells = []
            for city in CITIES:
                if city == cheapest_buy["city"]:  # Pula a mesma cidade
                    continue
                
                if city in prices and item_id in prices[city]:
                    price_data = prices[city][item_id]
                    buy_price = price_data["buy_max"]
                    
                    if buy_price > 0:
                        profit = buy_price - cheapest_price
                        profit_percent = (profit / cheapest_price) * 100
                        
                        if profit > 0:  # Só adiciona se há lucro
                            best_sells.append({
                                "city": city,
                                "price": buy_price,
                                "profit": profit,
                                "profit_percent": profit_percent,
                                "date": price_data["buy_max_date"]
                            })
            
            # Ordena por lucro decrescente
            best_sells.sort(key=lambda x: x["profit"], reverse=True)
            
            if best_sells:
                opportunities.append({
                    "item_id": item_id,
                    "item_name": item_name,
                    "buy_location": cheapest_buy,
                    "sell_opportunities": best_sells[:3]  # Top 3 oportunidades
                })
        
        return opportunities
    
    def print_arbitrage_results(self, opportunities: List[Dict]):
        """Imprime os resultados de arbitragem de forma organizada"""
        if not opportunities:
            print("❌ Nenhuma oportunidade de arbitragem encontrada.")
            return
        
        print(f"\n{'='*80}")
        print(f"🎯 OPORTUNIDADES DE ARBITRAGEM ENCONTRADAS: {len(opportunities)}")
        print(f"{'='*80}")
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n📦 {i}. {opp['item_name']} ({opp['item_id']})")
            print(f"💰 Comprar em: {opp['buy_location']['city']} por {opp['buy_location']['price']:,} silver")
            
            print("🎯 Melhores locais para vender:")
            for j, sell in enumerate(opp['sell_opportunities'], 1):
                print(f"   {j}. {sell['city']}: {sell['price']:,} silver "
                      f"(+{sell['profit']:,} | +{sell['profit_percent']:.1f}%)")
            
            print("-" * 50)

def main():
    analyzer = AlbionArbitrageAnalyzer()
    
    print("\n🔍 BUSCA DE ITENS PARA ARBITRAGEM")
    print("Digite o nome do item para buscar (ou 'sair' para terminar)")
    
    while True:
        search_term = input("\n> Digite o nome do item: ").strip()
        
        if search_term.lower() in ['sair', 'exit', 'quit']:
            print("👋 Até mais!")
            break
        
        if not search_term:
            print("❌ Digite um nome válido.")
            continue
        
        # Busca itens
        results = analyzer.search_item_by_name(search_term)
        
        if not results:
            print(f"❌ Nenhum item encontrado com o termo '{search_term}'.")
            continue
        
        print(f"\n📋 Encontrados {len(results)} grupos de itens:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['base_name']} ({len(result['variants'])} variantes)")
        
        # Seleciona qual grupo analisar
        try:
            choice = input(f"\nEscolha um grupo (1-{len(results)}) ou 'todos': ").strip()
            
            if choice.lower() == 'todos':
                # Analisa todos os grupos
                all_variants = []
                for result in results:
                    all_variants.extend(result['variants'])
                
                print(f"\n🔄 Analisando {len(all_variants)} variantes...")
                opportunities = analyzer.analyze_arbitrage(all_variants)
                analyzer.print_arbitrage_results(opportunities)
            
            else:
                choice_num = int(choice) - 1
                if 0 <= choice_num < len(results):
                    selected = results[choice_num]
                    print(f"\n📊 Variantes de {selected['base_name']}:")
                    for variant in selected['variants']:
                        variant_name = analyzer.items_dict.get(variant, {}).get('name', variant)
                        print(f"  • {variant}: {variant_name}")
                    
                    print(f"\n🔄 Analisando {len(selected['variants'])} variantes...")
                    opportunities = analyzer.analyze_arbitrage(selected['variants'])
                    analyzer.print_arbitrage_results(opportunities)
                else:
                    print("❌ Escolha inválida.")
        
        except ValueError:
            print("❌ Digite um número válido.")
        except KeyboardInterrupt:
            print("\n👋 Até mais!")
            break

if __name__ == "__main__":
    main()