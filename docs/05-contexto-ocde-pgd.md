# Contexto Estratégico dos Indicadores PGD (Projeto OCDE/ICMBio)

Este documento consolida as diretrizes do projeto piloto da OCDE no ICMBio para o Programa de Gestão e Desempenho (PGD), servindo como base de contexto para as consultas SQL deste repositório.

## 1. Visão Geral

O projeto piloto **"Fortalecendo a capacidade organizacional no Brasil"** (OCDE, MGI, SPU, ICMBio, UFRN) visa transformar o PGD de uma ferramenta de controle de frequência em um instrumento de **gestão de desempenho e tomada de decisão baseada em evidências**.

Este esforço está diretamente alinhado às competências da **Coordenação de Governança (CGOV)** (Portaria ICMBio nº 5.592/2025), fornecendo dados quantitativos para:

- Monitoramento da Cadeia de Valor e Alinhamento Estratégico
- Dimensionamento da Força de Trabalho (DFT)
- Governança, Cultura de Controle e Gestão de Riscos

O *Performance Toolkit* da OCDE estabelece **12 indicadores chave**, divididos em 4 eixos estruturantes.

---

## 2. Os 4 Eixos e os 12 Indicadores

### Eixo 1: Trabalho Remoto

| Indicador | Descrição | Status neste repositório |
|---|---|---|
| I01 | Proporção de servidores por regime de trabalho | Pendente — requer tabela de regimes |

### Eixo 2: Execução

| Indicador | Descrição | Status neste repositório |
|---|---|---|
| I02 | Taxa de cumprimento das entregas | Disponível |
| I03 | Taxa de cumprimento de metas por entrega | Disponível |
| I04 | Índice de atingimento de metas (Score) | Disponível |

### Eixo 3: Carga de Trabalho

| Indicador | Descrição | Status neste repositório |
|---|---|---|
| I05 | Distribuição das entregas entre os servidores | Disponível |
| I06 | Grau de responsabilidade pelas entregas | Disponível |
| I07 | Horas por entrega — planejadas | Disponível |
| I08 | Proporção de horas por entrega — planejadas | Disponível |

### Eixo 4: Desempenho e Avaliação

| Indicador | Descrição | Status neste repositório |
|---|---|---|
| I09 | Média da avaliação do Plano de Trabalho | Pendente — mapeamento em andamento |
| I10 | Percentual de avaliações inadequadas (nota 2) | Pendente |
| I11 | Percentual de avaliações excepcionais (nota 5) | Pendente |
| I12 | Coerência da avaliação entre PT e PE | Pendente |

---

## 3. Fórmulas dos Indicadores Disponíveis

### I02 — Taxa de cumprimento das entregas
```
I = (A ÷ B) × 100
A = Entregas concluídas (meta executada >= meta planejada)
B = Total de entregas planejadas no período
```

### I03 — Taxa de cumprimento de metas por entrega
```
I = (A ÷ B) × 100  (por entrega individual)
A = Meta executada
B = Meta planejada
```

### I04 — Índice de atingimento de metas
```
I = (Σ (A ÷ B) ÷ C) × 100
A = Meta executada por entrega
B = Meta planejada por entrega
C = Total de entregas da unidade
```

### I05 — Distribuição das entregas
```
Média = Total de atribuições ÷ Total de servidores (por unidade)
```

### I06 — Grau de responsabilidade
```
Contagem de servidores por entrega, agrupada em faixas:
1 servidor / 2 servidores / 3 servidores / 4+ servidores
```

### I07 — Horas por entrega — planejadas
```
Horas = Σ (dias úteis do plano × horas/dia × forca_trabalho%) por entrega
Dias úteis = dias do período excluindo fins de semana e feriados nacionais
```

### I08 — Proporção de horas por entrega
```
I = (A ÷ B) × 100
A = Horas alocadas à entrega (I07)
B = Total de horas disponíveis da unidade no período
```

---

## 4. Regras gerais de uso das consultas

### Bloco de parâmetros padrão

Todas as consultas usam um bloco `parametros` no início:

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
)
```

- Ajuste `data_inicio` e `data_fim` conforme o período de análise.
- `incluir_excluidos = 0`: apenas registros ativos (`deleted_at is null`).
- `incluir_excluidos = 1`: inclui registros excluídos logicamente (útil para auditoria).

### Exclusão lógica no PETRVS

O PETRVS não apaga registros fisicamente. Registros excluídos recebem uma data em `deleted_at`. O campo `incluir_excluidos` controla se esses registros entram nos indicadores.

### Nomenclatura das entregas

O campo principal do nome da entrega é `descricao`. Se estiver vazio, usa-se `descricao_entrega` como fallback. Nenhuma entrega deve aparecer com nome em branco nos resultados.

---

## 5. Tabelas do PETRVS utilizadas

| Tabela | Papel nos indicadores |
|---|---|
| `planos_entregas_entregas` | Dados de metas e progresso (I02, I03, I04, I07, I08) |
| `planos_trabalhos` | Planos de trabalho dos servidores (I05, I06, I07, I08) |
| `planos_trabalhos_entregas` | Vínculo servidor ↔ entrega + percentual de dedicação (I05, I06, I07, I08) |
| `unidades` | Nome e sigla das unidades |
| `usuarios` | Nome dos servidores |
| `avaliacoes` | Notas de avaliação (I09 a I12 — pendente) |
