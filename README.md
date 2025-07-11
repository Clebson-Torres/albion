# Analisador de Mercado para Albion Online

Este projeto é uma ferramenta de linha de comando (CLI) para analisar oportunidades de arbitragem no jogo Albion Online. A aplicação busca os preços de itens em diferentes cidades e calcula o lucro potencial ao comprar em um local e vender em outro.

Opcionalmente, utiliza um assistente de IA (rodando localmente com Ollama) para interpretar os pedidos do usuário em linguagem natural, tornando a busca de itens mais flexível e intuitiva.

## Funcionalidades

- **Busca de Itens**: Encontra itens e todas as suas variantes (tiers e encantamentos) com base em um nome.
- **Integração com IA**: Permite que o usuário descreva um item em linguagem natural (ex: "a espada que reflete dano") para a IA identificar o item correto.
- **Análise de Preços**: Consulta a API pública do [Albion Online Data Project](https://www.albion-online-data.com/) para obter os preços de compra e venda mais recentes.
- **Cálculo de Arbitragem**: Identifica o local de compra mais barato e os locais de venda mais lucrativos para cada variante de item.
- **Resultados Detalhados**: Exibe as oportunidades de lucro em valor absoluto (silver) e percentual.

## Estrutura do Projeto

O código é organizado de forma modular para facilitar a manutenção e expansão:

- `main.py`: Ponto de entrada da aplicação, gerencia a interação com o usuário e orquestra os outros módulos.
- `data_loader.py`: Responsável por carregar, processar e buscar os dados dos itens a partir do arquivo `json/items.json`.
- `api_client.py`: Contém a lógica para se comunicar com a API de preços do Albion Online.
- `json/items.json`: Arquivo de dados contendo informações sobre todos os itens do jogo. (É necessário obter este arquivo separadamente).

## Pré-requisitos

- Python 3.9+
- Pip (gerenciador de pacotes do Python)
- (Opcional) [Ollama](https://ollama.com/) para a funcionalidade de IA. É necessário ter um modelo como o `gemma3:4b` instalado (`ollama run gemma3:4b`).

## Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```

2. **Crie e ative um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Obtenha o arquivo de itens:**
   Faça o download do arquivo `items.json` mais recente e coloque-o dentro de uma pasta `json` na raiz do projeto. Uma fonte comum para este arquivo é o [Albion Online Data Project](https://github.com/albion-online-data/albion-online-data).

## Como Usar

Com o ambiente configurado e o `items.json` no lugar, execute a aplicação:

```bash
python main.py
```

A aplicação irá carregar os itens e, se configurado, inicializar a IA. Depois, você poderá digitar o nome de um item para iniciar a análise.

**Exemplos de uso:**

```
> Bolsa de Couro

> o capuz que te deixa invisível

> sair
```

## Como Contribuir

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* para relatar bugs ou sugerir novas funcionalidades. Se desejar contribuir com código, por favor, crie um *fork* do projeto e envie um *pull request*.
