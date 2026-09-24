import json
import requests
from requests_aws4auth import AWS4Auth
import boto3


REGION = "us-east-2"

GATEWAY_URL = (
    "https://gameadvisor-gateway-0jfvsrgazu"
    ".gateway.bedrock-agentcore.us-east-2.amazonaws.com/mcp"
)

STEAM_ID = "76561198844640485"


# ---------------------------------------------------------
# AWS SigV4
# ---------------------------------------------------------

session = boto3.Session(region_name=REGION)
credentials = session.get_credentials()

auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "bedrock-agentcore",
    session_token=credentials.token,
)


# ---------------------------------------------------------
# Função genérica para chamar MCP
# ---------------------------------------------------------

def call_tool(tool_name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "id": "test-tool",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-11-25",
    }

    response = requests.post(
        GATEWAY_URL,
        auth=auth,
        headers=headers,
        json=payload,
        timeout=30,
    )

    print("=" * 70)
    print(f"TOOL: {tool_name}")
    print(f"STATUS: {response.status_code}")
    print("=" * 70)

    print(response.text)

    print()

    return response

# ---------------------------------------------------------
# LISTAR TOOLS DO GATEWAY
# ---------------------------------------------------------

def list_tools():
    payload = {
        "jsonrpc": "2.0",
        "id": "list-tools-request",
        "method": "tools/list",
        "params": {},
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-11-25",
    }

    response = requests.post(
        GATEWAY_URL,
        auth=auth,
        headers=headers,
        json=payload,
        timeout=30,
    )

    print("=" * 70)
    print("TOOLS DISPONÍVEIS NO GATEWAY")
    print("=" * 70)
    print(response.text)
    print()

    return response


list_tools()
# ---------------------------------------------------------
# 1. Top games
# ---------------------------------------------------------

call_tool(
    "steamtools___get_user_top_games",
    {
        "steam_input": STEAM_ID,
        "limit": 5,
    },
)


# ---------------------------------------------------------
# 2. Recently played
# ---------------------------------------------------------

call_tool(
    "steamtools___get_recently_played_games",
    {
        "steam_input": STEAM_ID,
        "limit": 5,
    },
)


# ---------------------------------------------------------
# 3. Wishlist
# ---------------------------------------------------------

call_tool(
    "steamtools___get_wishlist",
    {
        "steam_input": STEAM_ID,
        "limit": 5,
    },
)


# ---------------------------------------------------------
# 4. Game price
# ---------------------------------------------------------

call_tool(
    "steamtools___get_game_price",
    {
        "appid": 22300,
    },
)


# ---------------------------------------------------------
# 5. Wishlist prices
# ---------------------------------------------------------

call_tool(
    "steamtools___getWishlistPrices",
    {
        "steam_input": STEAM_ID,
        "limit": 5,
    },
)

# ---------------------------------------------------------
# 6. Game reviews - Knowledge Base
# ---------------------------------------------------------

call_tool(
    "steamtools___retrieve_game_reviews",
    {
        "query": "Quais são os principais pontos negativos de Cities: Skylines?",
        "number_of_results": 5,
    },
)


