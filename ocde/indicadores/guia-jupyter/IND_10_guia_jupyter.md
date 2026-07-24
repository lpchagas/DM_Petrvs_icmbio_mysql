# I10 — Percentual de Avaliações Inadequadas por Unidade — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_10.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Calcula o percentual de avaliações do PT classificadas como "Inadequado"
(`tan.sequencia = 4`) por unidade — sinaliza baixa prevalência ou atenção
crítica de desempenho.

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

## 4. Query SQL_I10

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
        av.id          AS id_avaliacao,
        pt.unidade_id,
        tan.sequencia  AS sequencia_nota
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
proporcao_por_unidade AS (
    SELECT
        COALESCE(un.sigla, 'N.I.')                                   AS unidade_sigla,
        COALESCE(un.nome,  'N.I.')                                   AS unidade_nome,
        COUNT(avpt.id_avaliacao)                                     AS total_avaliacoes_pt,
        SUM(CASE WHEN avpt.sequencia_nota = 4 THEN 1 ELSE 0 END)    AS qtd_inadequado,
        ROUND(
            SUM(CASE WHEN avpt.sequencia_nota = 4 THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(avpt.id_avaliacao), 0),
            2
        )                                                            AS perc_inadequado
    FROM avaliacoes_pt avpt
    LEFT JOIN petrvs_icmbio_unidades un ON un.id = avpt.unidade_id
    GROUP BY COALESCE(un.sigla, 'N.I.'), COALESCE(un.nome, 'N.I.')
)
SELECT
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    qtd_inadequado,
    perc_inadequado,
    CASE
        WHEN perc_inadequado >= 30 THEN 'Atencao critica'
        WHEN perc_inadequado >= 15 THEN 'Atencao moderada'
        WHEN perc_inadequado >=  5 THEN 'Observacao'
        ELSE 'Baixa prevalencia'
    END AS nivel_alerta
FROM proporcao_por_unidade
ORDER BY perc_inadequado DESC, unidade_sigla
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i10`.
4. Rodar `df_i10 = run_query(sql_i10)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_10.2_perc_inadequado_pt_{stamp}.csv"
df_i10.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- **Correção de escala obrigatória (12.06.2026):** "Inadequado" é
  `tan.sequencia = 4`, não `sequencia = 2` (que é "Alto desempenho"). O bug
  original classificava 82–86% das unidades em "Atenção crítica" — incorreto.
  **Não usar `tan.nota` ou `JSON_UNQUOTE(tan.nota)`.**
- Resultado após correção: 98,9% das unidades em "Baixa prevalência".
- Alerta recorrente confirmado: PARNAEMAS (T1–T3/2025).
- Unidades com < 5 avaliações em períodos encerrados têm percentuais
  estatisticamente frágeis.

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_10.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.4.2-i10.md`
