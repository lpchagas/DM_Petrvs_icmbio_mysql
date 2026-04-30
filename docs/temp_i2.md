# 📄 Documentação Técnica: Indicador 2 - Taxa de Cumprimento das Entregas (MySQL Edition)

**Público-Alvo:** Cientistas de Dados / Engenheiros de Analytics Sênior  
**SGBD Alvo:** MySQL 8.x  
**Contexto de Negócio:** Mensurar se as equipes do ICMBio executam o que planejam no Programa de Gestão e Desempenho (PGD), validando o realismo do planejamento (sistema Petrvs).

---

## 1. Mapeamento de Domínio e Lógica do Indicador

O **Indicador 2 (Deliverables achievement rate)** avalia a proporção de entregas concluídas em relação ao total de entregas planejadas em um ciclo.

*   **Granularidade (Grão):** Agregação por Unidade Executora (`id_unidade_executora`).
*   **Fórmula Base:** `I = (A / B) * 100`
    *   **A (Numerador):** Contagem de entregas cujo status de atingimento é verdadeiro.
    *   **B (Denominador):** Contagem absoluta de entregas planejadas no ciclo.
*   **Regra de Conclusão (Limiar/Threshold):** Uma entrega só conta como "1" no Numerador (A) se a meta executada for **maior ou igual** à meta planejada. Se não atingir os 100% da meta unitária daquela entrega, ela recebe valor `0` para o cálculo deste indicador.
*   **Categorização Analítica (Bucketing):** As unidades devem ser clusterizadas nos grupos: A (>=90%), B (70-89%), C (50-69%) e D (<50%).

> **Justificativa da Regra:** Ao adotar um valor binário (1 ou 0) para o atingimento da meta da entrega, evitamos distorções onde uma única entrega superexecutada (ex: 300%) compense o não-cumprimento de várias outras entregas (o que inflaria falsamente a taxa de cumprimento geral da unidade).

---

## 2. Premissas de Modelagem (Esquema Esperado)

Para que a query funcione com máxima eficiência no MySQL, assume-se a existência de uma tabela transacional ou *Fact Table* no Data Warehouse que registra o ciclo no grão da **Entrega**.

```sql
-- DDL Referência para compreensão da Query
CREATE TABLE fato_plano_entregas (
    id_entrega VARCHAR(50) PRIMARY KEY,
    id_unidade_executora INT NOT NULL,
    status_plano VARCHAR(20) NOT NULL, -- Ex: 'CONCLUIDO', 'EM_ANDAMENTO', 'CANCELADO'
    data_fim_ciclo DATE NOT NULL,
    meta_planejada DECIMAL(10,2) NOT NULL,
    meta_executada DECIMAL(10,2) DEFAULT 0.00
);
```

> **Justificativa dos Tipos:** Utilizamos `DECIMAL` para as metas em vez de `FLOAT` ou `DOUBLE` para evitar erros de precisão de ponto flutuante inerentes à arquitetura do MySQL ao realizar comparações de igualdade/maioria (`>=`).

---

## 3. Implementação SQL (MySQL 8.x)

Abaixo apresento a query otimizada. Utilizei uma CTE (Common Table Expression) para modularizar o código, calculando primeiro as taxas brutas e, em seguida, aplicando a lógica de agrupamento (Categorias A, B, C, D).

```sql
WITH calculo_base AS (
    SELECT 
        id_unidade_executora,
        
        -- Denominador (B): Total de entregas planejadas no ciclo válido
        COUNT(id_entrega) AS total_entregas_planejadas, 
        
        -- Numerador (A): Somatório condicional baseando-se no threshold de atingimento
        SUM(CASE 
                WHEN meta_executada >= meta_planejada THEN 1 
                ELSE 0 
            END) AS total_entregas_concluidas,
            
        -- Cálculo da Taxa bruta (A/B) com proteção contra Divisão por Zero
        ROUND(
            (
                SUM(CASE WHEN meta_executada >= meta_planejada THEN 1.0 ELSE 0.0 END) 
                / 
                NULLIF(COUNT(id_entrega), 0)
            ) * 100, 
        2) AS taxa_cumprimento_perc
        
    FROM 
        fato_plano_entregas
    WHERE 
        status_plano = 'CONCLUIDO' 
        -- Filtro temporal parametrizável:
        AND data_fim_ciclo = '2025-12-31' 
    GROUP BY 
        id_unidade_executora
)
SELECT 
    id_unidade_executora,
    total_entregas_planejadas,
    total_entregas_concluidas,
    taxa_cumprimento_perc,
    
    -- Bucketing (Classificação de Performance)
    CASE 
        WHEN taxa_cumprimento_perc >= 90.00 THEN 'Grupo A (90-100%)'
        WHEN taxa_cumprimento_perc >= 70.00 AND taxa_cumprimento_perc < 90.00 THEN 'Grupo B (70-89%)'
        WHEN taxa_cumprimento_perc >= 50.00 AND taxa_cumprimento_perc < 70.00 THEN 'Grupo C (50-69%)'
        WHEN taxa_cumprimento_perc < 50.00 THEN 'Grupo D (<50%)'
        ELSE 'Não Classificado'
    END AS grupo_performance
FROM 
    calculo_base
ORDER BY 
    taxa_cumprimento_perc DESC;
```

### Justificativas Técnicas do Código SQL:
1. **Uso de `NULLIF(..., 0)`:** O MySQL, por padrão, lança warnings ou dependendo do `sql_mode` (como `ERROR_FOR_DIVISION_BY_ZERO`), retorna um erro fatal ao dividir por zero. O `NULLIF` transforma o 0 do denominador em `NULL`, fazendo com que toda a divisão resulte em `NULL` silenciosamente em vez de quebrar a pipeline de dados.
2. **Uso de `1.0` e `0.0` no CASE WHEN interno da divisão:** Força o MySQL a tratar o numerador como ponto flutuante/decimal antes da divisão, evitando truncamentos inteiros inesperados que acontecem em algumas versões antigas de motores relacionais.

---

## 4. Tratamento de Exceções e Otimização de Performance no MySQL

Para garantir que a consulta rode de forma performática (sub-segundo) ao plugar um DBeaver ou uma ferramenta de BI diretamente no MySQL local:

### 4.1. Índices Recomendados (Performance)
A cláusula `WHERE` e o `GROUP BY` determinam o plano de execução (*execution plan*). Recomenda-se a criação de um índice composto para evitar um *Full Table Scan*:

```sql
CREATE INDEX idx_status_data_unidade 
ON fato_plano_entregas (status_plano, data_fim_ciclo, id_unidade_executora);
```
> **Justificativa:** No MySQL, a ordem das colunas no índice importa (Regra do prefixo mais à esquerda). Como as filtragens (`WHERE`) ocorrem em `status_plano` e `data_fim_ciclo`, e o agrupamento (`GROUP BY`) em `id_unidade_executora`, este índice cobrirá a query perfeitamente (Covering Index), possivelmente reduzindo o acesso ao disco e processando tudo em memória (Using Index no `EXPLAIN`).

### 4.2. Edge Cases (Comportamento de Negócio vs Dados)
* **Entregas Canceladas:** Garanta que a sua ingestão do Petrvs atualize corretamente o `status_plano`. Se o filtro `status_plano = 'CONCLUIDO'` for esquecido, metas canceladas que vierem com `meta_executada = 0` vão derrubar drasticamente a taxa de cumprimento da unidade de forma errônea.
* **Metas Negativas:** Se existir regra de negócio permitindo `meta_planejada` negativa (ex: redução de incêndios), a lógica relacional `>=` pode inverter o sentido esperado. *(Assumimos pelo escopo que todas as metas no banco Petrvs possuem valor absoluto >= 0)*. Caso possa ser negativo, deve-se aplicar a função `ABS()` ao redor dos campos na etapa do CTE.