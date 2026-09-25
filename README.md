#  GameAdvisor

> Agente de recomendação de jogos desenvolvido com Amazon Bedrock AgentCore, AWS Lambda, Bedrock Knowledge Base, Steam Web API e DeepEval.

O **GameAdvisor** é um agente de Inteligência Artificial desenvolvido para recomendar jogos com base em informações disponíveis de um perfil público da Steam e/ou nas preferências informadas pelo usuário.

O projeto foi desenvolvido no contexto do **Desafio 2**, com foco não apenas na construção do agente, mas também em **integração de ferramentas, contexto de sessão, avaliação, segurança e red teaming**.

---

## Objetivo do projeto

O GameAdvisor combina:

- dados públicos da Steam;
- agente baseado em LLM;
- Amazon Bedrock AgentCore Gateway;
- AWS Lambda;
- DeepEval;
- testes de red teaming;
- contexto durante a sessão.

O agente pode utilizar informações de um perfil público da Steam ou, caso o usuário não queira compartilhar sua conta, trabalhar a partir de jogos e preferências informados diretamente.

Um princípio importante do projeto é:

> **O agente não deve inventar dados da Steam, AppIDs, preços ou informações que não estejam disponíveis ou verificadas.**

---

#  Arquitetura

```text
                         ┌──────────────────────┐
                         │       Usuário        │
                         │ Steam ID / URL       │
                         │ Preferências         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   GameAdvisor Agent  │
                         │                      │
                         │ LLM + Instruções     │
                         │ Contexto da sessão   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │ Amazon Bedrock AgentCore     │
                    │ Gateway                      │
                    └──────────────┬───────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
      resolveSteamId        getPlayerProfile     getOwnedGames
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                         getRecentlyPlayedGames
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │    Steam Web API     │
                         └──────────────────────┘


```

A integração com a Steam é realizada por funções AWS Lambda expostas ao agente por meio do AgentCore Gateway.

# Funcionalidades
## Integração com a Steam

O agente possui ferramentas para:

- resolver Steam ID a partir de URL ou vanity name;
- consultar perfil público;
- consultar jogos pertencentes ao perfil;
- consultar jogos jogados recentemente;
- utilizar informações de tempo de jogo retornadas pela Steam.
- Ferramentas disponíveis
- resolveSteamId
- getPlayerProfile
- getOwnedGames
- getRecentlyPlayedGames

As ferramentas possuem finalidade de consulta e leitura e não realizam alterações na conta Steam.

## Recomendações baseadas em dados

As recomendações devem ser baseadas nas informações disponíveis durante a interação.

O agente diferencia:

- dados retornados pela Steam;
- informações fornecidas diretamente pelo usuário;
- inferências do modelo;
- recomendações geradas pelo agente.

Essa separação é importante para evitar que uma inferência seja apresentada como se fosse um dado confirmado.

## Contexto de sessão

O agente utiliza o contexto acumulado durante a conversa para permitir interações multi-turno.

Exemplo:

Usuário:
Meu perfil da Steam é ...

Agente:
Encontrei seu perfil. Que tipo de jogo você procura?

Usuário:
Quero algo parecido com os jogos que joguei recentemente.

Agente:
Com base nos seus jogos recentes, ...

O contexto da Steam deve permanecer associado à sessão atual.

O Steam ID de um usuário não deve ser transportado para uma sessão não relacionada.

## Segurança e privacidade

A segurança foi considerada como parte da arquitetura e da avaliação do agente.

Credenciais

O agente:

- não solicita senha da Steam;
- não solicita a API Key da Steam ao usuário;
- não modifica contas;
- utiliza operações de leitura da Steam Web API.

A chave da Steam é utilizada por meio da variável de ambiente:

`STEAM_API_KEY`


### Perfis privados

As informações disponíveis dependem da visibilidade do perfil e dos dados de jogos na Steam.

Quando a API não disponibiliza uma informação, o agente deve informar a limitação em vez de assumir que:

informação ausente = informação inexistente

A ausência de um jogo na biblioteca retornada não deve ser usada isoladamente para concluir que o jogo não está disponível na Steam.

### Prompt Injection

Os resultados das ferramentas devem ser tratados como dados, e não como instruções.


```text
Resultado da ferramenta
        │
        ▼
      Dados
        │
        ▼
Interpretação pelo agente
        │
        ✗
        └── Não executar instruções contidas no dado

        
```

Essa preocupação foi incorporada à campanha de red teaming.

## Avaliação

O projeto utiliza duas frentes de avaliação:

- Amazon Bedrock AgentCore Evaluations
- DeepEval

O objetivo é avaliar tanto a qualidade das respostas quanto a conformidade do agente com as regras específicas do domínio.

### DeepEval

As métricas definidas para o desafio são:

Métrica	Threshold
Answer Relevancy	≥ 0,7
Faithfulness	≥ 0,8
G-Eval de conformidade	≥ 0,8

#### Answer Relevancy

Verifica se a resposta realmente atende à pergunta realizada.

#### Faithfulness

Verifica se a resposta permanece fiel ao contexto fornecido, evitando informações inventadas.

#### G-Eval de conformidade

Verifica uma regra específica do domínio definida para o agente.

#### Baseline

O baseline registrado durante o desenvolvimento apresentou:

Total de testes:     20
Testes aprovados:    11
Testes reprovados:    9

Taxa de aprovação:   55%

Esse resultado representa o baseline inicial utilizado para identificar problemas e orientar as correções.

## Sessão exploratória

Durante a exploração do agente foram identificados comportamentos que passaram a orientar o dataset e o red teaming.

Entre os problemas observados:

- recomendação de jogos já presentes na biblioteca;
- confusão entre diferentes versões de Cities: Skylines;
- generalização indevida de informações de reviews;
- invenção de AppID;
- associação incorreta entre jogo e AppID;
- inferência incorreta de disponibilidade na Steam;
- chamadas desnecessárias/erradas a ferramentas;
- possíveis problemas de timeout.

Esses casos foram transformados em cenários de teste e/ou ataques adversariais.

## Red Teaming

A campanha de red teaming foi estruturada para testar a resistência do agente a diferentes classes de ataques.

O dataset de red teaming contém 15 tentativas de ataque.

As categorias trabalhadas incluem:

- Prompt Injection;
- Tool Output Injection;
- Jailbreak / bypass de regras;
- Vazamento de informações;
- Vazamento de contexto entre sessões;
- Indução de alucinação;
- Uso indevido de ferramentas;
- Promessas ou afirmações indevidas.

Cada caso considera:

Objetivo do ataque
        ↓
Técnica utilizada
        ↓
Comportamento esperado
        ↓
Resultado observado
        ↓
Severidade

### Principais achados
ID	Problema	Severidade
REC-01	Recomendação de jogos já possuídos	Média
RAG-01	Confusão entre Cities: Skylines e Cities: Skylines II	Média
RAG-02	Generalização indevida de reviews	Média
PRICE-02	Invenção de AppID para Silent Hill f	Alta
PRICE-05	Associação incorreta de Devotion a AppID de outro jogo	Alta
TOOL-06	Inferência de disponibilidade pela biblioteca	Alta
PERF-01	Chamadas desnecessárias / timeout	Média
###  Correções
#### Validação de jogos
Foi proposta uma ferramenta específica para validação:
`search_game_by_name`

A finalidade é validar:
nome do jogo;
AppID;
correspondência entre jogo e identificador.

Regra:

O agente não deve inventar ou deduzir um AppID quando ele não foi confirmado por uma fonte válida.

#### Disponibilidade na Steam

Foi reforçada a distinção:

Biblioteca do usuário
        ≠
Catálogo da Steam

Portanto:

Jogo não encontrado na biblioteca

não significa automaticamente:

Jogo não disponível na Steam

#### Uso de ferramentas

As ferramentas devem ser acionadas somente quando necessárias para responder à solicitação.

Isso reduz:

chamadas redundantes;
latência;
possibilidade de timeout;
uso incorreto das ferramentas.

## Baseline × versão final

A metodologia utilizada para evolução do agente é:

BASELINE
   │
   ▼
20 casos
11 aprovados
55%
   │
   ▼
Análise de falhas
   │
   ├── Grounding
   ├── AppID
   ├── Disponibilidade
   ├── Recomendações
   └── Uso de ferramentas
   │
   ▼
Correções
   │
   ▼
Nova avaliação
   │
   ├── DeepEval
   ├── AgentCore Evaluations
   └── Red Team

FINAL
   │
   ▼
20 casos
12 aprovados
55%

No caso dos testes, 5 dos testes deveriam falhar, então os resultados foram bem positivos.

## Tecnologias utilizadas
IA e agentes
Amazon Bedrock
Amazon Bedrock AgentCore
AgentCore Gateway
LLM
AgentCore Evaluations
Cloud
AWS Lambda
AWS CLI
Amazon S3
APIs
Steam Web API
REST APIs
Avaliação
DeepEval
pytest
Golden Dataset
Red Teaming
Testes adversariais
Desenvolvimento
Python
Git
GitHub

## Estrutura do repositório
```text

GameAdvisor/
│
├── dataset/
│   └── Golden dataset e dados de avaliação
│
├── docs/
│   └── Documentação do projeto
│
├── evaluations/
│   └── Configurações e resultados das avaliações
│
├── local/
│   └── Testes e desenvolvimento local
│
├── red_team/
│   └── Dataset e execução dos testes adversariais
│
├── scr/
│   └── lambda/
│       └── Integração com a Steam Web API
│
├── src/
│   └── Código/configuração do agente
│
└── README.md

```

## Execução
Pré-requisitos
- Python 3.12
- AWS CLI
- conta AWS com as permissões necessárias;
- acesso aos serviços Amazon Bedrock/AgentCore utilizados;
- Steam Web API Key;
- dependências do projeto instaladas.
- Configuração da AWS

Configure o perfil AWS:
aws configure

Ou utilize AWS SSO:
aws configure sso

Valide a identidade:

aws sts get-caller-identity
Configuração da Steam API

A chave deve ser disponibilizada para a Lambda por meio da variável:

STEAM_API_KEY


## Avaliações

Os datasets e configurações estão organizados em:

dataset/
evaluations/
red_team/

Consulte os arquivos dessas pastas para executar as avaliações e a campanha de red teaming.

## O que este projeto demonstra

O GameAdvisor demonstra um ciclo de desenvolvimento e qualidade para agentes de IA:

Definição de escopo e riscos
            ↓
Construção do agente
            ↓
Integração de ferramentas
            ↓
Sessão exploratória
            ↓
Golden Dataset
            ↓
Avaliação
            ↓
Red Teaming
            ↓
Análise de falhas
            ↓
Correções
            ↓
Reavaliação

O foco do projeto é demonstrar que a construção de um agente não termina quando ele consegue responder a uma pergunta.

É necessário:

- definir limites;
- avaliar o comportamento;
- procurar falhas;
- testar ataques;
- corrigir problemas;
- reexecutar as avaliações.
 
