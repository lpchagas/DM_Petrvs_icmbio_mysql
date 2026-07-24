# I03 — Taxa de Cumprimento de Metas por Entrega — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_03.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Mede a taxa de cumprimento de metas por entrega individual (`meta_executada /
meta_planejada * 100`), considerando as entregas cujo prazo (`pee.data_fim`)
**vence dentro do período** consultado — diferente do I02, que olha a vigência
do PE.

## 2. Pré-requisitos

- IP da máquina liberado pelo Dataprev; driver JDBC instalado (ver CLAUDE.md seção 2).
- Notebook `consultas_denodo.ipynb` (raiz do projeto) aberto no VS Code.
- Célula 2 (conexão) já configurada localmente com usuário/senha do Denodo —
  **não copie credenciais para este arquivo**; ver CLAUDE.md seção 2
  (arquivo local, não versionado).

## 3. Instrumento e periodicidade

- Instrumento: **Plano de Entregas (PE)** → `build_periods_pe()`.
- Regra vigente: 2025 trimestral (T3–T4, H1/2025 excluído) | 2026+ quadrimestral (Q1–Q3).
  Base: 01/07/2025.

Períodos vigentes em 24.07.2026 (recalcular com `build_periods_pe()` se datas futuras):

| Período | Tipo | Início | Fim | Status |
|---|---|---|---|---|
| T3-2025 | trimestral | 2025-07-01 | 2025-09-30 | encerrado |
| T4-2025 | trimestral | 2025-10-01 | 2025-12-31 | encerrado |
| Q1-2026 | quadrimestral | 2026-01-01 | 2026-04-30 | encerrado |
| Q2-2026 | quadrimestral | 2026-05-01 | 2026-08-31 | em_andamento |

## 4. Query SQL_I03

Exemplo com o primeiro período (T3-2025) preenchido — troque as datas de
`parametros` a cada rodada.

```sql
WITH parametros AS (
    SELECT
        CAST('2025-07-01' AS DATE) AS data_inicio,
        CAST('2025-09-30' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
entregas_base AS (
    SELECT
        u.sigla AS unidade_sigla,
        u.nome  AS unidade_nome,
        pee.id  AS id_entrega,
        COALESCE(
            NULLIF(TRIM(pee.descricao), ''),
            NULLIF(TRIM(pee.descricao_entrega), ''),
            'N.I.'
        ) AS nome_entrega,
        COALESCE(NULLIF(TRIM(pee.descricao_entrega), ''), 'N.I.') AS descricao_entrega,
        pee.progresso_esperado AS progresso_esperado_bruto,
        CASE
            WHEN pee.progresso_esperado > 0 AND pee.progresso_esperado <= 1
            THEN pee.progresso_esperado * 100
            ELSE pee.progresso_esperado
        END AS meta_planejada,
        COALESCE(pee.progresso_realizado, 0) AS meta_executada,
        pee.meta      AS meta_json,
        pee.realizado AS realizado_json
    FROM petrvs_icmbio_planos_entregas pe
    JOIN petrvs_icmbio_planos_entregas_entregas pee
        ON pee.plano_entrega_id = pe.id
    JOIN petrvs_icmbio_unidades u
        ON u.id = pe.unidade_id
    CROSS JOIN parametros p
    WHERE CAST(pee.data_fim AS DATE) BETWEEN p.data_inicio AND p.data_fim
      AND (p.incluir_excluidos = 1 OR pe.deleted_at  IS NULL)
      AND (p.incluir_excluidos = 1 OR pee.deleted_at IS NULL)
      AND pee.progresso_esperado IS NOT NULL
      AND pee.progresso_esperado > 0
),
entregas_com_taxa AS (
    SELECT
        unidade_sigla,
        unidade_nome,
        id_entrega,
        nome_entrega,
        descricao_entrega,
        progresso_esperado_bruto,
        CASE
            WHEN progresso_esperado_bruto > 0 AND progresso_esperado_bruto <= 1
            THEN 'S'
            ELSE 'N'
        END AS anomalia_escala,
        meta_planejada,
        meta_executada,
        ROUND(meta_executada / NULLIF(meta_planejada, 0) * 100, 2) AS taxa_atingimento_perc,
        meta_json,
        realizado_json
    FROM entregas_base
)
SELECT
    unidade_sigla,
    unidade_nome,
    id_entrega,
    nome_entrega,
    descricao_entrega,
    progresso_esperado_bruto,
    anomalia_escala,
    meta_planejada,
    meta_executada,
    taxa_atingimento_perc,
    CASE
        WHEN taxa_atingimento_perc <    0 THEN 'Dado inconsistente'
        WHEN taxa_atingimento_perc >  100 THEN 'Superexecutada'
        WHEN taxa_atingimento_perc =  100 THEN 'Concluida'
        WHEN taxa_atingimento_perc >= 70  THEN 'Parcialmente cumprida'
        WHEN taxa_atingimento_perc >    0 THEN 'Em andamento'
        ELSE                                   'Nao executada'
    END AS status_entrega,
    meta_json,
    realizado_json
FROM entregas_com_taxa
ORDER BY unidade_sigla, taxa_atingimento_perc DESC
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i03`.
4. Rodar `df_i03 = run_query(sql_i03)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.
6. (Opcional, replicando o `.py`) calcular a abordagem alternativa "meta
   integral" a partir de `meta_json`/`realizado_json` (campos JSON com chaves
   `quantitativo` ou `porcentagem`) — ver `parse_meta_integral()` em
   `IND_03.1_run.py` linhas 147-177 se precisar dessa segunda perspectiva.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_03.2_taxa_cumprimento_entrega_{stamp}.csv"
df_i03.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- Diferença metodológica **I02 vs I03**: I02 = PEs que se sobrepõem ao período;
  I03 = entregas que **vencem** no período (`pee.data_fim BETWEEN`).
- Correção de escala: metas entre 0–1 são normalizadas para 0–100
  (`anomalia_escala = 'S'`).
- Correção de dado inconsistente (19.06.2026): `taxa_atingimento_perc < 0`
  (de `progresso_realizado` negativo) é classificada como `'Dado inconsistente'`,
  não como "Não executada".
- Scores > 100% são legítimos (superexecução) — não são erro.
- Validação A3 (17.05.2026): fórmula confirmada; dupla abordagem (ciclo vs.
  meta integral) aprovada.

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_03.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.2.2-i03.md`
