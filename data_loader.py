import json
import os
import unicodedata
from typing import Dict, List

# --- Constantes ---
ITEMS_JSON_PATH = "json/items.json"

# --- Funções Auxiliares ---
def normalize(text: str) -> str:
    """Normaliza o texto para busca, removendo acentos e convertendo para minúsculas."""
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

class ItemDataLoader:
    """Carrega e gerencia os dados dos itens do jogo a partir de um arquivo JSON."""
    def __init__(self):
        self.items_dict = self._load_items_json()
        if self.items_dict:
            print(f"✅ Carregados {len(self.items_dict)} itens do JSON")

    def _load_items_json(self) -> Dict:
        """Carrega os itens do arquivo JSON e os processa em um dicionário."""
        if not os.path.exists(ITEMS_JSON_PATH):
            print(f"❌ Arquivo '{ITEMS_JSON_PATH}' não encontrado.")
            return {}

        try:
            with open(ITEMS_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            items_dict = {}
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    print(f"⚠️ Ignorando entrada inválida na posição {idx}: {item}")
                    continue

                item_id = item.get("UniqueName")
                if not item_id:
                    continue

                localized_names = item.get("LocalizedNames") or {}
                localized_descriptions = item.get("LocalizedDescriptions") or {}

                name = localized_names.get("PT-BR") or localized_names.get("EN-US") or item_id
                description = localized_descriptions.get("PT-BR") or localized_descriptions.get("EN-US") or ""

                items_dict[item_id] = {"name": name, "description": description}
            
            return items_dict

        except Exception as e:
            print(f"❌ Erro ao carregar JSON: {e}")
            return {}

    def search_item_by_name(self, search_term: str) -> List[Dict]:
        """Busca por um item com base em um termo de pesquisa."""
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

        processed_bases = set()
        for item_id in matching_items:
            base_id = self._extract_base_id(item_id)
            if base_id in processed_bases:
                continue
            processed_bases.add(base_id)

            variants = self._find_all_variants(base_id)
            if variants:
                results.append({
                    "base_name": self.items_dict.get(variants[0], {}).get("name", base_id),
                    "variants": variants
                })

        return results

    def _extract_base_id(self, item_id: str) -> str:
        """Extrai o ID base de um item (ex: T4_BAG -> BAG)."""
        base = item_id.split('@')[0]
        if base.startswith('T') and '_' in base:
            parts = base.split('_', 1)
            if len(parts) > 1 and parts[0][1:].isdigit():
                return parts[1]
        return base

    def _find_all_variants(self, base_id: str) -> List[str]:
        """Encontra todas as variantes de um item base (tiers e encantamentos)."""
        variants = []
        for tier in range(1, 9): # T1-T8
            tier_id = f"T{tier}_{base_id}"
            if tier_id in self.items_dict:
                variants.append(tier_id)
            for enchant in range(1, 4):
                enchanted_id = f"{tier_id}@{enchant}"
                if enchanted_id in self.items_dict:
                    variants.append(enchanted_id)
        return variants

    def get_item_name(self, item_id: str) -> str:
        """Retorna o nome de um item a partir de seu ID."""
        return self.items_dict.get(item_id, {}).get("name", item_id)
