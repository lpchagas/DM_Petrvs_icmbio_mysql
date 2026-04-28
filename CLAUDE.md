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
  06-indicadores-ocde-mysql.md     Documentação das queries + explicação de cada indicador

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
