import json
import os
import re
import uuid
from pathlib import Path

import boto3


# ============================================================
# CONFIGURAÇÕES
# ============================================================

REGION = os.getenv(
    "AWS_DEFAULT_REGION",
    "us-east-2",
)

HARNESS_ARN = os.getenv(
    "HARNESS_ARN",
    "arn:aws:bedrock-agentcore:us-east-2:737634035154:"
    "harness/GameAdvisor_Desafio2-q7z7exq1Vx",
)

TEST_STEAM_ID = os.getenv(
    "TEST_STEAM_ID",
    "76561198844640485",
)

DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "dataset"
    / "red_team_dataset.jsonl"
)

RESULTS_PATH = (
    Path(__file__).resolve().parent
    / "results.jsonl"
)


# ============================================================
# CLIENTE AGENTCORE
# ============================================================

agentcore_client = boto3.client(
    "bedrock-agentcore",
    region_name=REGION,
)


# ============================================================
# LIMPAR OUTPUT
# ============================================================

def clean_agent_output(text):
    """
    Remove blocos de <thinking>...</thinking> do output
    antes de salvar a resposta final.
    """

    text = re.sub(
        r"<thinking>.*?</thinking>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return text.strip()


# ============================================================
# INVOCAR AGENTCORE HARNESS
# ============================================================

def invoke_agent(prompt, session_id):

    response = agentcore_client.invoke_harness(
        harnessArn=HARNESS_ARN,
        qualifier="DEFAULT",
        runtimeSessionId=session_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
    )

    output_parts = []

    for event in response["stream"]:

        # ----------------------------------------------------
        # Texto da resposta
        # ----------------------------------------------------

        if "contentBlockDelta" in event:

            delta = event["contentBlockDelta"].get(
                "delta",
                {}
            )

            if "text" in delta:
                output_parts.append(
                    delta["text"]
                )

        # ----------------------------------------------------
        # Erro do Runtime
        # ----------------------------------------------------

        elif "runtimeClientError" in event:

            raise RuntimeError(
                event["runtimeClientError"].get(
                    "message",
                    "Erro no AgentCore Runtime."
                )
            )

        # ----------------------------------------------------
        # Erro de validação
        # ----------------------------------------------------

        elif "validationException" in event:

            raise RuntimeError(
                event["validationException"].get(
                    "message",
                    "Erro de validação no AgentCore."
                )
            )

    raw_output = "".join(
        output_parts
    ).strip()

    return clean_agent_output(
        raw_output
    )


# ============================================================
# CARREGAR DATASET
# ============================================================

def load_dataset():

    cases = []

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:

                case = json.loads(line)

                cases.append(case)

            except json.JSONDecodeError as error:

                raise ValueError(
                    f"Erro no JSONL na linha "
                    f"{line_number}: {error}"
                )

    return cases


# ============================================================
# SALVAR RESULTADO
# ============================================================

def save_result(result):

    with open(
        RESULTS_PATH,
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                result,
                ensure_ascii=False,
            )
            + "\n"
        )


# ============================================================
# EXECUTAR CASO NORMAL
# ============================================================

def run_single_case(case):

    case_id = case["id"]

    print(
        f"[{case_id}] Executando caso normal..."
    )

    # Cada ataque normal recebe uma nova sessão
    session_id = (
        f"redteam-{uuid.uuid4()}"
    )

    setup_output = None

    # --------------------------------------------------------
    # CONTEXTO OPCIONAL
    # --------------------------------------------------------

    context = case.get(
        "context"
    )

    if context and context.get(
        "steam_id"
    ):

        steam_id = context[
            "steam_id"
        ]

        # Substitui placeholder pelo SteamID
        # de teste real.
        steam_id = steam_id.replace(
            "<STEAM_ID_DE_TESTE>",
            TEST_STEAM_ID,
        )

        setup_prompt = (
            f"Meu SteamID é {steam_id}."
        )

        print(
            "  → Enviando contexto da conta..."
        )

        setup_output = invoke_agent(
            setup_prompt,
            session_id,
        )

    # --------------------------------------------------------
    # ATAQUE
    # --------------------------------------------------------

    attack = case[
        "attack"
    ]

    print(
        "  → Executando ataque..."
    )

    actual_output = invoke_agent(
        attack,
        session_id,
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    result = {
        "id": case_id,
        "category": case.get(
            "category"
        ),
        "attack": attack,
        "objective": case.get(
            "objective"
        ),
        "expected_result": case.get(
            "expected_result"
        ),
        "severity": case.get(
            "severity"
        ),
        "session_id": session_id,
        "setup_output": setup_output,
        "actual_output": actual_output,
        "status": "EXECUTED",
    }

    save_result(
        result
    )

    print(
        "  ✓ Executado"
    )

    print(
        f"  Resposta: {actual_output}"
    )


# ============================================================
# TESTE DE ISOLAMENTO ENTRE SESSÕES
# ============================================================

def run_cross_session_test(case):

    print(
        f"[{case['id']}] "
        "Teste de isolamento entre sessões"
    )

    # ========================================================
    # SESSÃO A
    # ========================================================

    session_a = (
        f"redteam-a-{uuid.uuid4()}"
    )

    setup_prompt = (
        f"Meu SteamID é {TEST_STEAM_ID}."
    )

    print(
        "  → Sessão A: fornecendo SteamID..."
    )

    setup_output = invoke_agent(
        setup_prompt,
        session_a,
    )

    print(
        "  ✓ Sessão A concluída."
    )

    # ========================================================
    # SESSÃO B
    # ========================================================

    session_b = (
        f"redteam-b-{uuid.uuid4()}"
    )

    attack = case[
        "attack"
    ]

    print(
        "  → Sessão B: executando ataque..."
    )

    attack_output = invoke_agent(
        attack,
        session_b,
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    result = {
        "id": case["id"],
        "category": case.get(
            "category"
        ),
        "attack": attack,
        "objective": case.get(
            "objective"
        ),
        "expected_result": case.get(
            "expected_result"
        ),
        "severity": case.get(
            "severity"
        ),
        "session_a": session_a,
        "session_b": session_b,
        "setup_output": setup_output,
        "actual_output": attack_output,
        "status": "EXECUTED",
    }

    save_result(
        result
    )

    print(
        "  ✓ Teste concluído."
    )

    print(
        f"  Resposta da Sessão B: "
        f"{attack_output}"
    )


# ============================================================
# EXECUTAR RED TEAM
# ============================================================

def run_red_team():

    cases = load_dataset()

    print()
    print("=" * 70)
    print("GAMEADVISOR — RED TEAM")
    print("=" * 70)

    print(
        f"Dataset: {DATASET_PATH}"
    )

    print(
        f"Casos encontrados: {len(cases)}"
    )

    print(
        f"Results: {RESULTS_PATH}"
    )

    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Limpar resultados anteriores
    # --------------------------------------------------------

    if RESULTS_PATH.exists():

        RESULTS_PATH.unlink()

        print(
            "Resultados anteriores removidos."
        )

        print()

    # --------------------------------------------------------
    # Executar casos
    # --------------------------------------------------------

    for index, case in enumerate(
        cases,
        start=1,
    ):

        print(
            f"[{index}/{len(cases)}] "
            f"{case['id']} — "
            f"{case.get('category', 'unknown')}"
        )

        try:

            # ------------------------------------------------
            # TESTES DE ISOLAMENTO
            # ------------------------------------------------

            if case["id"] in [
                "RT-09",
                "RT-10",
            ]:

                run_cross_session_test(
                    case
                )

            # ------------------------------------------------
            # DEMAIS TESTES
            # ------------------------------------------------

            else:

                run_single_case(
                    case
                )

        except Exception as error:

            print(
                f"  ✗ ERRO: {error}"
            )

            result = {
                "id": case.get(
                    "id"
                ),
                "category": case.get(
                    "category"
                ),
                "attack": case.get(
                    "attack"
                ),
                "objective": case.get(
                    "objective"
                ),
                "expected_result": case.get(
                    "expected_result"
                ),
                "severity": case.get(
                    "severity"
                ),
                "actual_output": None,
                "error": str(
                    error
                ),
                "status": "ERROR",
            }

            save_result(
                result
            )

        print()
        print("-" * 70)
        print()

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print("=" * 70)
    print("RED TEAM FINALIZADO")
    print("=" * 70)

    print(
        f"Resultados salvos em:"
    )

    print(
        RESULTS_PATH
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_red_team()
