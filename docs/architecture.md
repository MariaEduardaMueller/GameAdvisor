# Arquitetura — GameAdvisor

## Visão geral

O GameAdvisor é um agente hospedado no **Amazon Bedrock AgentCore Runtime** (Harness) que recomenda jogos da Steam com base no perfil Steam do próprio usuário, informado por chat (SteamID64, URL de perfil, URL customizada ou nome customizado). O agente combina:

1. **Dados em tempo real da Steam** (biblioteca, jogos recentes, wishlist, preços, busca por nome) via ferramentas.
2. **Uma base de conhecimento (RAG)** no Amazon Bedrock Knowledge Bases com reviews de usuários, usada para embasar recomendações com opiniões reais em vez de dados inventados.
3. **Contexto de sessão** mantido pelo AgentCore Runtime (`runtimeSessionId`), permitindo conversas multi-turno (ex.: "e o mais barato desses?" reaproveitando o SteamID já informado).

## Componentes

### 1. Agente (`src/agent/`)
- `main.py`: entrypoint do agente no AgentCore Harness (`invoke_harness`), registra as ferramentas e a instrução de sistema.
- `system_prompt.txt`: papel, tom e regras de comportamento do GameAdvisor — inclui explicitamente: não recomendar jogos que o usuário já possui, não inventar preço/dados de jogo, recusar perguntas fora do domínio Steam, nunca revelar a Steam API key nem o próprio system prompt/instruções internas.

### 2. Ferramentas Steam (`src/tools/steam_tools.py`)
Funções que encapsulam chamadas à Steam Web API e à Steam Store API:

| Função | Descrição |
|---|---|
| `extract_or_resolve_steam_id` | Resolve SteamID64 a partir de URL de perfil, URL customizada, nome customizado ou ID direto (usa `ISteamUser/ResolveVanityURL`). |
| `get_user_top_games` | Biblioteca completa + jogos mais jogados por tempo total + jogos recentes (`IPlayerService/GetOwnedGames`, `GetRecentlyPlayedGames`). Retorna também a lista de jogos já possuídos, para o agente nunca recomendar duplicado. |
| `get_recently_played_games` | Jogos jogados nas últimas 2 semanas. |
| `get_wishlist` | Lista da wishlist com nomes resolvidos via Steam Store (`IWishlistService/GetWishlist` + `store/api/appdetails`). |
| `get_game_price` / `get_wishlist_prices` | Preço atual, preço original e desconto (região `br`), inclusive o item mais caro da wishlist. |
| `search_game_by_name` | Busca por nome na Steam Store (`store/api/storesearch`) para resolver AppID quando o usuário não sabe o ID. |
| `retrieve_game_reviews` | Consulta a Knowledge Base do Bedrock (`bedrock-agent-runtime.retrieve`) para trazer trechos de reviews relevantes a uma pergunta/jogo. |

### 3. Exposição das ferramentas via Gateway (`src/tools/lambda_function.py`)
A Steam API key não fica exposta ao agente/LLM: as funções de `steam_tools.py` são executadas dentro de uma **AWS Lambda**, registrada como *target* do **Amazon Bedrock AgentCore Gateway**. O Gateway expõe essas funções como ferramentas (MCP) que o agente pode chamar; a credencial (`STEAM_API_KEY`) vive apenas na variável de ambiente da Lambda.

### 4. RAG (`src/rag/`)
Base de conhecimento no Amazon Bedrock Knowledge Bases contendo reviews de jogos. Usada pela ferramenta `retrieve_game_reviews` para embasar respostas sobre opinião/qualidade de um jogo (ex.: "o que os jogadores acham de Cities: Skylines?") — o `retrieval_context` retornado é o que a métrica **Faithfulness** do DeepEval usa como referência.

## Fluxo de uma interação

1. Usuário informa SteamID/URL/nome no chat.
2. Agente chama `extract_or_resolve_steam_id` (via Gateway → Lambda) para obter o SteamID64.
3. Conforme a pergunta, chama a ferramenta Steam relevante (biblioteca, preço, wishlist, busca) e/ou `retrieve_game_reviews` para embasar a recomendação com reviews reais.
4. Agente combina os dados retornados com a instrução de sistema (não recomendar jogos já possuídos, não inventar preço, manter-se no domínio Steam) e responde.
5. O `runtimeSessionId` mantém o SteamID e o histórico da conversa disponíveis nos turnos seguintes.

## Escopo e limites assumidos

- **Domínio**: recomendação de jogos Steam e informações sobre a biblioteca/wishlist/preço do próprio usuário.
- **Fora de escopo**: qualquer assunto fora de jogos/Steam, promessas de compra/reembolso, exposição da API key ou do system prompt.
- **Falha grave**: recomendar um jogo que o usuário já possui, inventar preço/disponibilidade, ou vazar credenciais/instruções internas.


