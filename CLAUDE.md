# Contexto do projeto para o Claude — DM_Petrvs_icmbio_mysql

## 1. O que é este projeto

Projeto de análise direta dos dados do PETRVS via MySQL local + DBeaver, sem Docker, sem ETL e sem datamart intermediário. Disponibiliza consultas SQL e documentação para calcular os indicadores OCDE/PGD do ICMBio diretamente da base operacional.

Projeto relacionado (datamart completo com ETL e Superset): [DM_Petrvs_icmbio_postgre](https://github.com/lpchagas/DM_Petrvs_icmbio_postgre)

---

## 2. Stack tecnológica

| Componente | Detalhe |
|---|---|
| Banco de dados | MySQL Server 8.0 local (Windows) |
| Ferramenta de consulta | DBeaver Community |
| Docker | Não utilizado |
| Python/Flask | Não utilizado |

MySQL 8.0 é requisito mínimo obrigatório: os indicadores I05, I06, I07 e I08 usam window functions (`RANK()`, `SUM() OVER`) e CTEs recursivas, indisponíveis em versões anteriores.

---

## 3. Estrutura de arquivos

```
README.md                           Visão geral e início rápido

Consultas SQL/
  indicadores_ocde_pgd_icmbio_mysql_direto.sql   Queries para execução direta no DBeaver
  indicadores_ocde_pgd_icmbio_mysql_guiado.sql   Mesmo conteúdo, com comentários explicativos

docs/
  01-visao-geral.md                 Conceito, fluxo e diferença em relação ao projeto postgre
  02-restauracao-dump-petrvs.md     Como restaurar o dump MySQL localmente (sem Docker)
  03-acesso-direto-mysql-dbeaver.md Como conectar no MySQL via DBeaver + validações iniciais
  04-configuracao-dbeaver.md        Configuração detalhada do DBeaver
  05-contexto-ocde-pgd.md          Contexto estratégico dos indicadores OCDE/PGD
  06-indicadores-ocde-mysql.md     [LEGADO — será substituído pelos arquivos abaixo]
  07-estrutura-banco-dados.md      Arquitetura completa do banco PETRVS (técnico)
  08-guia-rapido-gestores.md       Início rápido para usuários de negócio (sem SQL)

  --- Reestruturação em andamento: manual técnico por eixo/indicador ---

  06.1-eixo1.md                    [CONCLUÍDO] Eixo 1 — Trabalho Remoto
  06.1.1-i01.md                    [CONCLUÍDO] I01 — Proporção por regime de trabalho

  06.2-eixo2.md                    [PENDENTE] Eixo 2 — Execução
  06.2.1-i02.md                    [PENDENTE] I02 — Taxa de cumprimento das entregas
  06.2.2-i03.md                    [PENDENTE] I03 — Taxa de cumprimento por entrega
  06.2.3-i04.md                    [PENDENTE] I04 — Índice de atingimento de metas

  06.3-eixo3.md                    [PENDENTE] Eixo 3 — Carga de Trabalho
  06.3.1-i05.md                    [PENDENTE] I05 — Distribuição de entregas por servidor
  06.3.2-i06.md                    [PENDENTE] I06 — Grau de responsabilidade por entrega
  06.3.3-i07.md                    [PENDENTE] I07 — Horas por entrega (absoluto)
  06.3.4-i08.md                    [PENDENTE] I08 — Proporção de horas por entrega (%)

  06.4-eixo4.md                    [CONCLUÍDO] Eixo 4 — Desempenho e Avaliação
  06.4.1-i09.md                    [CONCLUÍDO] I09 — Média da avaliação do PT por unidade
  06.4.2-i10.md                    [CONCLUÍDO] I10 — Percentual de avaliações inadequadas
  06.4.3-i11.md                    [CONCLUÍDO] I11 — Percentual de avaliações excepcionais
  06.4.4-i12.md                    [CONCLUÍDO] I12 — Coerência entre avaliação PT e PE

.gitignore
.vscode/settings.json
DM_Petrvs_icmbio_mysql.code-workspace
```

---

## 4. Fonte de dados — banco PETRVS MySQL

O banco restaurado se chama `petrvs_icmbio` (MySQL local, porta 3306).

### Tabelas da origem utilizadas pelas queries

| Tabela MySQL | Papel nos indicadores |
|---|---|
| `planos_entregas_entregas` | Entregas planejadas e realizadas (I02, I03, I04) |
| `planos_trabalhos_entregas` | Vínculo servidor × entrega (I05, I06, I07, I08) |
| `unidades` | Estrutura organizacional (join em todos os indicadores) |
| `usuarios` | Servidores (join quando necessário) |
| `planos_entregas` | Planos de entrega (contexto do ciclo) |
| `planos_trabalhos` | Planos de trabalho individuais |

### Campos críticos de mapeamento

| Conceito analítico | Campo MySQL |
|---|---|
| Nome da entrega | `COALESCE(NULLIF(TRIM(descricao),''), NULLIF(TRIM(descricao_entrega),''))` |
| Meta planejada | `progresso_esperado` |
| Meta executada | `progresso_realizado` |
| Entrega concluída | `progresso_realizado >= progresso_esperado` |
| Registro ativo | `deleted_at IS NULL` |
| Horas planejadas por servidor | `quantidade * horas_por_unidade` (em `planos_trabalhos_entregas`) |

---

## 5. Padrão das queries SQL

Todas as queries seguem o mesmo padrão de entrada: um bloco `parametros` no topo que concentra os filtros de data e comportamento.

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos   -- 0 = só ativos; 1 = inclui excluídos
)
```

Ajuste apenas os valores nesse bloco. O restante da query não precisa ser editado.

---

## 6. Indicadores disponíveis

| Indicador | Descrição | Tabela base |
|---|---|---|
| I02 | Taxa de cumprimento das entregas (por unidade) | `planos_entregas_entregas` |
| I03 | Taxa de cumprimento de metas por entrega (por entrega) | `planos_entregas_entregas` |
| I04 | Índice de atingimento de metas — score médio por unidade | `planos_entregas_entregas` |
| I05 | Distribuição das entregas entre os servidores | `planos_trabalhos_entregas` |
| I06 | Grau de responsabilidade pelas entregas | `planos_trabalhos_entregas` |
| I07 | Horas por entrega — planejadas (absolutas) | `planos_trabalhos_entregas` |
| I08 | Proporção de horas por entrega — planejadas (%) | `planos_trabalhos_entregas` |

O Indicador I01 (regimes de trabalho) depende de tabelas de modalidade não mapeadas neste projeto — não está implementado na versão MySQL.

---

## 7. Contexto de negócio — Indicadores OCDE/PGD ICMBio

Piloto OCDE/MGI/ICMBio/UFRN para transformar o PGD de controle de frequência em instrumento de gestão de desempenho. Alinhado às competências da Coordenação de Governança (CGOV), Portaria ICMBio nº 5.592/2025.

**4 eixos estruturantes:**

| Eixo | Foco |
|---|---|
| 1. Trabalho Remoto | Distribuição por regime (presencial/híbrido/remoto) |
| 2. Execução | Cumprimento de entregas e atingimento de metas |
| 3. Carga de Trabalho | Distribuição de esforço e horas por entrega |
| 4. Desempenho e Avaliação | Notas, coerência entre avaliações individuais e de unidade |

Contexto completo: [docs/05-contexto-ocde-pgd.md](docs/05-contexto-ocde-pgd.md)

---

## 8. Fluxo de trabalho padrão

```
1. Confirmar que MySQL 8.0 está rodando (Serviços Windows > MySQL80)
2. Confirmar que o banco petrvs_icmbio está restaurado
3. Abrir DBeaver > conexão MySQL > banco petrvs_icmbio
4. Abrir Consultas SQL/indicadores_ocde_pgd_icmbio_mysql_guiado.sql
5. Ajustar data_inicio e data_fim no bloco `parametros`
6. Executar o indicador desejado (buscar por I02, I03, etc.)
7. Exportar resultado (botão direito > Export > CSV/Excel)
```

---

## 9. Dump de origem

O arquivo de dump identificado no ambiente:
- Caminho: `C:\_dump\D.PGD.MGI.001.DUMP.20260226ICMBIO.sql`
- Banco de origem: `petrvs_icmbio`
- Versão MySQL de origem: 8.0.32
- Tamanho: superior a 4 GB
- Total de registros validado em `planos_entregas_entregas` (ativos): 14.727

O dump fica fora do repositório. Nunca versionar o arquivo de dump.

---

## 10. Regras importantes

- Nunca versionar dumps, credenciais ou dados pessoais.
- Sempre usar `deleted_at IS NULL` para filtrar registros ativos (soft-delete do PETRVS).
- O nome da entrega precisa do `COALESCE(descricao, descricao_entrega)` — ambos os campos podem estar preenchidos, vazios ou nulos conforme a versão do PETRVS.
- As queries usam CTEs encadeadas — execute a query completa, não partes isoladas.
- `progresso_esperado = 0` pode causar divisão por zero nos indicadores I03 e I04 — as queries já tratam com `NULLIF`.
- Para novos indicadores: seguir o padrão do bloco `parametros` e o estilo de nomeação das colunas já adotado (snake_case, sufixos `_perc`, `_total`, `_media`).

---

## 11. Estado do Projeto — Documentação (Atualização 28.04.2026)

### ✅ Concluído (Fase 1 - Exploração)

- **28.04.2026**: Exploração completa do banco de dados PETRVS
  - Conectado e validado: MySQL 8.0 local com dump restaurado (4 GB+)
  - Mapeadas 130+ tabelas do banco
  - Identificados relacionamentos (Foreign Keys) entre todas as tabelas
  - Documentada a arquitetura em 4 camadas:
    1. Camada de Referência (usuários, unidades, tipos)
    2. Camada de Planejamento (planos de entregas e trabalho)
    3. Camada de Execução (atividades, ocorrências, afastamentos)
    4. Camada de Avaliação & Resultado (avaliações, progressos, consolidações)
  - Padrões de design catalogados (soft-delete, UUID, ENUM, JSON, decimais)
  - **Novo doc criado**: `docs/07-estrutura-banco-dados.md` — Referência técnica completa

### ✅ Concluído (Fase 2 e 3 - Simplificação para Usuários de Negócio) — 28.04.2026

#### Fase 2 - Atualizar Referências

- [x] Atualizar `README.md` com referência ao doc 07 (técnico) e doc 08 (gestores)
- [x] Separar "início rápido" em dois caminhos: gestores (sem SQL) e analistas (setup técnico)

#### Fase 3 - Simplificar Documentação

- [x] Criar `docs/08-guia-rapido-gestores.md` — Guia completo sem SQL: todos os indicadores em linguagem de negócio, analogias ICMBio, tabela de interpretação, FAQ
- [x] Reescrever `01-visao-geral.md` — analogia PE/PT (contrato da unidade vs. agenda do servidor), mapa de tabelas, link para guia de gestores
- [x] Melhorar `02-restauracao-dump-petrvs.md` — resumo de etapas com tempo estimado, checklist final, seção de erros comuns expandida
- [x] Ajustar `03-acesso-direto-mysql-dbeaver.md` — link para guia de gestores, correção de formatação markdown
- [x] Analogias ICMBio incorporadas em `01-visao-geral.md` e `08-guia-rapido-gestores.md`
- [ ] Revisar seções técnicas de `06-indicadores-ocde-mysql.md` — doc já tem explicações detalhadas; pendente apenas verificar se há gaps de linguagem de negócio para usuários avançados

### ✅ Concluído (Fase 4 - Indicadores Completos e Correções de Lint) — 28.04.2026

- [x] Reescrever `docs/05-contexto-ocde-pgd.md` — todos os 12 indicadores com fórmulas, contexto, tabelas e status
- [x] Atualizar `docs/06-indicadores-ocde-mysql.md` — inserir I01 com queries de mapeamento e variante por unidade; inserir I09–I12 com queries de validação e consultas completas; corrigir MD031 (8 blocos de código sem linha em branco) e MD024 (15 headings duplicados)

### ✅ Concluído (Fase 5 - Reestruturação do doc 06 em manual técnico por eixo/indicador) — 29.04.2026

**Objetivo:** desdobrar `06-indicadores-ocde-mysql.md` em arquivos individuais por eixo (4 arquivos) e por indicador (12 arquivos), estruturando um manual técnico para servidores públicos que queiram implementar os indicadores OCDE a partir do dump PETRVS.

**Estrutura de cada arquivo de indicador:** (i) finalidade, (ii) consulta SQL completa, (iii) passos da consulta com explicações para usuários de negócio, (iv) como interpretar o resultado com exemplos do ICMBio.

**Arquivos criados nesta fase:**

- [x] `docs/06.4-eixo4.md` — Eixo 4: contexto estratégico, escala de avaliação, tabelas, pré-requisito de mapeamento, limitações
- [x] `docs/06.4.1-i09.md` — I09: média da avaliação do PT por unidade
- [x] `docs/06.4.2-i10.md` — I10: percentual de avaliações inadequadas (nota 2)
- [x] `docs/06.4.3-i11.md` — I11: percentual de avaliações excepcionais (nota 5)
- [x] `docs/06.4.4-i12.md` — I12: coerência entre avaliação do PT e do PE

**Pendente (retomar no próximo chat):**

- [x] `docs/06.1-eixo1.md` — Eixo 1: contexto, regime de trabalho, tabelas, consultas de mapeamento
- [x] `docs/06.1.1-i01.md` — I01: proporção por regime (variante geral + por unidade + snapshot ROW_NUMBER)
- [x] `docs/06.2-eixo2.md` — Eixo 2 (execução): contexto, tabelas, pré-requisito de auditoria, relação I02/I03/I04
- [x] `docs/06.2.1-i02.md` — I02: taxa de cumprimento das entregas por unidade (inclui registro de auditoria com 5 bugs corrigidos; validado com dados reais da APA-BALEFRA)
- [x] `docs/06.2.2-i03.md` — I03: taxa de cumprimento de metas por entrega (auditado e corrigido — mesmo Bug #5 do I02 mais 4 correções de documentação)
- [x] `docs/06.2.3-i04.md` — I04: índice de atingimento de metas — score médio por unidade
- [ ] `docs/06.3-eixo3.md` + I05, I06, I07, I08 — Eixo 3 (carga de trabalho) — **próximo a criar**
- [ ] Substituir `06-indicadores-ocde-mysql.md` por um índice navegável apontando para os novos arquivos

### 📋 Próximas Tarefas (Futuro)

- [ ] Validar campo `tipos_modalidades.nome` no banco e confirmar I01 com dados reais
- [ ] Validar campo numérico de `tipos_avaliacoes_notas` (pode ser `nota`, `valor` ou `pontuacao`) e confirmar I09–I12
- [ ] Criar exemplos visuais (diagramas, screenshots do DBeaver)
- [ ] Validar feriados móveis (Sexta da Paixão, Corpus Christi) — atualizar queries I07 e I08

---

## 12. Instruções para Continuar em Novo Chat

**Para retomar a reestruturação do manual técnico (Fase 5):**

1. Abrir este arquivo (`CLAUDE.md`) e ler a seção "Estado do Projeto — Documentação"
2. Ler os arquivos já criados como referência de tom e estrutura:
   - `docs/06.4-eixo4.md` (modelo de documento de eixo)
   - `docs/06.4.1-i09.md` (modelo de documento de indicador)
3. Continuar a partir do **Eixo 1**, na ordem:
   - Criar `docs/06.1-eixo1.md` — apresentar ao usuário para aprovação antes de prosseguir
   - Criar `docs/06.1.1-i01.md` — I01 (regime de trabalho, tabela `tipos_modalidades`)
   - Criar `docs/06.2-eixo2.md` + I02, I03, I04
   - Criar `docs/06.3-eixo3.md` + I05, I06, I07, I08
   - Por último: substituir `06-indicadores-ocde-mysql.md` por índice navegável
4. Aplicar sempre as **Medidas de Qualidade**:
   - (i) Dividir em subtarefas menores
   - (ii) Explicar passos antes de executar
   - (iii) Justificar decisões
   - (iv) Gerar múltiplas opções e escolher a melhor
5. Para cada documento de eixo: apresentar ao usuário para aprovação antes de criar os indicadores do eixo
6. Para cada indicador: criar individualmente, aguardar aprovação, depois avançar para o próximo

**Estrutura padrão de cada documento de indicador:**

- (i) Finalidade — o que a consulta faz, pergunta central respondida
- (ii) Consulta completa MySQL — seguindo o padrão `parametros` CTE
- (iii) Passos da consulta — um subitem por bloco CTE, com analogias para usuários de negócio
- (iv) Como interpretar o resultado — tabela de colunas + exemplos nomeados com unidades do ICMBio (CGOV, CGOF, AUDIT, DIREC, COGEO)

**Referência rápida do banco:**
- Banco: `petrvs_icmbio` (MySQL 8.0 local)
- Credenciais: user=`root`, password=`Bfz1614A#` (não commitar!)
- Tabelas críticas: `planos_entregas_entregas`, `planos_trabalhos_entregas`, `planos_trabalhos`, `planos_entregas`, `unidades`, `usuarios`
- Dump: `C:\_dump\D.PGD.MGI.001.DUMP.20260226ICMBIO.sql` (não versionar)
- Soft-delete: usar `deleted_at IS NULL` em queries
