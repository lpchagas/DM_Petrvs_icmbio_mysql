# Manual Técnico — Indicadores OCDE/PGD ICMBio (MySQL)

Este documento é o índice do manual técnico dos 12 indicadores do *Performance Toolkit* OCDE/PGD, implementados para execução direta na base original PETRVS em MySQL, sem datamart intermediário.

Cada indicador tem seu próprio documento com: finalidade, consulta SQL completa, explicação passo a passo dos blocos e interpretação dos resultados com exemplos do ICMBio.

Para o contexto estratégico do projeto, fórmulas e status de cada indicador, consulte [05-contexto-ocde-pgd.md](05-contexto-ocde-pgd.md).

---

## Como usar

1. Abra a conexão MySQL `petrvs_icmbio` no DBeaver
2. Navegue até o indicador desejado na tabela abaixo
3. Copie a consulta completa do documento do indicador para um SQL Editor
4. Ajuste `data_inicio` e `data_fim` no bloco `parametros` no topo da consulta
5. Execute a consulta completa (não execute blocos isolados)
6. Exporte o resultado: botão direito → Export → CSV ou Excel

### Padrão do bloco `parametros`

Todas as consultas começam com este bloco de controle:

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos   -- 0 = só ativos; 1 = inclui excluídos
)
```

Os indicadores I07 e I08 têm um campo adicional:

```sql
        8 as horas_por_dia       -- jornada diária em horas (padrão: 8)
```

---

## Índice dos indicadores

### Eixo 1 — Trabalho Remoto

Contexto do eixo: [06.1-eixo1.md](06.1-eixo1.md)

| Indicador | Descrição | Nível | Documento |
| --- | --- | --- | --- |
| I01 | Proporção de servidores por regime de trabalho | Institucional e por unidade | [06.1.1-i01.md](06.1.1-i01.md) |

---

### Eixo 2 — Execução

Contexto do eixo: [06.2-eixo2.md](06.2-eixo2.md)

| Indicador | Descrição | Nível | Documento |
| --- | --- | --- | --- |
| I02 | Taxa de cumprimento das entregas | Por unidade | [06.2.1-i02.md](06.2.1-i02.md) |
| I03 | Taxa de cumprimento de metas por entrega | Por entrega | [06.2.2-i03.md](06.2.2-i03.md) |
| I04 | Índice de atingimento de metas | Por unidade (score médio) | [06.2.3-i04.md](06.2.3-i04.md) |

---

### Eixo 3 — Carga de Trabalho

Contexto do eixo: [06.3-eixo3.md](06.3-eixo3.md)

| Indicador | Descrição | Nível | Documento |
| --- | --- | --- | --- |
| I05 | Distribuição das entregas entre os servidores | Por servidor | [06.3.1-i05.md](06.3.1-i05.md) |
| I06 | Grau de responsabilidade pelas entregas | Por entrega | [06.3.2-i06.md](06.3.2-i06.md) |
| I07 | Horas por entrega — planejadas (absolutas) | Por entrega | [06.3.3-i07.md](06.3.3-i07.md) |
| I08 | Proporção de horas por entrega — planejadas (%) | Por entrega | [06.3.4-i08.md](06.3.4-i08.md) |

---

### Eixo 4 — Desempenho e Avaliação

Contexto do eixo: [06.4-eixo4.md](06.4-eixo4.md)

> **Pré-requisito:** execute as consultas de mapeamento do documento do Eixo 4 antes de rodar qualquer indicador deste eixo. Os campos de avaliação variam conforme a versão e configuração do PETRVS instalado.

| Indicador | Descrição | Nível | Documento |
| --- | --- | --- | --- |
| I09 | Média da avaliação do Plano de Trabalho por unidade | Por unidade | [06.4.1-i09.md](06.4.1-i09.md) |
| I10 | Percentual de avaliações inadequadas (nota 2) | Por unidade | [06.4.2-i10.md](06.4.2-i10.md) |
| I11 | Percentual de avaliações excepcionais (nota 5) | Por unidade | [06.4.3-i11.md](06.4.3-i11.md) |
| I12 | Coerência entre avaliação do PT e do PE | Por unidade | [06.4.4-i12.md](06.4.4-i12.md) |

---

## Requisitos técnicos

| Requisito | Afeta |
| --- | --- |
| MySQL 8.0+ obrigatório | I05 (window function `AVG() OVER`), I07 e I08 (CTE recursiva `WITH RECURSIVE`) |
| `SET SESSION cte_max_recursion_depth = 5000` | I07 e I08 com períodos superiores a ~2,7 anos |
| Feriados móveis inseridos manualmente | I07 e I08 (Sexta-feira da Paixão, Corpus Christi — ver bloco `feriados_moveis`) |

Confirme a versão do banco com:

```sql
select version();
```

---

## Estrutura do manual técnico

Cada documento de eixo apresenta:

- Contexto estratégico do eixo e sua relevância para o ICMBio
- Tabelas do PETRVS utilizadas e relacionamentos
- Consultas de mapeamento/auditoria a executar antes dos indicadores
- Relação com os demais eixos
- Limitações conhecidas

Cada documento de indicador apresenta:

1. **Finalidade** — pergunta central respondida
2. **Consulta completa MySQL** — pronta para copiar e executar no DBeaver
3. **Passos da consulta** — explicação de cada bloco CTE com analogias para usuários de negócio
4. **Como interpretar o resultado** — tabela de colunas + exemplos nomeados com unidades do ICMBio (CGOV, CGOF, AUDIT, DIREC, COGEO)
