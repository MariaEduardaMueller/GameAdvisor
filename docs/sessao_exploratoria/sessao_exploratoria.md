# Sessão exploratória — GameAdvisor
## Charter

- **Objetivo da sessão**: Explorar como o GameAdvisor reage a pedidos de recomendação, consultas de preço/wishlist e perguntas fora do domínio Steam.
- **Duração**: 60–90 min
- **Data**: 22/09/2026
- **Versão do agente testada**: versão 4

## Áreas exploradas

| Área | O que foi testado | Observações |
|---|---|---|
| Consulta direta (jogos mais jogados, recentes, wishlist) | Se o agente utilizava as tools corretas e acessava os dados ao invés de pegar dados da memória| Inventou dados e em alguns casos não realizava consultas com o tools |
| Preço/tarefa com ferramenta | Conferir preços por nome e id do jogo | Trouxe dados inventados ou errados sobre preços. Utizou ferramentas erradas ou desnecessárias. Utilizou dados da memória em vez de consulta a API |
| Multi-turno (contexto entre mensagens) | Consefir se ele continua com o perfil do usuário depois de algumas mensagens | Ele manteve os dados dos usuários e não apresentou nenhum problema |
| Fora de escopo | Perguntar sobre coisas não relacionadas a Steam ou jogos | Ele recusou responder e passou a informação que é um agente de recomendação de jogos e que deve receber perguntas sobre o escopo|

## Evidências
<img width="1421" height="643" alt="image" src="https://github.com/user-attachments/assets/43252ce6-34a8-4515-9777-af7eeb76fcf0" />



## Comportamentos suspeitos encontrados


### Respostas inventadas (alucinação)
- Inventou preços de jogos
- Inventou jogos para biblioteca do usuário
- Inventou/reutilizou AppID para outros jogos

### Recomendações desnecessárias
- SteamID sozinho gera recomendação não solicitada.
- O agente traz recomendação de jogos mesmo não sendo solicidado na conversa

### Falhas de recusa
- Quando você pergunta sobre o Steam API Key ou outras informações, ele diz que não conseguiu fazer ao invés de que não pode fazer.
- Se fosse pedido para o agente adicionar ou fazer alguma alteração na conta Steam do usuário, o agente respondia que "não conseguiu", ao invés de dizer que não pode fazer isso.

### Uso incorreto da ferramenta
- Recomenda jogos que já pertencem à biblioteca
- Utiliza a ferramenta errada para fazer a consulta
- Não chama a ferramenta se ele já possui dados na memória
- Chamadas desnecessárias / timeout
- Tentou usar ferramenta inexistente


### Vazamento de contexto entre turnos
- Ao criar uma nova sessão ele mantém o SteamID da sessão anterior.

## Resumo e próximos passos
Utilizei os dados obtidos na sessão exploratória para refinar o system prompt e também para os testes de evaluations e red team.
