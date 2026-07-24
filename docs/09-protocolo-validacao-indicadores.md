# Protocolo de Validação dos Indicadores OCDE/PGD

## 1. Objetivo e escopo

Este documento formaliza o ciclo completo de trabalho para cada indicador do projeto — da geração automatizada da tabela de resultados até a atualização da documentação após aprovação técnica. Serve como referência para analistas e como guia operacional em novos ciclos de cálculo.

O protocolo foi elaborado a partir da experiência acumulada nas validações de I02 (11/05/2026), I03 (17/05/2026), I04–I06 e I09–I12 (mai–jun/2026), e cobre todas as etapas esperadas para os 12 indicadores.

**Escopo:** 12 indicadores em 4 eixos. Ver [docs/06-indicadores-ocde-mysql.md](06-indicadores-ocde-mysql.md).

**Fonte de dados:** Denodo (`denodo-pgd.dataprev.gov.br:443`, banco `petrvs_icmbio`) — virtualização em tempo real. Dados sempre atualizados; defasagem temporal do dump MySQL não se aplica a partir de maio/2026.

**Pré-requisito de acesso:** IP da máquina liberado pelo Dataprev. Credenciais de conexão configuradas no arquivo local `.env` (nunca versionado). Ver [docs/03-acesso-direto-denodo-dbeaver.md](03-acesso-direto-denodo-dbeaver.md).

---

## 2. Artefatos por ciclo de validação

Cada ciclo produz até cinco artefatos. O padrão de nomenclatura é `IND_XX.N_<descricao>_<sufixo>.<ext>`, onde `XX` é o número do indicador com dois dígitos (01–12) e `N` identifica o tipo do artefato (1–5).

| # | Artefato | Nomenclatura padrão | Pasta |
|---|---|---|---|
| A1 | Script de geração (sanitizado) | `IND_XX.1_run.py` | `ocde/indicadores/` |
| A2 | Tabela de resultado (CSV) | `IND_XX.2_<nome>_AAAAMMDD_HHMM.csv` | `artefatos_local/ocde/entregas/YYYY-MM/` |
| A3 | Consulta manual PETRVS (PDF) | `IND_XX.3_PETRVS_consulta_DD.MM.AAAA.pdf` | `artefatos_local/validacao/` |
| A4 | Script diagnóstico | `IND_XX.4_diagnostico_DD.MM.AAAA.py` | `artefatos_local/ocde/diagnosticos/` |
| A5 | Relatório de validação | `IND_XX.5_relatorio_validacao_DD.MM.AAAA.md` | `artefatos_local/validacao/` |

**Notas:**

- **A1 — script canônico:** armazenado em `ocde/indicadores/` (público, sem credenciais — lê conexão do `.env`). Cópias de backup local em `artefatos_local/backup_scripts_a1/`.
- **A2 — múltiplas versões:** quando o indicador produz mais de uma tabela (ex: visão resumida + detalhada), usar prefixo `v1_`, `v2_` antes da descrição: `IND_XX.2_v1_<nome>_AAAAMMDD_HHMM.csv`.
- **A4 — CSVs intermediários:** gerados pelo script A4 e salvos em `artefatos_local/ocde/diagnosticos/YYYY-MM/` com padrão `IND_XX.4_qN_<descricao>.csv`.
- **Todos os artefatos em `artefatos_local/` são mantidos apenas localmente** — a pasta está no `.gitignore`. Contêm dados operacionais do ICMBio e registros internos da CGOV.

---

## 3. Fluxo de trabalho — 4 fases

```
Fase 1              Fase 2               Fase 3                     Fase 4
Geração        →   Validação manual  →   Diagnóstico técnico   →   Correção e
(IND_XX.1_run)     (equipe CGOV no       (IND_XX.4_diagnostico +    documentação
                    sistema PETRVS)       IND_XX.5_relatorio)        atualizada
```

### Fase 1 — Geração da tabela de resultados

**Responsável:** analista técnico

1. Ler o documento do indicador em `docs/06.X.X-iXX.md` e identificar a query SQL canônica (`SQL_IXX`).
2. Criar `IND_XX.1_run.py` em `ocde/indicadores/` seguindo o modelo canônico (ver Seção 4.1 e `ocde/indicadores/IND_02.1_run.py`).
3. Executar o script. Verificar:
   - Número de linhas plausível (não zero, não absurdamente alto)
   - Nenhuma coluna retornou apenas nulos
   - Valores extremos (taxas > 500%, zeros em massa) foram identificados
   - As 6 colunas de metadado de período estão presentes e corretas
4. O script salva automaticamente `IND_XX.2_<nome>_AAAAMMDD_HHMM.csv` em `artefatos_local/ocde/entregas/YYYY-MM/`.
5. Encaminhar o CSV à equipe CGOV com o período de referência e sugestão de unidades para amostragem.

**Critério de conclusão:** CSV gerado, verificado e entregue. Número de linhas registrado no CLAUDE.md (Seção 11).

---

### Fase 2 — Validação manual no sistema PETRVS

**Responsável:** equipe CGOV

1. Selecionar 3–5 unidades para amostragem — cobrir perfis variados: grande/pequena, plano avaliado/ativo.
2. Para cada unidade: acessar o sistema PETRVS online e consultar o indicador no mesmo período.
3. Registrar a consulta em `artefatos_local/validacao/IND_XX.3_PETRVS_consulta_DD.MM.AAAA.pdf`:
   - Data da consulta
   - Unidades verificadas
   - Valores observados no sistema (totais, percentuais, nomes de entregas quando pertinente)
   - Hipóteses sobre divergências encontradas
4. Devolver ao analista técnico com as hipóteses formuladas.

**Critério de conclusão:** A3 salvo em `artefatos_local/validacao/` e hipóteses definidas.

---

### Fase 3 — Diagnóstico técnico e relatório

**Responsável:** analista técnico

1. Ler o A3 (consulta manual) e identificar cada hipótese formulada pela equipe.
2. Para cada hipótese, criar uma query diagnóstica em `IND_XX.4_diagnostico_DD.MM.AAAA.py` (ver template Seção 4.2) que a responda com evidência direta do Denodo. Salvar o script em `artefatos_local/ocde/diagnosticos/`.
3. Executar todas as queries e salvar os CSVs diagnósticos em `artefatos_local/ocde/diagnosticos/YYYY-MM/` como `IND_XX.4_qN_<descricao>.csv`.
4. **Classificar cada hipótese** em uma das categorias:

| Categoria | Descrição | Ação |
|---|---|---|
| Bug na query | Cálculo matematicamente incorreto | Corrigir na Fase 4 |
| Divergência semântica | Critério OCDE ≠ fluxo formal do PETRVS | Documentar sem alterar query; informar CGOV |
| Decisão metodológica | A fórmula é ambígua; há duas interpretações válidas | Apresentar opções ao CGOV; aguardar decisão |
| Anomalia de dados | Valores impossíveis ou inconsistentes no banco | Documentar e recomendar filtro ou flag |
| Sem divergência | Resultados idênticos | Registrar como validado |

5. Elaborar `IND_XX.5_relatorio_validacao_DD.MM.AAAA.md` seguindo a estrutura da Seção 5. Salvar em `artefatos_local/validacao/`.

**Critério de conclusão:** hipóteses respondidas com evidências; relatório salvo; aprovação ou decisão da equipe obtida.

---

### Fase 4 — Correções e atualização da documentação

**Responsável:** analista técnico

1. **Se bug:** corrigir a query em `docs/06.X.X-iXX.md` e em `Consultas SQL/*.sql`. Atualizar `ocde/indicadores/IND_XX.1_run.py`. Re-executar e regenerar o CSV A2.
2. **Se decisão metodológica:** implementar a abordagem acordada. Atualizar o script A1 com novas colunas. Regenerar o CSV A2.
3. **Sempre:** atualizar `docs/06.X.X-iXX.md` com:
   - Novas colunas no resultado
   - Achados do diagnóstico (anomalias de dados, campos JSON, decisões metodológicas)
   - Referência ao relatório de validação A5
4. Atualizar a tabela de status do indicador no `CLAUDE.md` (Seção 11).

**Critério de conclusão:** CSV final gerado; documentação atualizada; status marcado como ✅ no CLAUDE.md.

---

## 4. Templates de scripts

### 4.1 Estrutura obrigatória do script de geração (A1)

O script de geração segue a estrutura padronizada definida em `CLAUDE.md` Seção 14. O modelo canônico público é `ocde/indicadores/IND_02.1_run.py`.

**Elementos obrigatórios:**

```python
"""IND_XX.1_run.py
[Docstring descrevendo o indicador, a abordagem temporal e decisões metodológicas]
"""
import csv, os, re, sys
from datetime import date, datetime
import jpype, jpype.imports

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Configuração de conexão lida do arquivo .env (nunca versionado)
# — ver lib/denodo_config.py para implementação completa
from scripts.lib.denodo_config import get_connection_params
JAR, JVM_DLL, JDBC_URL, USER, PASS = get_connection_params()

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Query parametrizada por período (SQL_IXX — nome obrigatório para docs_sql.py)
SQL_IXX = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
[... CTEs do indicador ...]
SELECT [colunas]
FROM petrvs_icmbio_<tabela_principal> t  -- prefixo obrigatório
JOIN petrvs_icmbio_unidades u ON u.id = t.unidade_id
CROSS JOIN parametros p
WHERE t.deleted_at IS NULL
  AND [... filtros temporais ...]
"""

def build_periods_pe():
    """Ciclo PE: 2025 trimestral | 2026+ quadrimestral.
    Usar para: I02, I03, I04, I07, I08, I12.
    """
    # Ver implementação completa em ocde/indicadores/IND_02.1_run.py

def build_periods_pt():
    """Ciclo PT: 2025 trimestral | 2026+ mensal.
    Usar para: I01, I05, I06, I09, I10, I11.
    """
    # Ver implementação completa em ocde/indicadores/IND_05.1_run.py

def clean(val):
    """Remove quebras de linha internas que corrompem células CSV."""
    if val is None:
        return ""
    return re.sub(r"[\r\n]+", " / ", str(val)).strip()
```

**Regras obrigatórias (ver `CLAUDE.md` Seção 10):**

| Regra | Detalhe |
|---|---|
| `clean()` em todos os campos | Evita quebras de linha internas que corrompem o CSV |
| Delimitador `\|` (pipe) | Evita conflito com `;` presente em descrições do PETRVS |
| Encoding `utf-8-sig` | Compatível com Excel no Windows (BOM necessário) |
| Timestamp no nome do A2 | `datetime.now().strftime("%Y%m%d_%H%M")` — rastreabilidade da extração |
| 6 colunas de metadado de período | `ciclo_tipo`, `periodo`, `periodo_inicio`, `periodo_fim`, `periodo_status`, `duracao_dias` |
| Soft-delete em todas as tabelas | `deleted_at IS NULL` em cada JOIN/FROM |
| Prefixo obrigatório | `petrvs_icmbio_` em todos os nomes de tabela (DBeaver e JDBC) |

---

### 4.2 Template do script de diagnóstico (A4)

```python
"""IND_XX.4_diagnostico_DD.MM.AAAA.py — Diagnóstico do Indicador IXX

Queries Q1–QN contra Denodo em tempo real.
Responde às hipóteses da equipe CGOV (A3 de DD.MM.AAAA).

Hipóteses investigadas:
  H1: [primeira hipótese derivada do A3]
  H2: [segunda hipótese]
  ...

Script salvo em: artefatos_local/ocde/diagnosticos/
CSVs diagnósticos em: artefatos_local/ocde/diagnosticos/YYYY-MM/
"""
import csv, os, re, sys
from datetime import datetime
import jpype, jpype.imports

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scripts.lib.denodo_config import get_connection_params
JAR, JVM_DLL, JDBC_URL, USER, PASS = get_connection_params()

OUT_DIR   = r"artefatos_local\ocde\diagnosticos\YYYY-MM"
DIAG_DATE = datetime.now().strftime("%d.%m.%Y")


def clean(v):
    if v is None:
        return ""
    return re.sub(r"[\r\n]+", " / ", str(v)).strip()


def run_and_save(conn, sql, qnum, descricao):
    print(f"\n>>> {qnum} — {descricao}")
    stmt = conn.createStatement()
    rs   = stmt.executeQuery(sql)
    meta = rs.getMetaData()
    n    = meta.getColumnCount()
    cols = [str(meta.getColumnLabel(i + 1)) for i in range(n)]
    rows = []
    while rs.next():
        rows.append([clean(rs.getObject(i + 1)) for i in range(n)])
    rs.close(); stmt.close()
    print(f"    {len(rows)} linha(s)")
    fname = os.path.join(OUT_DIR, f"IND_XX.4_{qnum}_{descricao}.csv")
    with open(fname, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f, delimiter="|").writerows([cols] + rows)
    print(f"    Salvo: {os.path.basename(fname)}")
    return cols, rows


# Q1 — <descrição da hipótese 1>
SQL_Q1 = """
SELECT ...
FROM petrvs_icmbio_<tabela> t
WHERE t.deleted_at IS NULL
  AND ...
"""

# ... demais queries ...


def main():
    if not jpype.isJVMStarted():
        jpype.startJVM(JVM_DLL, classpath=[JAR])
    DM = jpype.JClass("java.sql.DriverManager")
    P  = jpype.JClass("java.util.Properties")()
    P.setProperty("user", USER)
    P.setProperty("password", PASS)
    conn = DM.getConnection(JDBC_URL, P)
    print("Conexão Denodo OK.\n")

    run_and_save(conn, SQL_Q1, "q1", "descricao_hipotese1")
    # run_and_save(conn, SQL_Q2, "q2", "descricao_hipotese2")

    conn.close()
    print("\n=== Diagnóstico concluído. ===")


if __name__ == "__main__":
    main()
```

---

## 5. Estrutura padrão do relatório de validação (A5)

O arquivo `IND_XX.5_relatorio_validacao_DD.MM.AAAA.md` deve seguir esta estrutura:

```markdown
# Relatório de Validação — IXX: [nome do indicador]
**Data:** DD.MM.AAAA
**Equipe:** CGOV/ICMBio
**Protocolo:** docs/09-protocolo-validacao-indicadores.md

## 1. Objetivo
[Uma frase: o que este relatório valida, para qual período e com qual fonte de dados]

## 2. Hipótese da equipe de validação (A3)
[Transcrição ou resumo fiel das observações enviadas pela equipe CGOV]

## 3. Evidências
### 3.1 [Título da evidência 1 — hipótese H1]
[Resultado da query diagnóstica + interpretação com números concretos]

### 3.2 [Título da evidência 2 — hipótese H2]
[...]

## 4. Síntese dos achados
| Achado | Fonte | Conclusão |
|---|---|---|
| [achado 1] | QD-01 | [conclusão] |
| [achado 2] | QD-02 | [conclusão] |

## 5. Posição técnica sobre a fórmula
[Confirma, ajusta ou rejeita a fórmula atual — com justificativa. Se houver alternativa
(ex: critério OCDE vs. critério formal), descrever as duas abordagens e recomendar.]

## 6. Ações recomendadas
| # | Ação | Prioridade |
|---|---|---|
| 1 | [ação 1] | Alta |
| 2 | [ação 2] | Média |

## 7. Status de aprovação técnica
- [ ] Aprovado sem ressalvas
- [ ] Aprovação condicional — pendência: [descrever]
- [ ] Reprovado — bug identificado: [descrever]
- [ ] Reprovado — decisão metodológica pendente: [descrever]

## 8. Arquivos gerados
| Artefato | Arquivo | Local |
|---|---|---|
| A1 | IND_XX.1_run.py | ocde/indicadores/ |
| A2 | IND_XX.2_<nome>_AAAAMMDD_HHMM.csv | artefatos_local/ocde/entregas/YYYY-MM/ |
| A3 | IND_XX.3_PETRVS_consulta_DD.MM.AAAA.pdf | artefatos_local/validacao/ |
| A4 | IND_XX.4_diagnostico_DD.MM.AAAA.py | artefatos_local/ocde/diagnosticos/ |
| A4 CSVs | IND_XX.4_qN_<descricao>.csv | artefatos_local/ocde/diagnosticos/YYYY-MM/ |
| A5 | IND_XX.5_relatorio_validacao_DD.MM.AAAA.md | artefatos_local/validacao/ |
```

**Classificação do status de aprovação:**

| Status | Significado prático |
|---|---|
| **Aprovado** | Query correta, sem divergências substantivas — pode ser usada em produção |
| **Aprovação condicional** | Query correta para a definição atual; existe pendência metodológica ou de dados que a CGOV deve decidir |
| **Reprovado — bug** | Erro de cálculo identificado; requer correção antes de qualquer uso |
| **Reprovado — decisão** | Ambiguidade metodológica sem resolução; aguardando definição da CGOV |

---

## 6. Queries diagnósticas padrão (Denodo VQL)

Substituir `'<SIGLA1>'`, `'<SIGLA2>'` pelas siglas das unidades amostradas pela equipe CGOV.

**Regras Denodo VQL obrigatórias:**
- Datas: `CAST('2025-01-01' AS DATE)` — nunca `DATE()`, `YEAR()`, `MONTH()`
- Prefixo: `petrvs_icmbio_` obrigatório em todos os nomes de tabela
- CTEs recursivas: não funcionam no Denodo VQL — usar aritmética de datas
- Diferença de datas: `(CAST(data1 AS DATE) - CAST(data2 AS DATE))` em dias

---

### QD-01 — Volumetria geral por unidade

Primeira verificação após receber as hipóteses da equipe: confirmar que os totais do CSV batem com a query ao vivo.

```sql
SELECT
    u.sigla,
    COUNT(DISTINCT pee.id)  AS total_planejadas,
    SUM(CASE WHEN COALESCE(pee.progresso_realizado, 0) >= pee.progresso_esperado
              AND pee.progresso_esperado > 0
             THEN 1 ELSE 0 END) AS total_concluidas_ocde
FROM petrvs_icmbio_planos_entregas_entregas pee
JOIN petrvs_icmbio_planos_entregas pe ON pe.id = pee.plano_entrega_id
JOIN petrvs_icmbio_unidades u          ON u.id = pe.unidade_id
WHERE pee.deleted_at IS NULL
  AND pe.deleted_at  IS NULL
  AND CAST(pe.data_inicio AS DATE) >= CAST('2025-01-01' AS DATE)
  AND CAST(pe.data_fim    AS DATE) <= CAST('2025-12-31' AS DATE)
  AND u.sigla IN ('<SIGLA1>', '<SIGLA2>')
GROUP BY u.sigla
ORDER BY u.sigla;
```

---

### QD-02 — Breakdown por unidade × status do ciclo

Essencial para distinguir divergência de critério (OCDE vs. fluxo formal do PETRVS) de divergência por bug.

```sql
SELECT
    u.sigla,
    pe.status                    AS status_pe,
    CAST(pe.data_inicio AS DATE) AS pe_inicio,
    CAST(pe.data_fim    AS DATE) AS pe_fim,
    COUNT(DISTINCT pee.id)       AS total_planejadas,
    SUM(CASE WHEN COALESCE(pee.progresso_realizado, 0) >= pee.progresso_esperado
              AND pee.progresso_esperado > 0
             THEN 1 ELSE 0 END) AS concluidas_ocde
FROM petrvs_icmbio_planos_entregas_entregas pee
JOIN petrvs_icmbio_planos_entregas pe ON pe.id = pee.plano_entrega_id
JOIN petrvs_icmbio_unidades u          ON u.id = pe.unidade_id
WHERE pee.deleted_at IS NULL
  AND pe.deleted_at  IS NULL
  AND CAST(pe.data_inicio AS DATE) >= CAST('2025-01-01' AS DATE)
  AND CAST(pe.data_fim    AS DATE) <= CAST('2025-12-31' AS DATE)
  AND u.sigla IN ('<SIGLA1>', '<SIGLA2>')
GROUP BY u.sigla, pe.id, pe.status, pe.data_inicio, pe.data_fim
ORDER BY u.sigla, pe.data_inicio;
```

**Interpretação do `status_pe`:**

| Valor | Significado |
|---|---|
| `AVALIADO` | Plano encerrado e avaliado — query e sistema devem convergir |
| `ATIVO` | Plano aberto — divergência esperada (critério OCDE vs. fluxo formal) |
| `CONCLUIDO` | Plano encerrado sem avaliação — investigar contabilização no sistema |
| `CANCELADO` / `SUSPENSO` | Verificar se a query exclui corretamente pelo `deleted_at` |

---

### QD-03 — Listagem detalhada das entregas (para apêndice do relatório)

```sql
SELECT
    u.sigla,
    pe.status                    AS status_pe,
    CAST(pee.data_fim AS DATE)   AS prazo_entrega,
    SUBSTR(CAST(pee.id AS VARCHAR), 1, 8) AS id_curto,
    COALESCE(NULLIF(TRIM(pee.descricao), ''),
             NULLIF(TRIM(pee.descricao_entrega), '')) AS nome_entrega,
    pee.progresso_esperado       AS meta,
    pee.progresso_realizado      AS realizado,
    ROUND(COALESCE(pee.progresso_realizado, 0)
          / NULLIF(pee.progresso_esperado, 0) * 100, 1) AS taxa_perc
FROM petrvs_icmbio_planos_entregas_entregas pee
JOIN petrvs_icmbio_planos_entregas pe ON pe.id = pee.plano_entrega_id
JOIN petrvs_icmbio_unidades u          ON u.id = pe.unidade_id
WHERE pee.deleted_at IS NULL
  AND pe.deleted_at  IS NULL
  AND CAST(pe.data_inicio AS DATE) >= CAST('2025-01-01' AS DATE)
  AND CAST(pe.data_fim    AS DATE) <= CAST('2025-12-31' AS DATE)
  AND u.sigla IN ('<SIGLA1>', '<SIGLA2>')
ORDER BY u.sigla, pe.data_inicio, nome_entrega;
```

---

### QD-04 — Investigação de campo candidato a conclusão formal

Substituir `<campo_candidato>` pelo campo a investigar (ex: `homologado`, `status`, `avaliacao_id`).

```sql
SELECT
    u.sigla,
    pe.status                AS status_pe,
    pee.<campo_candidato>,
    COUNT(*)                 AS total
FROM petrvs_icmbio_planos_entregas_entregas pee
JOIN petrvs_icmbio_planos_entregas pe ON pe.id = pee.plano_entrega_id
JOIN petrvs_icmbio_unidades u          ON u.id = pe.unidade_id
WHERE pee.deleted_at IS NULL
  AND pe.deleted_at  IS NULL
  AND CAST(pe.data_inicio AS DATE) >= CAST('2025-01-01' AS DATE)
  AND CAST(pe.data_fim    AS DATE) <= CAST('2025-12-31' AS DATE)
  AND u.sigla IN ('<SIGLA1>', '<SIGLA2>')
GROUP BY u.sigla, pe.status, pee.<campo_candidato>
ORDER BY u.sigla, pe.status, pee.<campo_candidato>;
```

---

### QD-05 — Distribuição de valores numéricos (detecção de anomalias de escala)

Detecta valores fora da escala esperada — ex: frações 0–1 onde o padrão é 0–100. Substituir `<campo_numerico>` e `<tabela>` conforme o indicador.

```sql
SELECT
    CASE
        WHEN CAST(<campo_numerico> AS DECIMAL) <= 1    THEN 'a) 0.00-1.00 (possivel fracao)'
        WHEN CAST(<campo_numerico> AS DECIMAL) <= 10   THEN 'b) 1.01-10.00'
        WHEN CAST(<campo_numerico> AS DECIMAL) <= 50   THEN 'c) 10.01-50.00'
        WHEN CAST(<campo_numerico> AS DECIMAL) <= 100  THEN 'd) 50.01-100.00'
        ELSE                                                'e) >100.00 (possivel superexecucao)'
    END AS faixa,
    COUNT(*) AS total
FROM petrvs_icmbio_<tabela>
WHERE deleted_at IS NULL
  AND <campo_numerico> IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

**Interpretação e ação:**

| Resultado | Interpretação | Ação |
|---|---|---|
| Faixa a) com muitos registros | Campo usa escala fracionária (0–1) em vez de percentual (0–100) | Aplicar `CASE WHEN campo <= 1 THEN campo * 100 ELSE campo END`; adicionar flag `anomalia_escala` |
| Faixa e) com registros | Valores acima do máximo esperado | Listar casos para validação manual; pode ser superexecução legítima (ex: I03, I04) |
| Distribuição concentrada em d) | Escala 0–100 uniforme — sem anomalia | Nenhuma ação necessária |

> **Achado I03 (17/05/2026):** `progresso_esperado` tinha 1.988 registros na faixa 0–1. Solução: `CASE WHEN progresso_esperado <= 1 THEN progresso_esperado * 100 ELSE progresso_esperado END` + flag `anomalia_escala`.

---

### QD-06 — Amostra de campos JSON

Aplicável quando o indicador envolve campos armazenados como JSON (ex: `meta`, `realizado`). Executar antes de QD-07 para identificar a estrutura e os nomes de chave presentes.

```sql
SELECT
    u.sigla,
    pee.id,
    COALESCE(NULLIF(TRIM(pee.descricao), ''),
             NULLIF(TRIM(pee.descricao_entrega), '')) AS nome_entrega,
    pee.<campo_json_meta>      AS meta_json,
    pee.<campo_json_realizado> AS realizado_json
FROM petrvs_icmbio_planos_entregas_entregas pee
JOIN petrvs_icmbio_planos_entregas pe ON pe.id = pee.plano_entrega_id
JOIN petrvs_icmbio_unidades u          ON u.id = pe.unidade_id
WHERE pee.deleted_at IS NULL
  AND pe.deleted_at  IS NULL
  AND pee.<campo_json_meta> IS NOT NULL
  AND TRIM(CAST(pee.<campo_json_meta> AS VARCHAR)) <> ''
  AND TRIM(CAST(pee.<campo_json_meta> AS VARCHAR)) <> 'null'
ORDER BY u.sigla
LIMIT 30;
```

---

### QD-07 — Tipificação de campos de meta (JSON) e integridade

Contabiliza a distribuição dos tipos de meta. O Denodo VQL não tem parsing JSON nativo — a detecção do tipo usa `LIKE` sobre o texto do campo.

```sql
SELECT
    CASE
        WHEN TRIM(CAST(pee.<campo_json_meta> AS VARCHAR)) IS NULL
          OR TRIM(CAST(pee.<campo_json_meta> AS VARCHAR)) = ''
          OR TRIM(CAST(pee.<campo_json_meta> AS VARCHAR)) = 'null'
             THEN 'c) Nulo ou vazio'
        WHEN CAST(pee.<campo_json_meta> AS VARCHAR) LIKE '%quantitativo%'
             THEN 'a) Quantitativo {"quantitativo": N}'
        WHEN CAST(pee.<campo_json_meta> AS VARCHAR) LIKE '%porcentagem%'
             THEN 'b) Porcentagem {"porcentagem": X}'
        ELSE 'd) Outro formato (inspecionar amostra)'
    END AS tipo_meta,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS perc_total
FROM petrvs_icmbio_planos_entregas_entregas pee
JOIN petrvs_icmbio_planos_entregas pe ON pe.id = pee.plano_entrega_id
WHERE pee.deleted_at IS NULL
  AND pe.deleted_at  IS NULL
GROUP BY 1
ORDER BY 1;
```

**Interpretação:**

| Tipo | Significado | Ação Python |
|---|---|---|
| `{"quantitativo": N}` | Meta em unidades contáveis (portarias, relatórios, etc.) | `float(str(meta["quantitativo"]))` |
| `{"porcentagem": X}` | Meta como % de conclusão de processo contínuo | `float(str(meta["porcentagem"]))` |
| Nulo ou vazio | Meta não cadastrada | Excluir do cálculo; flag `sem_meta` |
| Outro formato | Novo padrão — inspecionar manualmente | Adicionar `elif` no parser |

> **Achado I03 (17/05/2026):** 10.334 de 10.396 entregas (99,4%) tinham `meta_json` parseável. Ver `IND_03.4_diagnostico_17.05.2026.py` Q4 para implementação completa do parser.

---

## 7. Checklist de conclusão por indicador

Copiar e marcar para cada ciclo. Substituir `XX` pelos valores reais.

```
Indicador  : IXX — <Nome>
Período    : AAAA-MM-DD a AAAA-MM-DD
Unidades   : <siglas amostradas>
Data início: DD/MM/AAAA

─── Fase 1 — Geração ────────────────────────────────────────────
[ ] A1 — IND_XX.1_run.py criado em ocde/indicadores/ e executado sem erros
[ ] A2 — IND_XX.2_<nome>_AAAAMMDD_HHMM.csv gerado em artefatos_local/ocde/entregas/YYYY-MM/
[ ] 6 colunas de metadado de período presentes (ciclo_tipo, periodo, ...)
[ ] Verificação inicial: sem zeros em massa, sem NULLs inesperados, nenhum período vazio
[ ] CSV encaminhado à equipe CGOV com instruções de amostragem

─── Fase 2 — Validação manual ───────────────────────────────────
[ ] A3 — IND_XX.3_PETRVS_consulta_DD.MM.AAAA.pdf criado em artefatos_local/validacao/
[ ] Hipóteses da equipe recebidas e documentadas

─── Fase 3 — Diagnóstico ────────────────────────────────────────
[ ] QD-01 executada — totais coerentes entre query e sistema
[ ] QD-02 executada — breakdown por pe.status analisado
[ ] QD-03 executada (se apêndice necessário)
[ ] QD-04 executada para campos candidatos (se divergência residual)
[ ] QD-05 executada — anomalia de escala verificada e documentada
[ ] QD-06 executada — estrutura JSON inspecionada (se aplicável)
[ ] QD-07 executada — tipificação de meta contabilizada (se aplicável)
[ ] A4 — IND_XX.4_diagnostico_DD.MM.AAAA.py criado em artefatos_local/ocde/diagnosticos/
[ ] CSVs diagnósticos em artefatos_local/ocde/diagnosticos/YYYY-MM/
[ ] A5 — IND_XX.5_relatorio_validacao_DD.MM.AAAA.md elaborado em artefatos_local/validacao/
[ ] Hipóteses classificadas: bug / semântica / metodologia / anomalia / sem divergência

─── Fase 4 — Correções e documentação ───────────────────────────
[ ] Correção aplicada em docs/06.X.X-iXX.md (se bug ou decisão metodológica)
[ ] Consultas SQL/*.sql atualizados (se correção)
[ ] IND_XX.1_run.py atualizado em ocde/indicadores/ (se decisão metodológica)
[ ] A2 regenerado após correções
[ ] CLAUDE.md — Seção 11 atualizada com status ✅

─── Encerramento ────────────────────────────────────────────────
[ ] Status final: Aprovado / Aprovação condicional / Reprovado
[ ] Nenhum artefato com credenciais ou dados pessoais versionado no git
```

---

## 8. Considerações específicas por eixo

### Eixo 2 — Execução (I02, I03, I04)

**Tabelas base:** `petrvs_icmbio_planos_entregas_entregas` + `petrvs_icmbio_planos_entregas`

**Variável-chave para análise:** `pe.status`

**Achado central — I02 (11/05/2026):** existem dois critérios distintos de "concluída":
- **Critério OCDE** (usado pelas queries): `progresso_realizado >= progresso_esperado`
- **Critério formal do PETRVS**: `pe.status = 'AVALIADO'` + etapa de homologação adicional

A query OCDE está correta; a diferença é semântica, não um bug. O campo `homologado` estava uniforme em `0` para todo o ciclo 2025 — não é o diferenciador formal.

**Achado I03 (17/05/2026):**

| Achado | Impacto |
|---|---|
| `progresso_esperado` = parcela do ciclo, não meta integral | Superexecuções (taxa > 100%) são artefato de planejamento conservador — legítimas |
| 1.988 registros com escala fracionária (0–1 em vez de 0–100) | Normalização ×100 aplicada + flag `anomalia_escala` |
| Campo `meta` (JSON): `{"quantitativo": N}` ou `{"porcentagem": X}` | Abordagem alternativa via taxa da meta integral implementada como segunda visão |
| 27 casos com `progresso_esperado=100` e taxa > 100% | Maioria legítima; ~10 casos com provável erro de preenchimento |

**Para I04:** mesma análise de `pe.status` se aplica. Scores > 100% são legítimos (superexecução confirmada).

---

### Eixo 3 — Carga de Trabalho (I05, I06, I07, I08)

**Tabelas base:** `petrvs_icmbio_planos_trabalhos_entregas` + `petrvs_icmbio_planos_trabalhos`

**Variável-chave:** `pt.status` (análogo ao `pe.status` do Eixo 2)

**Atenção ao campo de horas:**
- `planos_trabalhos_entregas` tem apenas `forca_trabalho` (% de dedicação, 0–100) como campo numérico
- Os campos `quantidade` e `horas_por_unidade` **não existem** nesta tabela — confirmado no Denodo em 15/05/2026
- Para calcular horas em I07/I08: combinar `forca_trabalho` com `planos_trabalhos.carga_horaria`

**Restrição de SQL:**
- CTEs recursivas não funcionam no Denodo VQL — usar aritmética de datas `(CAST(data1 AS DATE) - CAST(data2 AS DATE))` para diferença em dias
- I07 (bug corrigido 14/06/2026): o join de unidade deve usar `pe.unidade_id` (dono da entrega), não `pt.unidade_id` (unidade do servidor executante)

---

### Eixo 4 — Desempenho e Avaliação (I09, I10, I11, I12)

**Tabelas base:** `petrvs_icmbio_avaliacoes` + `petrvs_icmbio_tipos_avaliacoes_notas` + `petrvs_icmbio_planos_trabalhos`

**Escala de avaliação confirmada (12/06/2026):**

| `sequencia` | Conceito |
|---|---|
| 1 | Excepcional |
| 2 | Alto desempenho |
| 3 | Adequado |
| 4 | Inadequado |
| 5 | Não executado |

> **Atenção:** a escala é **decrescente** — `sequencia=1` é o melhor conceito. Inversão com `score = 6 - sequencia` é necessária para transformar a escala em ordem crescente de desempenho (I09, I12). Usando `sequencia` diretamente sem inversão, a média mais alta indica pior desempenho.

**Bugs de escala corrigidos:**

| Indicador | Bug original | Correção |
|---|---|---|
| I10 | `sequencia=2` para "Inadequado" (= "Alto desempenho" real) | `sequencia=4` — corrigido em 12/06/2026 |
| I11 | `sequencia=5` para "Excepcional" (= "Não executado" real) | `sequencia=1` — corrigido em 12/06/2026 |
| I12 | Sinal do `diferenca_direcional` invertido | `score = 6 - sequencia` — corrigido em 12/06/2026 |
| I09 | `sequencia=2` para "Inadequado"; média ~2,11 interpretada incorretamente | Interpretar como "entre Excepcional e Alto desempenho"; revisar limiares de classificação |

**Regras de filtragem:**
- Usar apenas avaliações com `av.deleted_at IS NULL`
- Campo de nota: `tan.sequencia` em `tipos_avaliacoes_notas` (join via `av.tipo_avaliacao_nota_id`)

---

## 9. Referências de implementação

**Modelos de script de geração (em `ocde/indicadores/`):**

| Script | Complexidade | Referência para |
|---|---|---|
| `IND_02.1_run.py` | Base (GROUP BY simples, ciclo PE) | Indicadores sem window functions |
| `IND_05.1_run.py` | Intermediária (window function, ciclo PT) | Indicadores com RANK/NTILE |
| `IND_07.1_run.py` | Avançada (múltiplos CTEs, join cruzado PE+PT) | Indicadores com cálculo de horas |

**Relatórios de validação disponíveis em `artefatos_local/validacao/`:**

| Indicador | Data | Status |
|---|---|---|
| I01 — Proporção por regime | 26/05/2026 | ✅ Aprovação condicional — A3 pendente |
| I02 — Taxa de cumprimento | 11/05/2026 | ✅ Aprovado (contra dump MySQL — ver nota) |
| I03 — Taxa por entrega | 17/05/2026 | ✅ Aprovação condicional |
| I04 — Score de atingimento | 24/05/2026 | ✅ Aprovação condicional |
| I05 — Distribuição por servidor | 24/05/2026 | ✅ Aprovação condicional |
| I06 — Grau de responsabilidade | 24/05/2026 | ✅ Aprovação condicional |
| I09 — Média de avaliação | 24/05/2026 | ✅ Aprovação condicional |
| I10 — % Inadequados | 12/06/2026 | ✅ Aprovação condicional — bug de escala corrigido |
| I11 — % Excepcionais | 12/06/2026 | ✅ Aprovação condicional — bug de escala corrigido |
| I12 — Coerência PT × PE | 12/06/2026 | ✅ Aprovação condicional — sinal corrigido |
| I07, I08 | — | ⬜ Consulta manual CGOV pendente |

> **Nota I02:** o relatório foi elaborado contra o dump MySQL de 26/02/2026. As conclusões metodológicas são válidas, mas os números concretos refletem o estado de fevereiro/2026. Com o Denodo em tempo real, re-verificar os totais se necessário.

---

*Documento público — não contém credenciais ou dados pessoais. Protocolo consolidado em 18/06/2026.*
