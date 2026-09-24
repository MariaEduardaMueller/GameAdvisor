import json
import re
import time

import requests
from bs4 import BeautifulSoup


URL = "https://steam250.com/most_played.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )
}


# ==========================================
# 1. Baixar ranking Steam250
# ==========================================

print("Baixando ranking...")

response = requests.get(
    URL,
    headers=HEADERS,
    timeout=30
)

response.raise_for_status()

print("Status:", response.status_code)


# ==========================================
# 2. Extrair links /app/XXXX/
# ==========================================

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

appids = []

for link in soup.find_all("a", href=True):

    href = link["href"]

    match = re.search(
        r"/app/(\d+)",
        href
    )

    if match:

        appid = int(match.group(1))

        if appid not in appids:
            appids.append(appid)


print(
    f"AppIDs encontrados: {len(appids)}"
)

print(
    "Primeiros IDs:",
    appids[:20]
)


# ==========================================
# 3. Salvar candidatos
# ==========================================

with open(
    "steam250_candidates.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "source": URL,
            "appids": appids
        },
        f,
        indent=2,
        ensure_ascii=False
    )


print(
    "Arquivo criado: steam250_candidates.json"
)
