# I09 — Média da Avaliação do Plano de Trabalho por Unidade — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_09.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Calcula a média das notas de avaliação do Plano de Trabalho (PT) por unidade,
usando a escala corrigida `(6 - tan.sequencia)`.

## 2. Pré-requisitos

- IP da máquina liberado pelo Dataprev; driver JDBC instalado (ver CLAUDE.md seção 2).
- Notebook `consultas_denodo.ipynb` (raiz do projeto) aberto no VS Code.
- Célula 2 (conexão) já configurada localmente com usuário/senha do Denodo —
  **não copie credenciais para este arquivo**; ver CLAUDE.md seção 2
  (arquivo local, não versionado).

## 3. Instrumento e periodicidade

- Instrumento: **Plano de Trabalho (PT)** → `build_periods_pt()`.
- Regra vigente: 2025 trimestral (T3–T4, H1/2025 excluído) | 2026+ mensal (M01–M12).
  Base: 01/07/2025.

Períodos vigentes em 24.07.2026 (recalcular com `build_periods_pt()` se datas futuras):

| Período | Tipo | Início | Fim | Status |
|---|---|---|---|---|
| T3-2025 | trimestral | 2025-07-01 | 2025-09-30 | encerrado |
| T4-2025 | trimestral | 2025-10-01 | 2025-12-31 | encerrado |
| M01-2026 | mensal | 2026-01-01 | 2026-01-31 | encerrado |
| M02-2026 | mensal | 2026-02-01 | 2026-02-28 | encerrado |
| M03-2026 | mensal | 2026-03-01 | 2026-03-31 | encerrado |
| M04-2026 | mensal | 2026-04-01 | 2026-04-30 | encerrado |
| M05-2026 | mensal | 2026-05-01 | 2026-05-31 | encerrado |
| M06-2026 | mensal | 2026-06-01 | 2026-06-30 | encerrado |
| M07-2026 | mensal | 2026-07-01 | 2026-07-31 | em_andamento |

## 4. Query SQL_I09

Exemplo com o primeiro período (T3-2025) preenchido — troque as datas de
`parametros` a cada rodada.

```sql
WITH parametros AS (
    SELECT
        CAST('2025-07-01' AS DATE) AS data_inicio,
        CAST('2025-09-30' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
avaliacoes_pt AS (
    SELECT
        av.id                    AS id_avaliacao,
        pt.unidade_id,
        ptc.plano_trabalho_id,
        (6 - tan.sequencia)      AS valor_nota
    FROM petrvs_icmbio_avaliacoes av
    JOIN petrvs_icmbio_planos_trabalhos_consolidacoes ptc
        ON ptc.id = av.plano_trabalho_consolidacao_id
    JOIN petrvs_icmbio_planos_trabalhos pt
        ON pt.id = ptc.plano_trabalho_id
    JOIN petrvs_icmbio_tipos_avaliacoes_notas tan
        ON tan.id = av.tipo_avaliacao_nota_id
    CROSS JOIN parametros p
    WHERE av.plano_trabalho_consolidacao_id IS NOT NULL
      AND (p.incluir_excluidos = 1 OR av.deleted_at IS NULL)
      AND CAST(pt.data_inicio AS DATE) <= p.data_fim
      AND CAST(pt.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pt.deleted_at IS NULL)
),
media_por_unidade AS (
    SELECT
        COALESCE(un.sigla, 'N.I.')                               AS unidade_sigla,
        COALESCE(un.nome,  'N.I.')                               AS unidade_nome,
        COUNT(avpt.id_avaliacao)                                 AS total_avaliacoes_pt,
        COUNT(DISTINCT avpt.plano_trabalho_id)                   AS total_planos_com_avaliacao,
        ROUND(AVG(avpt.valor_nota * 1.0), 2)                     AS media_nota_pt,
        MIN(avpt.valor_nota)                                     AS nota_minima,
        MAX(avpt.valor_nota)                                     AS nota_maxima,
        SUM(CASE WHEN avpt.valor_nota = 1 THEN 1 ELSE 0 END)    AS qtd_nota_1,
        SUM(CASE WHEN avpt.valor_nota = 2 THEN 1 ELSE 0 END)    AS qtd_nota_2,
        SUM(CASE WHEN avpt.valor_nota = 3 THEN 1 ELSE 0 END)    AS qtd_nota_3,
        SUM(CASE WHEN avpt.valor_nota = 4 THEN 1 ELSE 0 END)    AS qtd_nota_4,
        SUM(CASE WHEN avpt.valor_nota = 5 THEN 1 ELSE 0 END)    AS qtd_nota_5
    FROM avaliacoes_pt avpt
    LEFT JOIN petrvs_icmbio_unidades un ON un.id = avpt.unidade_id
    GROUP BY COALESCE(un.sigla, 'N.I.'), COALESCE(un.nome, 'N.I.')
)
SELECT
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    total_planos_com_avaliacao,
    media_nota_pt,
    nota_minima,
    nota_maxima,
    qtd_nota_1,
    qtd_nota_2,
    qtd_nota_3,
    qtd_nota_4,
    qtd_nota_5,
    CASE
        WHEN media_nota_pt >= 4.5 THEN 'Excepcional'
        WHEN media_nota_pt >= 3.5 THEN 'Alto desempenho'
        WHEN media_nota_pt >= 2.5 THEN 'Adequado'
        WHEN media_nota_pt >= 1.5 THEN 'Inadequado'
        ELSE 'Nao executado'
    END AS faixa_desempenho
FROM media_por_unidade
ORDER BY media_nota_pt DESC, unidade_sigla
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i09`.
4. Rodar `df_i09 = run_query(sql_i09)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_09.2_media_avaliacao_pt_{stamp}.csv"
df_i09.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- **Correção de escala obrigatória (19.06.2026):** `JSON_UNQUOTE(tan.nota)`
  não funciona no Denodo VQL via JDBC (retorna `NULL`). Usar sempre
  `(6 - tan.sequencia)`:
  `sequencia=1→Excepcional(5)`, `2→Alto desempenho(4)`, `3→Adequado(3)`,
  `4→Inadequado(2)`, `5→Não executado(1)`. **Nunca usar `tan.nota` ou `JSON_UNQUOTE`.**
- `total_planos_com_avaliacao` (`COUNT DISTINCT plano_trabalho_id`) é a
  referência correta para comparar com o PETRVS — `total_avaliacoes_pt` conta
  eventos (múltiplas consolidações mensais inflam a contagem, ratio ~2,78×).
- Unidades com < 5 avaliações em períodos encerrados têm resultado
  estatisticamente frágil.
- Média nacional de referência (jun/2026): ~4,0 ("Alto desempenho").
- Pendência: CGOV decidir abordagem eventos vs. planos vs. última
  consolidação (ver CLAUDE.md seção 11).

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_09.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.4.1-i09.md`
