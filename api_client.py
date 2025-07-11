import requests
from typing import Dict, List

# --- Constantes da API ---
PRICE_API_URL = "https://west.albion-online-data.com/api/v2/stats/prices"
CITIES = ["Martlock", "Bridgewatch", "Fort Sterling", "Lymhurst", "Thetford", "Caerleon"]

class AlbionApiClient:
    """Cliente para interagir com a API de dados do Albion Online."""
    def fetch_prices(self, item_ids: List[str]) -> Dict:
        """Busca os preços de uma lista de itens em cidades específicas."""
        if not item_ids:
            return {}

        # Filtra apenas os IDs que são strings válidas para evitar erros na API
        valid_ids = [str(id) for id in item_ids if isinstance(id, str) and id.strip()]
        if not valid_ids:
            return {}
        
        url = f"{PRICE_API_URL}/{','.join(valid_ids)}?locations={','.join(CITIES)}&qualities=1"

        print(f"[API] Consultando preços para {len(valid_ids)} itens...")
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()  # Lança uma exceção para respostas de erro (4xx ou 5xx)
            data = response.json()
            
            prices = {}
            for entry in data:
                city, item_id = entry["city"], entry["item_id"]
                if city not in prices:
                    prices[city] = {}
                prices[city][item_id] = {
                    "buy_max": entry.get("buy_price_max", 0),
                    "sell_min": entry.get("sell_price_min", 0),
                }
            return prices
        except requests.Timeout:
            print("❌ Erro: A requisição para a API demorou demais (timeout).")
            return {}
        except requests.RequestException as e:
            print(f"❌ Erro ao buscar preços na API: {e}")
            return {}
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado ao processar os preços: {e}")
            return {}
