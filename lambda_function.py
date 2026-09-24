import json

from steam_tools import (
    get_user_top_games,
    get_recently_played_games,
    get_wishlist,
    get_game_price,
    get_wishlist_prices,
    retrieve_game_reviews,
    search_game_by_name
)


def get_tool_name(event, context):
    """
    Obtém o nome da ferramenta.

    Para testes manuais da Lambda:
        event["tool"]

    Para chamadas pelo AgentCore Gateway:
        context.client_context.custom["bedrockAgentCoreToolName"]

    O nome pode vir no formato:
        targetName___toolName
    """

    # ---------------------------------------------------------
    # 1. TESTE MANUAL DA LAMBDA
    # ---------------------------------------------------------

    tool_from_event = event.get("tool")

    if tool_from_event:

        if "___" in tool_from_event:
            return tool_from_event.split("___", 1)[1]

        return tool_from_event

    # ---------------------------------------------------------
    # 2. CHAMADA PELO AGENTCORE GATEWAY
    # ---------------------------------------------------------

    try:

        if context.client_context and context.client_context.custom:

            custom = context.client_context.custom

            full_tool_name = custom.get(
                "bedrockAgentCoreToolName"
            )

            if full_tool_name:

                if "___" in full_tool_name:

                    return full_tool_name.split(
                        "___",
                        1
                    )[1]

                return full_tool_name

    except Exception as e:

        print(
            f"Erro ao identificar ferramenta pelo context: {e}"
        )

    return None


def lambda_handler(event, context):

    print("=== EVENT RECEIVED ===")

    print(
        json.dumps(
            event,
            ensure_ascii=False,
            default=str
        )
    )

    tool_name = get_tool_name(
        event,
        context
    )

    print("=== TOOL NAME ===")
    print(tool_name)

    try:

        # ---------------------------------------------------------
        # GET USER TOP GAMES
        # ---------------------------------------------------------

        if tool_name == "get_user_top_games":

            steam_input = event.get(
                "steam_input",
                ""
            )

            limit = event.get(
                "limit",
                15
            )

            result = get_user_top_games(
                steam_input=steam_input,
                limit=limit
            )

        # ---------------------------------------------------------
        # GET RECENTLY PLAYED GAMES
        # ---------------------------------------------------------

        elif tool_name == "get_recently_played_games":

            steam_input = event.get(
                "steam_input",
                ""
            )

            limit = event.get(
                "limit",
                5
            )

            result = get_recently_played_games(
                steam_input=steam_input,
                limit=limit
            )
            
        elif tool_name == "search_game_by_name":
            result = search_game_by_name(
                event.get("game_name")
            )
        # ---------------------------------------------------------
        # GET WISHLIST
        # ---------------------------------------------------------

        elif tool_name == "get_wishlist":

            steam_input = event.get(
                "steam_input",
                ""
            )

            limit = event.get(
                "limit",
                250
            )

            result = get_wishlist(
                steam_input=steam_input,
                limit=limit
            )

        # ---------------------------------------------------------
        # GET WISHLIST PRICES
        # ---------------------------------------------------------

        elif tool_name == "getWishlistPrices":

            steam_input = event.get(
                "steam_input",
                ""
            )

            limit = event.get(
                "limit",
                50
            )

            result = get_wishlist_prices(
                steam_input=steam_input,
                limit=limit
            )

        # ---------------------------------------------------------
        # GET GAME PRICE
        # ---------------------------------------------------------

        elif tool_name == "get_game_price":

            appid = event.get("appid")

            if appid is None:

                raise ValueError(
                    "O parâmetro 'appid' é obrigatório."
                )

            result = get_game_price(
                appid=int(appid)
            )

        # ---------------------------------------------------------
        # RETRIEVE GAME REVIEWS
        # ---------------------------------------------------------

        elif tool_name == "retrieve_game_reviews":

            query = event.get("query")

            number_of_results = event.get(
                "number_of_results",
                5
            )

            result = retrieve_game_reviews(
                query=query,
                number_of_results=number_of_results
            )

        # ---------------------------------------------------------
        # UNKNOWN TOOL
        # ---------------------------------------------------------

        else:

            raise ValueError(
                f"Ferramenta não reconhecida: {tool_name}"
            )

        # ---------------------------------------------------------
        # SUCCESS
        # ---------------------------------------------------------

        response = {
            "success": True,
            "tool": tool_name,
            "result": result
        }

        print("=== RESPONSE ===")

        print(
            json.dumps(
                response,
                ensure_ascii=False,
                default=str
            )
        )

        return response

    # ---------------------------------------------------------
    # ERROR
    # ---------------------------------------------------------

    except Exception as e:

        print("=== ERROR ===")
        print(str(e))

        return {
            "success": False,
            "tool": tool_name,
            "error": str(e)
        }