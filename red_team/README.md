# Red Team

Esta pasta contém os testes de segurança e robustez
realizados no GameAdvisor.

## Objetivo

Avaliar o comportamento do agente diante de tentativas de:

- prompt injection;
- tool output injection;
- credential extraction;
- operações não suportadas;
- manipulação de contexto;
- recomendações inseguras;
- vazamento entre sessões;
- identificadores inventados ou inconsistentes.

## Dataset

`red_team_dataset.jsonl` contém os 15 casos de ataque.

Cada caso define:

- ID;
- categoria;
- ataque;
- objetivo;
- comportamento esperado;
- severidade.

## Execução

```bash
python red_team/run_red_team.py
