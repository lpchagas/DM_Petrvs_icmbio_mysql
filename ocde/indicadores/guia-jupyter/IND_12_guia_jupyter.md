# I12 — Coerência entre Avaliação do PT e do PE — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_12.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Compara a média das avaliações individuais do Plano de Trabalho (PT) com a
média das avaliações coletivas do Plano de Entregas (PE) por unidade, medindo
a coerência entre os dois níveis de avaliação.

## 2. Pré-requisitos

- IP da máquina liberado pelo Dataprev; driver JDBC instalado (ver CLAUDE.md seção 2).
- Notebook `consultas_denodo.ipynb` (raiz do projeto) aberto no VS Code.
- Célula 2 (conexão) já configurada localmente com usuário/senha do Denodo —
  **não copie credenciais para este arquivo**; ver CLAUDE.md seção 2
  (arquivo local, não versionado).

## 3. Instrumento e periodicidade

- Instrumento: **misto PT + PE**, ciclo alinhado ao Plano de Entregas (PE) →
  `build_periods_pe()`.
- Regra vigente: 2025 trimestral (T3–T4, H1/2025 excluído) | 2026+ quadrimestral (Q1–Q3).
  Base: 01/07/2025.

Períodos vigentes em 24.07.2026 (recalcular com `build_periods_pe()` se datas futuras):

| Período | Tipo | Início | Fim | Status |
|---|---|---|---|---|
| T3-2025 | trimestral | 2025-07-01 | 2025-09-30 | encerrado |
| T4-2025 | trimestral | 2025-10-01 | 2025-12-31 | encerrado |
| Q1-2026 | quadrimestral | 2026-01-01 | 2026-04-30 | encerrado |
| Q2-2026 | quadrimestral | 2026-05-01 | 2026-08-31 | em_andamento |

## 4. Query SQL_I12

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
        pt.unidade_id,
        (6 - tan.sequencia) AS valor_nota
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
avaliacoes_pe AS (
    SELECT
        pe.unidade_id,
        (6 - tan.sequencia) AS valor_nota
    FROM petrvs_icmbio_avaliacoes av
    JOIN petrvs_icmbio_planos_entregas pe
        ON pe.id = av.plano_entrega_id
    JOIN petrvs_icmbio_tipos_avaliacoes_notas tan
        ON tan.id = av.tipo_avaliacao_nota_id
    CROSS JOIN parametros p
    WHERE av.plano_entrega_id IS NOT NULL
      AND (p.incluir_excluidos = 1 OR av.deleted_at IS NULL)
      AND CAST(pe.data_inicio AS DATE) <= p.data_fim
      AND CAST(pe.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pe.deleted_at IS NULL)
),
media_pt_por_unidade AS (
    SELECT
        unidade_id,
        COUNT(*)                           AS total_avaliacoes_pt,
        ROUND(AVG(valor_nota * 1.0), 2)    AS media_nota_pt
    FROM avaliacoes_pt
    GROUP BY unidade_id
),
media_pe_por_unidade AS (
    SELECT
        unidade_id,
        COUNT(*)                           AS total_avaliacoes_pe,
        ROUND(AVG(valor_nota * 1.0), 2)    AS media_nota_pe
    FROM avaliacoes_pe
    GROUP BY unidade_id
),
coerencia AS (
    SELECT
        COALESCE(un.sigla, 'N.I.')                                     AS unidade_sigla,
        COALESCE(un.nome,  'N.I.')                                     AS unidade_nome,
        mpt.total_avaliacoes_pt,
        mpt.media_nota_pt,
        mpe.total_avaliacoes_pe,
        mpe.media_nota_pe,
        ROUND(ABS(mpt.media_nota_pt - mpe.media_nota_pe), 2)           AS diferenca_absoluta,
        ROUND(mpt.media_nota_pt - mpe.media_nota_pe, 2)                AS diferenca_direcional
    FROM media_pt_por_unidade mpt
    JOIN media_pe_por_unidade mpe ON mpe.unidade_id = mpt.unidade_id
    LEFT JOIN petrvs_icmbio_unidades un ON un.id = mpt.unidade_id
)
SELECT
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    media_nota_pt,
    total_avaliacoes_pe,
    media_nota_pe,
    diferenca_absoluta,
    diferenca_direcional,
    CASE
        WHEN diferenca_absoluta <= 1.0 THEN 'Coerente'
        WHEN diferenca_absoluta <= 2.0 THEN 'Divergencia moderada'
        ELSE 'Alta divergencia'
    END AS classificacao_coerencia,
    CASE
        WHEN diferenca_direcional > 0 THEN 'PT > PE'
        WHEN diferenca_direcional < 0 THEN 'PE > PT'
        ELSE 'Sem diferenca'
    END AS direcao_divergencia
FROM coerencia
ORDER BY diferenca_absoluta DESC, unidade_sigla
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i12`.
4. Rodar `df_i12 = run_query(sql_i12)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_12.2_coerencia_pt_pe_{stamp}.csv"
df_i12.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- **Correção de escala obrigatória (19.06.2026):** usar `(6 - tan.sequencia)`
  em ambos os blocos (PT e PE) — `JSON_UNQUOTE(tan.nota)` retorna `NULL` no
  Denodo VQL e classificava todas as unidades como "Alta divergência".
- Correção de sinal (12.06.2026): `diferenca_direcional = media_nota_pt -
  media_nota_pe` é positivo quando PT > PE (confirmado em validação COCAGE).
- O `JOIN` interno entre `media_pt_por_unidade` e `media_pe_por_unidade`
  **exclui** unidades sem as duas perspectivas (ex.: 77 unidades com ciclo
  incompleto em T1/T2-2025) — não aparecem no resultado.
- Achados de referência (12.06.2026): 96–100% "Coerente" por período;
  diferença média 0,24–0,34 pts; padrão PE > PT (38%) > PT > PE (27%) —
  avaliador coletivo tende a dar nota levemente superior (oposto de leniência).
- Pendência: COCAGE confirmar a interpretação do padrão PE > PT (ver
  CLAUDE.md seção 11).

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_12.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.4.4-i12.md`
