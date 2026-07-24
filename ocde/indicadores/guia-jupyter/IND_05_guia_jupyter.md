# I05 — Distribuição das Entregas entre os Servidores — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_05.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Calcula quantas entregas do PE cada servidor carrega no Plano de Trabalho (PT)
e compara com a média dos demais servidores da mesma unidade — mede se a carga
está distribuída de forma equitativa ou concentrada em poucos.

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
- A unidade é derivada de `pt.unidade_id` (unidade do servidor), não do
  planejador — o I05 mede distribuição entre executores.

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

## 4. Query SQL_I05

Exemplo com o primeiro período (T3-2025) preenchido — troque as datas de
`parametros` a cada rodada.

```sql
WITH parametros AS (
    SELECT
        CAST('2025-07-01' AS DATE) AS data_inicio,
        CAST('2025-09-30' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
vinculos_entregas AS (
    SELECT DISTINCT
        COALESCE(un.sigla, 'N.I.') AS unidade_sigla,
        COALESCE(un.nome,  'N.I.') AS unidade_nome,
        pt.usuario_id              AS id_servidor,
        COALESCE(us.nome,  'N.I.') AS nome_servidor,
        pte.plano_entrega_entrega_id AS id_entrega
    FROM petrvs_icmbio_planos_trabalhos pt
    JOIN petrvs_icmbio_planos_trabalhos_entregas pte
        ON pte.plano_trabalho_id = pt.id
    LEFT JOIN petrvs_icmbio_unidades un
        ON un.id = pt.unidade_id
    LEFT JOIN petrvs_icmbio_usuarios us
        ON us.id = pt.usuario_id
    CROSS JOIN parametros p
    WHERE CAST(pt.data_inicio AS DATE) <= p.data_fim
      AND CAST(pt.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pt.deleted_at  IS NULL)
      AND (p.incluir_excluidos = 1 OR pte.deleted_at IS NULL)
      AND pt.usuario_id IS NOT NULL
      AND pte.plano_entrega_entrega_id IS NOT NULL
),
entregas_por_servidor AS (
    SELECT
        unidade_sigla,
        MIN(unidade_nome)              AS unidade_nome,
        id_servidor,
        MIN(nome_servidor)             AS nome_servidor,
        COUNT(DISTINCT id_entrega)     AS qtd_entregas_por_servidor
    FROM vinculos_entregas
    GROUP BY unidade_sigla, id_servidor
),
media_por_unidade AS (
    SELECT
        unidade_sigla,
        ROUND(AVG(qtd_entregas_por_servidor) * 1.0, 2)
            AS media_entregas_por_servidor_unidade
    FROM entregas_por_servidor
    GROUP BY unidade_sigla
)
SELECT
    e.unidade_sigla,
    e.unidade_nome,
    e.id_servidor,
    e.nome_servidor,
    e.qtd_entregas_por_servidor,
    m.media_entregas_por_servidor_unidade,
    CASE
        WHEN e.qtd_entregas_por_servidor > m.media_entregas_por_servidor_unidade THEN 'Acima da media'
        WHEN e.qtd_entregas_por_servidor < m.media_entregas_por_servidor_unidade THEN 'Abaixo da media'
        ELSE 'Na media'
    END AS posicao_relativa_media
FROM entregas_por_servidor e
JOIN media_por_unidade m ON m.unidade_sigla = e.unidade_sigla
ORDER BY e.unidade_sigla, e.qtd_entregas_por_servidor DESC, e.nome_servidor
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i05`.
4. Rodar `df_i05 = run_query(sql_i05)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_05.2_distribuicao_entregas_servidores_{stamp}.csv"
df_i05.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- Correção (24.05.2026): filtro `pte.deleted_at IS NULL` é obrigatório — sem
  ele, registros logicamente excluídos inflavam a contagem de entregas por
  servidor.
- Servidores com `qtd_entregas_por_servidor = 0` (PT ativo sem vínculos) são
  um aviso de qualidade — verificar preenchimento do PT.
- Pendência do projeto: executar A4 para confirmar numericamente a
  segmentação H1/H2 (ver CLAUDE.md seção 11).

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_05.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.3.1-i05.md`
