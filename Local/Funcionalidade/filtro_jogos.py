import json
import time
import requests

INPUT_FILE = "steam250_candidates.json"
OUTPUT_FILE = "popular_games_200.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

appids = data["appids"]

valid_games = []
rejected = []

for index, appid in enumerate(appids, start=1):

    print(f"[{index}/{len(appids)}] Verificando {appid}...")

    url = (
        "https://store.steampowered.com/api/appdetails"
        f"?appids={appid}&cc=br&l=brazilian"
    )

    try:
        response = requests.get(
            url,
            timeout=15
        )

        response.raise_for_status()

        result = response.json()

        app_data = result.get(str(appid))

        if not app_data:
            rejected.append({
                "appid": appid,
                "reason": "sem dados"
            })
            continue

        if not app_data.get("success"):
            rejected.append({
                "appid": appid,
                "reason": "Steam retornou success=false"
            })
            continue

        details = app_data.get("data", {})

        app_type = details.get("type")
        name = details.get("name")

        if app_type == "game":

            valid_games.append({
                "appid": appid,
                "name": name,
                "type": app_type
            })

            print(f"  ✓ JOGO: {name}")

        else:

            rejected.append({
                "appid": appid,
                "name": name,
                "type": app_type,
                "reason": "não é game"
            })

            print(
                f"  ✗ IGNORADO: {name} "
                f"(type={app_type})"
            )

    except Exception as e:

        rejected.append({
            "appid": appid,
            "reason": str(e)
        })

        print(f"  ✗ ERRO: {e}")

    # Evita bombardear a API
    time.sleep(1.5)

    # Para quando já temos 200 jogos válidos
    if len(valid_games) >= 200:
        break


# -----------------------------------------
# Salvar resultado
# -----------------------------------------

valid_games = valid_games[:200]

output = {
    "source": "SteamDB + Steam Store AppDetails",
    "description": "200 jogos classificados como type=game",
    "total_games": len(valid_games),
    "appids": [
        game["appid"]
        for game in valid_games
    ],
    "games": valid_games
}

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )


# -----------------------------------------
# Relatório
# -----------------------------------------

print("\n==============================")
print("RESULTADO")
print("==============================")

print(
    f"Jogos válidos: {len(valid_games)}"
)

print(
    f"Descartados: {len(rejected)}"
)

print(
    f"Arquivo: {OUTPUT_FILE}"
)
