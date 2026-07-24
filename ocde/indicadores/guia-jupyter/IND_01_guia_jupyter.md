# I01 — Proporção de Servidores por Regime de Trabalho — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_01.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Mede a proporção de servidores por regime de trabalho (presencial/híbrido/remoto),
a partir do campo `modalidade_pgd` do cadastro SIAPE/PGD, vinculado por CPF ao
Plano de Trabalho (PT) vigente no período.

## 2. Pré-requisitos

- IP da máquina liberado pelo Dataprev; driver JDBC instalado (ver CLAUDE.md seção 2).
- Notebook `consultas_denodo.ipynb` (raiz do projeto) aberto no VS Code.
- Célula 2 (conexão) já configurada localmente com usuário/senha do Denodo —
  **não copie credenciais para este arquivo**; ver CLAUDE.md seção 2
  (arquivo local, não versionado). Se a célula 2 ainda não tiver usuário/senha
  preenchidos, edite-a localmente antes de continuar — nunca cole credenciais
  neste `.md`.

## 3. Instrumento e periodicidade

- Instrumento: **Plano de Trabalho (PT)** → `build_periods_pt()`.
- Regra vigente: 2025 trimestral (T3–T4, H1/2025 excluído) | 2026+ mensal (M01–M12).
  Base: 01/07/2025.

**Particularidade do I01:** a query `SQL_I01_PLANOS` **não recebe** `{ini}`/`{fim}`
— ela carrega **todos** os planos de trabalho com vigência a partir de 2025-01-01
em uma única consulta (~14.000 registros), e a segmentação por período +
agregação por modalidade é feita **em Python** (pandas, no notebook), não em SQL.
Isso evita 9 round-trips ao Denodo. A tabela abaixo é usada apenas para filtrar
o DataFrame por sobreposição de datas (`inicio <= periodo_fim AND fim >= periodo_ini`).

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

## 4. Query SQL_I01_PLANOS

```sql
SELECT
    pt.usuario_id,
    COALESCE(un.sigla, 'N.I.') AS unidade_sigla,
    COALESCE(un.nome,  'N.I.') AS unidade_nome,
    CASE
        WHEN NULLIF(TRIM(COALESCE(ins.modalidade_pgd, '')), '') IS NULL THEN 'N.I.'
        ELSE TRIM(ins.modalidade_pgd)
    END                          AS modalidade,
    CAST(pt.data_inicio AS DATE) AS plano_inicio,
    CAST(pt.data_fim    AS DATE) AS plano_fim
FROM petrvs_icmbio_planos_trabalhos pt
JOIN petrvs_icmbio_usuarios u
    ON  u.id = pt.usuario_id
LEFT JOIN (
    SELECT
        cpf,
        MIN(NULLIF(TRIM(COALESCE(modalidade_pgd, '')), '')) AS modalidade_pgd
    FROM petrvs_icmbio_integracao_servidores
    WHERE cpf IS NOT NULL
    GROUP BY cpf
) ins ON ins.cpf = u.cpf
LEFT JOIN petrvs_icmbio_unidades un
    ON  un.id = pt.unidade_id
WHERE pt.deleted_at  IS NULL
  AND pt.usuario_id  IS NOT NULL
  AND pt.data_inicio IS NOT NULL
  AND pt.data_fim    IS NOT NULL
  AND CAST(pt.data_fim AS DATE) >= CAST('2025-01-01' AS DATE)
```

Sem placeholders para trocar — a query roda uma única vez.

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 em uma nova célula, atribuída a `sql_i01`, e rodar:
   ```python
   sql_i01 = """<colar a query da seção 4>"""
   df_i01 = run_query(sql_i01)
   ```
4. Segmentar por período e agregar por modalidade — célula pandas (traduz a lógica
   de `IND_01.1_run.py`, função `main()`, para o notebook):
   ```python
   import pandas as pd

   periodos = [
       ("T3-2025", "trimestral", "2025-07-01", "2025-09-30", "encerrado"),
       ("T4-2025", "trimestral", "2025-10-01", "2025-12-31", "encerrado"),
       ("M01-2026", "mensal", "2026-01-01", "2026-01-31", "encerrado"),
       ("M02-2026", "mensal", "2026-02-01", "2026-02-28", "encerrado"),
       ("M03-2026", "mensal", "2026-03-01", "2026-03-31", "encerrado"),
       ("M04-2026", "mensal", "2026-04-01", "2026-04-30", "encerrado"),
       ("M05-2026", "mensal", "2026-05-01", "2026-05-31", "encerrado"),
       ("M06-2026", "mensal", "2026-06-01", "2026-06-30", "encerrado"),
       ("M07-2026", "mensal", "2026-07-01", "2026-07-31", "em_andamento"),
   ]

   df_i01["plano_inicio"] = pd.to_datetime(df_i01["plano_inicio"])
   df_i01["plano_fim"]    = pd.to_datetime(df_i01["plano_fim"])

   linhas_v1 = []  # visao institucional: periodo x modalidade
   for label, kind, ini, fim, status in periodos:
       ini_dt, fim_dt = pd.Timestamp(ini), pd.Timestamp(fim)
       ativo = df_i01[(df_i01["plano_inicio"] <= fim_dt) & (df_i01["plano_fim"] >= ini_dt)]
       total = ativo["usuario_id"].nunique()
       if total == 0:
           continue
       por_modalidade = ativo.groupby("modalidade")["usuario_id"].nunique()
       for modalidade, n in por_modalidade.sort_values(ascending=False).items():
           linhas_v1.append([kind, label, ini, fim, status, n, round(n * 100.0 / total, 2)])

   df_i01_v1 = pd.DataFrame(
       linhas_v1,
       columns=["ciclo_tipo", "periodo", "periodo_inicio", "periodo_fim",
                "periodo_status", "total_servidores", "proporcao_perc"],
   )
   df_i01_v1
   ```
   Para a visão por unidade (V2), repita o agrupamento incluindo `unidade_sigla`,
   `unidade_nome` antes de `modalidade` — ver `IND_01.1_run.py` linhas 188-202
   para a lógica completa (denominador = total de servidores da unidade no período).

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_01.2_v1_proporcao_mensal_{stamp}.csv"
df_i01_v1.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

Ajuste `2026-07` para o mês corrente. Repita para `df_i01_v2` com o nome
`IND_01.2_v2_proporcao_unidade_mensal_{stamp}.csv`.

## 7. Observações e pontos críticos

- **Nota técnica (23.05.2026):** a view `tipos_modalidades` está inacessível no
  Denodo. O regime de trabalho vem de `integracao_servidores.modalidade_pgd`,
  consolidado por CPF com `MIN()`.
- UUIDs brutos em `modalidade` indicam falha de mapeamento no cadastro SIAPE/PGD
  — não são um regime de trabalho válido.
- Planos com `plano_inicio > plano_fim` ou datas nulas devem ser descartados
  antes da agregação (replicar filtro `skipped` do `.py`).
- Período em andamento (M07-2026 nesta tabela): dados preliminares.
- Pendência do projeto: decidir critério MIN vs. mais recente para servidores
  com múltiplos registros de modalidade (ver CLAUDE.md seção 11).

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_01.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.1.1-i01.md`
