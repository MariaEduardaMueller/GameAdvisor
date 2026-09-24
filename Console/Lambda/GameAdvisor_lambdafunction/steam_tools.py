import os
import re
import boto3
import requests

STEAM_API_KEY = os.getenv("STEAM_API_KEY")


# =========================================================
# RESOLVER STEAM ID
# =========================================================

def extract_or_resolve_steam_id(user_input: str) -> str:
    """
    Extrai ou resolve o SteamID64 de:
    - SteamID64
    - URL de perfil
    - URL customizada
    - nome customizado
    """

    user_input = user_input.strip().strip("/")

    # 1. Extrai ID de 17 dígitos em URLs
    # Exemplo:
    # https://steamcommunity.com/profiles/76561198844640485/
    profile_match = re.search(
        r'profiles/(\d{17})',
        user_input
    )

    if profile_match:
        return profile_match.group(1)

    # 2. Se for um ID numérico de 17 dígitos direto
    if user_input.isdigit() and len(user_input) == 17:
        return user_input

    # 3. Se for URL personalizada
    # ou apenas o custom_name
    custom_name = user_input.split("/")[-1]

    url = (
        "https://api.steampowered.com/"
        "ISteamUser/ResolveVanityURL/v0001/"
    )

    params = {
        "key": STEAM_API_KEY,
        "vanityurl": custom_name
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("response", {}).get("success") == 1:
            return data["response"]["steamid"]

    except requests.RequestException as err:
        raise ValueError(
            f"Erro ao consultar a Steam: {err}"
        )

    raise ValueError(
        f"Não foi possível resolver o Steam ID para: {user_input}"
    )


# =========================================================
# JOGOS MAIS JOGADOS
# =========================================================

def get_user_top_games(
    steam_input: str,
    limit: int = 15,
    recent_limit: int = 5
) -> str:
    """
    Busca informações da conta Steam:

    - jogos mais jogados por tempo total;
    - jogos jogados recentemente;
    - biblioteca completa.
    """

    # -----------------------------------------------------
    # 1. Identificar SteamID
    # -----------------------------------------------------

    try:
        steam_id = extract_or_resolve_steam_id(
            steam_input
        )

    except Exception as e:
        return (
            f"Erro ao identificar conta Steam: {str(e)}"
        )

    # -----------------------------------------------------
    # 2. Buscar biblioteca
    # -----------------------------------------------------

    owned_games_url = (
        "https://api.steampowered.com/"
        "IPlayerService/GetOwnedGames/v0001/"
    )

    owned_params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id,
        "format": "json",
        "include_appinfo": True,
        "include_played_free_games": True
    }

    try:
        owned_response = requests.get(
            owned_games_url,
            params=owned_params,
            timeout=10
        )

        owned_response.raise_for_status()

        owned_data = owned_response.json()

        response_data = owned_data.get(
            "response",
            {}
        )

        # Importante:
        # ausência de "games" pode significar
        # perfil privado e não biblioteca vazia.
        if "games" not in response_data:
            return (
                f"Não foi possível acessar a biblioteca "
                f"do SteamID {steam_id}. "
                f"O perfil ou os detalhes dos jogos "
                f"podem estar privados."
            )

        games = response_data.get(
            "games",
            []
        )

        # -------------------------------------------------
        # 3. Ordenar jogos por tempo total
        # -------------------------------------------------

        games_sorted = sorted(
            games,
            key=lambda x: x.get(
                "playtime_forever",
                0
            ),
            reverse=True
        )

        top_games = games_sorted[:limit]

        # -------------------------------------------------
        # 4. Lista completa da biblioteca
        # -------------------------------------------------

        all_owned_names = [
            game.get("name")
            for game in games
            if game.get("name")
        ]

        # -------------------------------------------------
        # 5. Buscar jogos recentes
        # -------------------------------------------------

        recent_games_url = (
            "https://api.steampowered.com/"
            "IPlayerService/GetRecentlyPlayedGames/v0001/"
        )

        recent_params = {
            "key": STEAM_API_KEY,
            "steamid": steam_id,
            "format": "json",
            "count": recent_limit
        }

        try:
            recent_response = requests.get(
                recent_games_url,
                params=recent_params,
                timeout=10
            )

            recent_response.raise_for_status()

            recent_data = recent_response.json()

            recent_response_data = recent_data.get(
                "response",
                {}
            )

            recent_games = recent_response_data.get(
                "games",
                []
            )

        except requests.RequestException:
            recent_games = []

        # -------------------------------------------------
        # 6. Montar resultado
        # -------------------------------------------------

        output = [
            f"SteamID: {steam_id}",
            "",
            "--- JOGOS MAIS JOGADOS (TEMPO TOTAL) ---"
        ]

        if top_games:

            for game in top_games:

                name = game.get(
                    "name",
                    "Nome desconhecido"
                )

                minutes = game.get(
                    "playtime_forever",
                    0
                )

                hours = round(
                    minutes / 60,
                    1
                )

                output.append(
                    f"- {name}: {hours} horas"
                )

        else:

            output.append(
                "Nenhum jogo disponível na biblioteca."
            )

        # -------------------------------------------------
        # Jogos recentes
        # -------------------------------------------------

        output.extend([
            "",
            "--- JOGOS JOGADOS RECENTEMENTE ---"
        ])

        if recent_games:

            for game in recent_games[:recent_limit]:

                name = game.get(
                    "name",
                    "Nome desconhecido"
                )

                recent_minutes = game.get(
                    "playtime_2weeks",
                    0
                )

                recent_hours = round(
                    recent_minutes / 60,
                    1
                )

                total_minutes = game.get(
                    "playtime_forever",
                    0
                )

                total_hours = round(
                    total_minutes / 60,
                    1
                )

                output.append(
                    f"- {name}: "
                    f"{recent_hours} horas nas últimas "
                    f"2 semanas "
                    f"(total: {total_hours} horas)"
                )

        else:

            output.append(
                "Nenhum jogo jogado recentemente "
                "foi retornado pela Steam."
            )

        # -----------------------------------------------------
        # Biblioteca completa
        # -----------------------------------------------------

        output.extend([
            "",
            "--- LISTA DE TODOS OS JOGOS JÁ POSSUÍDOS "
            "PELO USUÁRIO (NÃO RECOMENDAR ESTES) ---"
        ])

        if all_owned_names:

            output.append(
                ", ".join(all_owned_names)
            )

        else:

            output.append(
                "Nenhum jogo disponível."
            )

        return "\n".join(output)

    except requests.RequestException as err:

        return (
            f"Erro ao consultar a biblioteca da Steam: {err}"
        )

    except Exception as err:

        return (
            f"Erro ao processar dados da Steam: {err}"
        )


# =========================================================
# JOGOS JOGADOS RECENTEMENTE
# =========================================================

def get_recently_played_games(
    steam_input: str,
    limit: int = 5
) -> str:
    """
    Busca os jogos jogados recentemente pelo usuário.

    A Steam retorna dados de jogos jogados
    nas últimas duas semanas.
    """

    try:

        steam_id = extract_or_resolve_steam_id(
            steam_input
        )

    except Exception as e:

        return (
            f"Erro ao identificar conta Steam: {str(e)}"
        )

    url = (
        "https://api.steampowered.com/"
        "IPlayerService/GetRecentlyPlayedGames/v0001/"
    )

    params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id,
        "format": "json",
        "count": limit
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        response_data = data.get(
            "response",
            {}
        )

        # A Steam pode não retornar "games"
        if "games" not in response_data:

            return (
                f"Nenhum jogo jogado recentemente "
                f"foi retornado pela Steam para o "
                f"SteamID {steam_id}."
            )

        games = response_data.get(
            "games",
            []
        )

        if not games:

            return (
                f"Nenhum jogo jogado recentemente "
                f"foi retornado pela Steam para o "
                f"SteamID {steam_id}."
            )

        output = [
            f"SteamID: {steam_id}",
            "",
            "--- JOGOS JOGADOS RECENTEMENTE ---"
        ]

        for game in games[:limit]:

            name = game.get(
                "name",
                "Nome desconhecido"
            )

            recent_minutes = game.get(
                "playtime_2weeks",
                0
            )

            recent_hours = round(
                recent_minutes / 60,
                1
            )

            total_minutes = game.get(
                "playtime_forever",
                0
            )

            total_hours = round(
                total_minutes / 60,
                1
            )

            output.append(
                f"- {name}: "
                f"{recent_hours} horas nas últimas "
                f"2 semanas "
                f"(total: {total_hours} horas)"
            )

        return "\n".join(output)

    except requests.RequestException as err:

        return (
            f"Erro ao consultar jogos recentes "
            f"da Steam: {err}"
        )

    except Exception as err:

        return (
            f"Erro ao processar jogos recentes "
            f"da Steam: {err}"
        )


# =========================================================
# WISHLIST
# =========================================================

def get_wishlist(
    steam_input: str,
    limit: int = 250
) -> str:
    """
    Consulta a wishlist da Steam.

    Retorna os jogos encontrados e tenta
    resolver o nome de cada AppID através
    da Steam Store.
    """

    try:

        steam_id = extract_or_resolve_steam_id(
            steam_input
        )

    except Exception as e:

        return (
            f"Erro ao identificar conta Steam: {str(e)}"
        )

    wishlist_url = (
        "https://api.steampowered.com/"
        "IWishlistService/GetWishlist/v0001/"
    )

    params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id
    }

    try:

        response = requests.get(
            wishlist_url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        response_data = data.get(
            "response",
            {}
        )

        items = response_data.get(
            "items",
            []
        )

        if not items:

            return (
                "A Steam não retornou itens "
                "disponíveis na wishlist."
            )

        # Ordena pelos mais recentemente adicionados
        items = sorted(
            items,
            key=lambda x: x.get(
                "date_added",
                0
            ),
            reverse=True
        )

        wishlist_games = []

        for item in items[:limit]:

            appid = item.get("appid")

            if not appid:
                continue

            appdetails_url = (
                "https://store.steampowered.com/"
                "api/appdetails"
            )

            app_response = requests.get(
                appdetails_url,
                params={
                    "appids": appid,
                    "cc": "br",
                    "l": "brazilian"
                },
                timeout=10
            )

            if app_response.status_code != 200:
                continue

            app_data = app_response.json()

            app_info = app_data.get(
                str(appid),
                {}
            )

            if not app_info.get("success"):
                continue

            game_data = app_info.get(
                "data",
                {}
            )

            game_name = game_data.get(
                "name"
            )

            if game_name:

                wishlist_games.append({
                    "appid": appid,
                    "name": game_name
                })

        if not wishlist_games:

            return (
                "A Steam retornou itens para a wishlist, "
                "mas não foi possível obter os nomes "
                "dos jogos."
            )

        output = [
            f"SteamID: {steam_id}",
            "",
            "--- WISHLIST DA STEAM ---"
        ]

        for game in wishlist_games:

            output.append(
                f"- {game['name']} "
                f"(appid: {game['appid']})"
            )

        return "\n".join(output)

    except requests.RequestException as err:

        return (
            f"Erro ao consultar a wishlist "
            f"da Steam: {err}"
        )

    except Exception as err:

        return (
            f"Erro ao processar a wishlist "
            f"da Steam: {err}"
        )


# =========================================================
# PREÇO DE UM JOGO
# =========================================================

def _fetch_game_price_data(appid: str) -> dict:
    """
    Busca informações de preço de um jogo na Steam Store,
    usando a região do Brasil.
    """

    appdetails_url = "https://store.steampowered.com/api/appdetails"

    params = {
        "appids": str(appid),
        "cc": "br",
        "l": "brazilian"
    }

    response = requests.get(
        appdetails_url,
        params=params,
        headers={"User-Agent": "GameAdvisor/1.0"},
        timeout=10
    )

    response.raise_for_status()

    data = response.json()
    app_data = data.get(str(appid), {})

    if not app_data.get("success"):
        return {
            "appid": str(appid),
            "available": False,
            "error": "Não foi possível obter os dados do jogo."
        }

    game_data = app_data.get("data", {})

    name = game_data.get("name", "Nome não disponível")
    price_overview = game_data.get("price_overview")

    # Jogo gratuito ou sem informação de preço
    if not price_overview:
        return {
            "appid": str(appid),
            "name": name,
            "available": False,
            "free": game_data.get("is_free", False),
            "current_price": None,
            "original_price": None,
            "discount_percent": 0
        }

    final_price = price_overview.get("final")
    initial_price = price_overview.get("initial")
    discount_percent = price_overview.get("discount_percent", 0)

    return {
        "appid": str(appid),
        "name": name,
        "available": True,
        "free": False,
        "current_price": final_price / 100 if final_price is not None else None,
        "original_price": initial_price / 100 if initial_price is not None else None,
        "discount_percent": discount_percent,
        "currency": price_overview.get("currency", "BRL")
    }


def get_game_price(appid: str) -> str:
    """
    Consulta o preço atual de um jogo na Steam Store.
    A região utilizada é o Brasil.
    """

    if not appid:
        return "Erro: AppID é obrigatório."

    try:
        data = _fetch_game_price_data(appid)

        if not data.get("available"):
            if data.get("free"):
                return (
                    f"Jogo: {data.get('name', 'Nome não disponível')}\n"
                    f"AppID: {appid}\n"
                    f"Preço: Grátis"
                )

            return (
                f"Jogo: {data.get('name', 'Nome não disponível')}\n"
                f"AppID: {appid}\n"
                f"Preço não disponível."
            )

        current_price = data["current_price"]
        original_price = data["original_price"]
        discount = data["discount_percent"]

        return (
            f"Jogo: {data['name']}\n"
            f"AppID: {appid}\n"
            f"Preço atual: R$ {current_price:.2f}".replace(".", ",") + "\n"
            f"Preço original: R$ {original_price:.2f}".replace(".", ",") + "\n"
            f"Desconto: {discount}%"
        )

    except requests.RequestException as err:
        return f"Erro ao consultar preço do jogo na Steam: {err}"

    except Exception as err:
        return f"Erro ao processar preço do jogo: {err}"


def get_wishlist_prices(steam_input: str, limit: int = 50) -> str:
    """
    Consulta a wishlist da Steam, obtém os preços dos jogos
    e identifica o jogo mais caro com preço disponível.

    O limite evita uma quantidade excessiva de chamadas à Steam Store.
    """

    try:
        steam_id = extract_or_resolve_steam_id(steam_input)

    except Exception as e:
        return f"Erro ao identificar conta Steam: {str(e)}"

    wishlist_url = (
        "https://api.steampowered.com/"
        "IWishlistService/GetWishlist/v0001/"
    )

    params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id
    }

    try:
        response = requests.get(
            wishlist_url,
            params=params,
            headers={"User-Agent": "GameAdvisor/1.0"},
            timeout=10
        )

        response.raise_for_status()

        data = response.json()
        response_data = data.get("response", {})

        items = response_data.get("items", [])

        if not items:
            return (
                "Não foi possível obter itens da wishlist da Steam. "
                "Isso não deve ser interpretado como wishlist vazia."
            )

        # Limita a quantidade de jogos consultados
        items = items[:limit]

        games = []

        for item in items:
            appid = item.get("appid")

            if not appid:
                continue

            try:
                price_data = _fetch_game_price_data(str(appid))

                games.append(price_data)

            except requests.RequestException:
                games.append({
                    "appid": str(appid),
                    "name": "Nome não disponível",
                    "available": False,
                    "error": "Erro ao consultar preço."
                })

            except Exception:
                games.append({
                    "appid": str(appid),
                    "name": "Nome não disponível",
                    "available": False,
                    "error": "Erro ao processar preço."
                })

        if not games:
            return "Não foi possível obter os jogos da wishlist."

        # Jogos que possuem preço numérico
        priced_games = [
            game
            for game in games
            if game.get("available")
            and game.get("current_price") is not None
        ]

        # Ordena do mais caro para o mais barato
        priced_games.sort(
            key=lambda game: game["current_price"],
            reverse=True
        )

        output = [
            f"SteamID: {steam_id}",
            "",
            "--- PREÇOS DA WISHLIST ---"
        ]

        for game in games:

            name = game.get("name", "Nome não disponível")
            appid = game.get("appid")

            if game.get("available"):

                current_price = game.get("current_price")
                original_price = game.get("original_price")
                discount = game.get("discount_percent", 0)

                current_formatted = (
                    f"R$ {current_price:.2f}".replace(".", ",")
                    if current_price is not None
                    else "Preço não disponível"
                )

                original_formatted = (
                    f"R$ {original_price:.2f}".replace(".", ",")
                    if original_price is not None
                    else "Preço não disponível"
                )

                output.append(
                    f"- {name} | AppID: {appid} | "
                    f"Atual: {current_formatted} | "
                    f"Original: {original_formatted} | "
                    f"Desconto: {discount}%"
                )

            elif game.get("free"):

                output.append(
                    f"- {name} | AppID: {appid} | "
                    f"Preço: Grátis"
                )

            else:

                output.append(
                    f"- {name} | AppID: {appid} | "
                    f"Preço não disponível"
                )

        output.append("")

        if priced_games:

            most_expensive = priced_games[0]

            price = most_expensive["current_price"]

            price_formatted = (
                f"R$ {price:.2f}".replace(".", ",")
            )

            output.append("--- JOGO MAIS CARO ---")

            output.append(
                f"Jogo: {most_expensive['name']}"
            )

            output.append(
                f"AppID: {most_expensive['appid']}"
            )

            output.append(
                f"Preço atual: {price_formatted}"
            )

            output.append(
                f"Desconto: "
                f"{most_expensive.get('discount_percent', 0)}%"
            )

        else:

            output.append(
                "Não foi possível determinar o jogo mais caro "
                "porque nenhum jogo retornou um preço numérico."
            )

        unavailable_count = len(games) - len(priced_games)

        if unavailable_count > 0:

            output.append("")

            output.append(
                f"Jogos sem preço numérico disponível: "
                f"{unavailable_count}"
            )

        return "\n".join(output)

    except requests.RequestException as err:

        return (
            f"Erro ao consultar a wishlist da Steam: {err}"
        )

    except Exception as err:

        return (
            f"Erro ao processar preços da wishlist: {err}"
        )



# ============================================================
# AMAZON BEDROCK KNOWLEDGE BASE
# ============================================================

KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")

bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.getenv(
        "AWS_DEFAULT_REGION",
        "us-east-2"
    )
)


def retrieve_game_reviews(
    query: str,
    number_of_results: int = 5
) -> dict:
    """
    Recupera reviews relevantes da GameAdvisor Knowledge Base.

    A ferramenta utiliza a API Retrieve do Amazon Bedrock
    Knowledge Bases e retorna os trechos recuperados
    para serem utilizados pelo agente como contexto.

    O agente é responsável por interpretar os resultados
    e formular a resposta final.
    """

    # --------------------------------------------------------
    # 1. Validar Knowledge Base ID
    # --------------------------------------------------------

    if not KNOWLEDGE_BASE_ID:

        raise RuntimeError(
            "A variável de ambiente "
            "KNOWLEDGE_BASE_ID não está configurada."
        )

    # --------------------------------------------------------
    # 2. Validar query
    # --------------------------------------------------------

    if not query or not isinstance(query, str):

        raise ValueError(
            "O parâmetro 'query' deve ser "
            "uma string não vazia."
        )

    query = query.strip()

    if not query:

        raise ValueError(
            "O parâmetro 'query' não pode estar vazio."
        )

    # --------------------------------------------------------
    # 3. Validar quantidade de resultados
    # --------------------------------------------------------

    try:

        number_of_results = int(
            number_of_results
        )

    except (TypeError, ValueError):

        raise ValueError(
            "O parâmetro 'number_of_results' "
            "deve ser um número inteiro."
        )

    # Limite de segurança
    if number_of_results < 1:

        number_of_results = 1

    if number_of_results > 10:

        number_of_results = 10

    # --------------------------------------------------------
    # 4. Logs
    # --------------------------------------------------------

    print("=" * 60)
    print("GAMEADVISOR RAG RETRIEVAL")
    print("=" * 60)

    print(
        f"Knowledge Base ID: "
        f"{KNOWLEDGE_BASE_ID}"
    )

    print(
        f"Query: {query}"
    )

    print(
        f"Number of results: "
        f"{number_of_results}"
    )

    # --------------------------------------------------------
    # 5. Consultar Knowledge Base
    # --------------------------------------------------------

    response = bedrock_agent_runtime.retrieve(

        knowledgeBaseId=KNOWLEDGE_BASE_ID,

        retrievalQuery={
            "text": query
        },

        retrievalConfiguration={

            "vectorSearchConfiguration": {

                "numberOfResults":
                    number_of_results
            }
        }
    )

    # --------------------------------------------------------
    # 6. Extrair resultados
    # --------------------------------------------------------

    retrieval_results = response.get(
        "retrievalResults",
        []
    )

    print(
        f"Resultados recuperados: "
        f"{len(retrieval_results)}"
    )

    # --------------------------------------------------------
    # 7. Formatar resultados
    # --------------------------------------------------------

    results = []

    for index, item in enumerate(
        retrieval_results,
        start=1
    ):

        content = item.get(
            "content",
            {}
        )

        text = content.get(
            "text",
            ""
        )

        score = item.get(
            "score"
        )

        location = item.get(
            "location",
            {}
        )

        source = None

        if isinstance(
            location,
            dict
        ):

            s3_location = location.get(
                "s3Location",
                {}
            )

            if isinstance(
                s3_location,
                dict
            ):

                source = s3_location.get(
                    "uri"
                )

        metadata = item.get(
            "metadata",
            {}
        )

        result = {

            "rank": index,

            "score": score,

            "text": text,

            "source": source,

            "metadata": metadata
        }

        results.append(
            result
        )

        # ----------------------------------------------------
        # Logs do resultado
        # ----------------------------------------------------

        print("-" * 60)

        print(
            f"Resultado #{index}"
        )

        print(
            f"Score: {score}"
        )

        print(
            f"Source: {source}"
        )

        print(
            f"Text preview: "
            f"{text[:300]}"
        )

    # --------------------------------------------------------
    # 8. Retorno
    # --------------------------------------------------------

    return {
        "query": query,

        "knowledge_base_id":
            KNOWLEDGE_BASE_ID,

        "number_of_results":
            len(results),

        "results":
            results
    }


def search_game_by_name(game_name: str) -> dict:
    """
    Busca um jogo pelo nome na Steam Store e retorna candidatos
    com nome e AppID.
    """

    if not game_name or not game_name.strip():
        return {
            "success": False,
            "error": "Nome do jogo não informado."
        }

    url = "https://store.steampowered.com/api/storesearch/"

    params = {
        "term": game_name.strip(),
        "cc": "br",
        "l": "brazilian"
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    items = data.get("items", [])

    if not items:
        return {
            "success": True,
            "query": game_name,
            "count": 0,
            "results": []
        }

    results = []

    for item in items[:10]:
        results.append({
            "appid": item.get("id"),
            "name": item.get("name"),
            "price": item.get("price", {})
        })

    return {
        "success": True,
        "query": game_name,
        "count": len(results),
        "results": results
    }
