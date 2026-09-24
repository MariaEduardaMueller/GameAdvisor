import json
import re
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")

BUCKET = "gameadvisor-kb-s3"

RAW_PREFIX = "raw-reviews/"
PROCESSED_PREFIX = "processed-reviews/"
CATALOG_KEY = "game-catalog/popular_games_200.json"

DEFAULT_BATCH_SIZE = 10


# ============================================================
# CATÁLOGO DE JOGOS
# ============================================================

def load_game_catalog():

    print(f"Carregando catálogo: s3://{BUCKET}/{CATALOG_KEY}")

    response = s3.get_object(
        Bucket=BUCKET,
        Key=CATALOG_KEY
    )

    data = json.loads(
        response["Body"].read().decode("utf-8")
    )

    catalog = {}

    for game in data.get("games", []):

        appid = str(game.get("appid"))
        name = game.get("name")

        if appid and name:
            catalog[appid] = name

    print(
        f"Jogos carregados no catálogo: {len(catalog)}"
    )

    return catalog


# ============================================================
# EXTRAIR APPID
# ============================================================

def extract_appid_from_key(key):

    match = re.search(
        r"appid-(\d+)",
        key
    )

    if not match:
        raise ValueError(
            f"Não foi possível identificar o AppID na chave: {key}"
        )

    return match.group(1)


# ============================================================
# IDENTIFICAR APPIDS JÁ PROCESSADOS
# ============================================================

def get_processed_appids():

    processed_appids = set()

    paginator = s3.get_paginator(
        "list_objects_v2"
    )

    for page in paginator.paginate(
        Bucket=BUCKET,
        Prefix=PROCESSED_PREFIX
    ):

        for obj in page.get(
            "Contents",
            []
        ):

            key = obj["Key"]

            match = re.search(
                r"processed-reviews/appid-(\d+)/_processed\.txt$",
                key
            )

            if match:

                processed_appids.add(
                    match.group(1)
                )

    print(
        f"AppIDs encontrados com marcador: "
        f"{len(processed_appids)}"
    )

    return processed_appids


# ============================================================
# PROCESSAR UMA REVIEW
# ============================================================

def process_review(review, appid, game_name, index):
    language = review.get("language", "unknown")

    recommendation = review.get("voted_up", None)

    if recommendation is True:
        recommendation_text = "recommended"
    elif recommendation is False:
        recommendation_text = "not recommended"
    else:
        recommendation_text = "unknown"

    # Trata playtime_forever ausente ou None
    playtime_minutes = (
        review
        .get("author", {})
        .get("playtime_forever", 0)
    )

    if playtime_minutes is None:
        playtime_minutes = 0

    playtime_hours = round(
        playtime_minutes / 60,
        1
    )

    review_text = review.get("review", "").strip()

    content = (
        f"Game: {game_name}\n"
        f"AppID: {appid}\n"
        f"Language: {language}\n"
        f"Recommendation: {recommendation_text}\n"
        f"Playtime hours: {playtime_hours}\n"
        f"\n"
        f"Review:\n"
        f"{review_text}\n"
    )

    return content

    
# ============================================================
# PROCESSAR ARQUIVO RAW
# ============================================================

def process_file(
    key,
    game_catalog
):

    print("=" * 60)
    print(f"Processando arquivo: {key}")
    print("=" * 60)

    appid = extract_appid_from_key(key)

    game_name = game_catalog.get(
        appid,
        f"Steam Game {appid}"
    )

    print(f"AppID: {appid}")
    print(f"Game: {game_name}")

    # --------------------------------------------------------
    # LER RAW
    # --------------------------------------------------------

    response = s3.get_object(
        Bucket=BUCKET,
        Key=key
    )

    data = json.loads(
        response["Body"].read().decode("utf-8")
    )

    reviews = data.get(
        "reviews",
        []
    )

    print(
        f"Reviews encontradas: {len(reviews)}"
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    processed_count = 0

    # --------------------------------------------------------
    # CRIAR TXT DE CADA REVIEW
    # --------------------------------------------------------

    for index, review in enumerate(reviews):

        content = process_review(
            review=review,
            appid=appid,
            game_name=game_name,
            index=index
        )

        output_key = (
            f"{PROCESSED_PREFIX}"
            f"appid-{appid}/"
            f"review-{index:03d}.txt"
        )

        s3.put_object(
            Bucket=BUCKET,
            Key=output_key,
            Body=content.encode("utf-8"),
            ContentType="text/plain; charset=utf-8"
        )

        processed_count += 1

    print(
        f"Reviews processadas: {processed_count}"
    )

    # --------------------------------------------------------
    # CRIAR MARCADOR
    # --------------------------------------------------------

    marker_key = (
        f"{PROCESSED_PREFIX}"
        f"appid-{appid}/"
        f"_processed.txt"
    )

    marker_content = (
        f"Game: {game_name}\n"
        f"AppID: {appid}\n"
        f"Reviews processed: {processed_count}\n"
        f"Processed at: {timestamp}\n"
        f"Source: {key}\n"
    )

    s3.put_object(
        Bucket=BUCKET,
        Key=marker_key,
        Body=marker_content.encode("utf-8"),
        ContentType="text/plain; charset=utf-8"
    )

    print(
        f"Marcador criado: {marker_key}"
    )

    return {
        "source": key,
        "appid": appid,
        "game_name": game_name,
        "reviews_processed": processed_count,
        "output_prefix":
            f"{PROCESSED_PREFIX}appid-{appid}/",
        "processed_at": timestamp,
        "status": "success"
    }


# ============================================================
# LISTAR ARQUIVOS RAW
# ============================================================

def list_raw_files():

    files = []

    paginator = s3.get_paginator(
        "list_objects_v2"
    )

    for page in paginator.paginate(
        Bucket=BUCKET,
        Prefix=RAW_PREFIX
    ):

        for obj in page.get(
            "Contents",
            []
        ):

            key = obj["Key"]

            if key.endswith(".json"):

                files.append(key)

    return files


# ============================================================
# LAMBDA HANDLER
# ============================================================

def lambda_handler(
    event,
    context
):

    print("=" * 60)
    print("GAMEADVISOR PROCESSOR")
    print("=" * 60)

    print("EVENT:")

    print(
        json.dumps(
            event,
            ensure_ascii=False
        )
    )

    # --------------------------------------------------------
    # CARREGAR CATÁLOGO
    # --------------------------------------------------------

    game_catalog = load_game_catalog()

    # --------------------------------------------------------
    # LISTAR RAW
    # --------------------------------------------------------

    raw_files = list_raw_files()

    raw_files.sort()

    print(
        f"Total de arquivos RAW encontrados: "
        f"{len(raw_files)}"
    )

    # --------------------------------------------------------
    # IDENTIFICAR PROCESSADOS
    # --------------------------------------------------------

    processed_appids = get_processed_appids()

    processed_count = len(
        processed_appids
    )

    print(
        f"Total de AppIDs já processados: "
        f"{processed_count}"
    )

    # --------------------------------------------------------
    # IDENTIFICAR PENDENTES
    # --------------------------------------------------------

    pending_files = []

    for key in raw_files:

        appid = extract_appid_from_key(
            key
        )

        if appid not in processed_appids:

            pending_files.append(
                key
            )

    print(
        f"Total de arquivos RAW pendentes: "
        f"{len(pending_files)}"
    )

    # --------------------------------------------------------
    # BATCH
    # --------------------------------------------------------

    batch_size = int(
        event.get(
            "batch_size",
            DEFAULT_BATCH_SIZE
        )
    )

    if batch_size < 1:

        raise ValueError(
            "batch_size deve ser >= 1."
        )

    files_to_process = (
        pending_files[:batch_size]
    )

    print(
        f"Arquivos selecionados nesta execução: "
        f"{len(files_to_process)}"
    )

    # --------------------------------------------------------
    # PROCESSAR
    # --------------------------------------------------------

    results = []

    for key in files_to_process:

        try:

            result = process_file(
                key,
                game_catalog
            )

            results.append(
                result
            )

        except Exception as e:

            print(
                f"[ERROR] Falha processando "
                f"{key}: {str(e)}"
            )

            results.append({
                "source": key,
                "status": "error",
                "error": str(e)
            })

    # --------------------------------------------------------
    # ESTATÍSTICAS
    # --------------------------------------------------------

    successful = sum(
        1
        for result in results
        if result.get("status") == "success"
    )

    failed = sum(
        1
        for result in results
        if result.get("status") == "error"
    )

    remaining = (
        len(pending_files)
        - len(files_to_process)
    )

    # --------------------------------------------------------
    # RESPOSTA
    # --------------------------------------------------------

    response = {

        "statusCode": 200,

        "total_raw_files":
            len(raw_files),

        "already_processed":
            processed_count,

        "pending_before_execution":
            len(pending_files),

        "processed_this_execution":
            successful,

        "failed_this_execution":
            failed,

        "remaining_after_execution":
            remaining,

        "results":
            results
    }

    print("=" * 60)
    print("FINAL RESPONSE")
    print("=" * 60)

    print(
        json.dumps(
            response,
            ensure_ascii=False,
            indent=2
        )
    )

    return response