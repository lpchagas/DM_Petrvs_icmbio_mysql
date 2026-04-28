# Estrutura do Banco de Dados PETRVS — Frame MySQL

**Última atualização:** 28 de abril de 2026  
**Fonte:** Dump `D.PGD.MGI.001.DUMP.20260226ICMBIO.sql`  
**Total de tabelas:** 130+

---

## 1. Visão Geral: Arquitetura em Camadas

O banco de dados PETRVS é organizado em **4 camadas de abstração**, que representam o fluxo de dados do sistema de gestão de desempenho do ICMBio:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CAMADA DE REFERÊNCIA                                     │
│    (usuários, unidades, tipos de dados, configurações)     │
├─────────────────────────────────────────────────────────────┤
│ 2. CAMADA DE PLANEJAMENTO                                   │
│    (planos de entregas, planos de trabalho, metas)         │
├─────────────────────────────────────────────────────────────┤
│ 3. CAMADA DE EXECUÇÃO                                       │
│    (atividades, tarefas, ocorrências, afastamentos)        │
├─────────────────────────────────────────────────────────────┤
│ 4. CAMADA DE AVALIAÇÃO & RESULTADO                          │
│    (avaliações, progressos, consolidações, resultados)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Camada 1: Referência (Foundation)

Tabelas que servem como "base de dados" para todo o sistema. Mudam raramente.

### 2.1 Usuários e Autorização

| Tabela | Descrição | Registros esperados | Soft-delete |
|---|---|---|---|
| `usuarios` | Cadastro de todos os servidores/usuários do ICMBio | 1000+ | Sim (`deleted_at`) |
| `perfis` | Perfis de acesso (permissões) | 5-10 | Sim |

**Campos críticos de `usuarios`:**
- `id` (char 36): ID único (UUID)
- `nome`, `email`, `cpf`, `matricula`: Identidade
- `situacao_funcional`: Enum com 50+ estados (ativo permanente, aposentado, cedido, etc.)
- `situacao_siape`: Enum (ATIVO, INATIVO, ATIVO_TEMPORARIO)
- `tipo_modalidade_id`: Regime de trabalho (presencial/híbrido/remoto)
- `participa_pgd`: Se participa do Programa de Gestão e Desempenho (sim/não)

---

### 2.2 Estrutura Organizacional

| Tabela | Descrição | Registros esperados | Soft-delete |
|---|---|---|---|
| `unidades` | Departamentos, coordenações, diretorias do ICMBio | 100+ | Sim |
| `unidades_integrantes` | Composição de unidades (hierarquia) | 1000+ | Sim |
| `cidades` | Cidades brasileiras | 5000+ | Não |
| `entidades` | Órgãos/entidades vinculadas | 10+ | Sim |

**Campos críticos de `unidades`:**
- `id` (char 36): ID único
- `sigla`: Código curto (ex: CGOV, AUDIT, etc.)
- `nome`: Nome completo
- `path`: Caminho hierárquico (ex: `/ICMBio/CGOV/SUGESTAO/`)
- `unidade_pai_id`: Referência à unidade superior (hierarquia)
- `instituidora`: Flag se é unidade principal
- `deleted_at`: Soft-delete

---

### 2.3 Tipos e Catálogos

Mais de 40 tabelas de `tipos_*` que servem como enumerações/listas de referência. Exemplos:

| Tabela | Descrição | Uso |
|---|---|---|
| `tipos_modalidades` | Regimes de trabalho | Vinculado em `planos_trabalhos` |
| `tipos_atividades` | Categorias de atividades | Vinculado em `atividades` |
| `tipos_avaliacoes` | Tipos de avaliação (PT, PE, etc.) | Vinculado em `avaliacoes` |
| `tipos_justificativas` | Motivos de atraso/não conclusão | Vinculado em justificativas |
| `tipos_motivos_afastamentos` | Tipos de afastamento (férias, licença, etc.) | Vinculado em `afastamentos` |
| `tipos_tarefas` | Categorias de tarefas | Vinculado em `atividades_tarefas` |

---

### 2.4 Currículos e Profissionais

| Tabela | Descrição |
|---|---|
| `curriculuns` | Curricula dos usuários |
| `curriculuns_graduacoes` | Educação formal |
| `curriculuns_profissionais` | Experiência profissional |
| `historicos_funcoes` | Histórico de funções ocupadas |
| `historicos_lotacoes` | Histórico de lotações (unidades onde trabalhou) |

---

## 3. Camada 2: Planejamento (Planning)

Tabelas que representam o planejamento de entregas e planos de trabalho no período.

### 3.1 Estrutura de Planejamento

| Tabela | Descrição | Chave estrangeira em |
|---|---|---|
| `planejamentos` | Ciclos de planejamento (ex: 2025, 2026) | `unidades`, `entidades` |
| `planejamentos_objetivos` | Objetivos estratégicos do planejamento | `planejamentos` |

---

### 3.2 Planos de Entregas (PE)

**Tabelas principais:**

| Tabela | Descrição | Soft-delete | Relacionamento crítico |
|---|---|---|---|
| `planos_entregas` | **Plano de Entrega** — ciclo de entregas de uma unidade | Sim | `unidades`, `programas`, `planejamentos` |
| `planos_entregas_entregas` | **Entrega individual** — cada entrega dentro de um plano | Sim | `planos_entregas`, `unidades` |

**Campos críticos de `planos_entregas`:**
- `id`, `numero`, `nome`: Identificação
- `status`: Enum (INCLUIDO, HOMOLOGANDO, ATIVO, CONCLUIDO, AVALIADO, SUSPENSO, CANCELADO)
- `data_inicio`, `data_fim`: Período do plano
- `unidade_id`: Unidade responsável
- `criacao_usuario_id`: Quem criou

**Campos críticos de `planos_entregas_entregas` (CRÍTICO PARA INDICADORES):**
- `id`, `descricao`, `descricao_entrega`: Nome da entrega
- `progresso_esperado`, `progresso_realizado`: **METAS** (decimal 5.2)
- `data_inicio`, `data_fim`: Período da entrega
- `homologado`: Flag de aprovação
- `meta`, `realizado`: JSON com estrutura detalhada
- `plano_entrega_id`: Referência ao plano pai
- `unidade_id`: Unidade responsável
- `deleted_at`: Soft-delete

---

### 3.3 Planos de Trabalho (PT)

**Tabelas principais:**

| Tabela | Descrição | Soft-delete | Crítico para indicadores |
|---|---|---|---|
| `planos_trabalhos` | **Plano de Trabalho** — plano individual de um servidor | Sim | ✓ I05, I06, I07, I08 |
| `planos_trabalhos_entregas` | **Vínculo PT ↔ Entrega** — servidor responsável por entrega | Sim | ✓ I05, I06, I07, I08 |

**Campos críticos de `planos_trabalhos`:**
- `id`, `numero`: Identificação
- `usuario_id`: Servidor responsável
- `unidade_id`: Unidade do servidor
- `data_inicio`, `data_fim`: Vigência do plano
- `carga_horaria`: Horas totais do período
- `tempo_proporcional`: Horas ajustadas para o período
- `status`: Enum (INCLUIDO, AGUARDANDO_ASSINATURA, ATIVO, CONCLUIDO, etc.)
- `tipo_modalidade_id`: Regime de trabalho (presencial/híbrido/remoto)
- `deleted_at`: Soft-delete

**Campos críticos de `planos_trabalhos_entregas` (CRÍTICO PARA INDICADORES):**
- `id`: Identificação do link
- `plano_trabalho_id`: Referência ao plano
- `plano_entrega_entrega_id`: Referência à entrega (da tabela `planos_entregas_entregas`)
- `forca_trabalho`: **Percentual de dedicação** (decimal 5.2, ex: 40 para 40%)
- `descricao`: Descrição do trabalho a fazer
- `deleted_at`: Soft-delete

---

### 3.4 Vinculações Estratégicas

| Tabela | Descrição | Vincula |
|---|---|---|
| `planos_entregas_entregas_objetivos` | Entregas vinculadas a objetivos estratégicos | `planejamentos_objetivos` |
| `planos_entregas_entregas_processos` | Entregas vinculadas a processos | `cadeias_valores_processos` |
| `planos_entregas_entregas_produtos` | Entregas vinculadas a produtos | `produtos` |

---

## 4. Camada 3: Execução (Execution)

Tabelas que registram o que realmente aconteceu durante o período.

### 4.1 Atividades

| Tabela | Descrição | Soft-delete |
|---|---|---|
| `atividades` | Atividades atribuídas (podem ser pontuais ou ligadas a entregas) | Sim |
| `atividades_pausas` | Pausas em atividades | Sim |
| `atividades_tarefas` | Tarefas dentro de atividades | Sim |

---

### 4.2 Ocorrências

| Tabela | Descrição |
|---|---|
| `ocorrencias` | Eventos de desvio (atraso, impedimento, etc.) |

---

### 4.3 Afastamentos

| Tabela | Descrição | Campo importante |
|---|---|---|
| `afastamentos` | Ausências do servidor (férias, licença, luto, etc.) | `tipo_motivo_afastamento_id`, `data_inicio`, `data_fim`, `horas` |

---

### 4.4 Consolidações

| Tabela | Descrição | Agregação |
|---|---|---|
| `planos_trabalhos_consolidacoes` | Consolidação do PT após período | Agrupa atividades, afastamentos, ocorrências |
| `planos_trabalhos_consolidacoes_atividades` | Link para atividades executadas | Referência |
| `planos_trabalhos_consolidacoes_afastamentos` | Link para afastamentos no período | Referência |
| `planos_trabalhos_consolidacoes_ocorrencias` | Link para ocorrências no período | Referência |

---

### 4.5 Comparecimentos

| Tabela | Descrição |
|---|---|
| `comparecimentos` | Registros de presença/ausência por consolidação |

---

## 5. Camada 4: Avaliação & Resultado

Tabelas que registram as avaliações finais e resultados.

### 5.1 Avaliações

| Tabela | Descrição | Soft-delete | Crítico |
|---|---|---|---|
| `avaliacoes` | Avaliação de um PT ou PE | Sim | Para I09, I10, I11, I12 |
| `tipos_avaliacoes` | Tipos de avaliação (PT, PE, autoavaliação, etc.) | Sim | Referência |
| `tipos_avaliacoes_notas` | Escala de notas (1-5, conceitos) | Não | Referência |

**Campos críticos de `avaliacoes`:**
- `id`: Identificação
- `plano_trabalho_consolidacao_id`: Qual PT está sendo avaliado
- `plano_entrega_id`: Qual PE está sendo avaliado (pode ser nulo se é PT)
- `tipo_avaliacao_id`: Tipo de avaliação
- `tipo_avaliacao_nota_id`: Nota/conceito atribuído
- `avaliador_id`: Usuário que fez a avaliação
- `deleted_at`: Soft-delete

---

### 5.2 Avaliações de Entregas (Checklist)

| Tabela | Descrição |
|---|---|
| `avaliacoes_entregas_checklist` | Checklist de avaliação de uma entrega |

---

### 5.3 Progressos

| Tabela | Descrição |
|---|---|
| `planos_entregas_entregas_progressos` | Histórico de registros de progresso (quem registrou, quando) |

---

## 6. Padrões de Design Observados

### 6.1 Soft-Delete

**Padrão:** Quase todas as tabelas de negócio têm uma coluna `deleted_at` (timestamp).

- `deleted_at IS NULL` → registro ativo
- `deleted_at IS NOT NULL` → registro excluído logicamente (ainda existe no BD, só marcado como deletado)

**Motivo:** Rastreabilidade e auditoria. Dados nunca são apagados fisicamente.

**Implicação:** Todas as queries dos indicadores devem filtrar `deleted_at IS NULL` ou incluir explicitamente deletados conforme necessário.

---

### 6.2 Timestamps de Auditoria

**Padrão:** Quase todas as tabelas têm:
- `created_at` (timestamp): Quando foi criado
- `updated_at` (timestamp): Última modificação
- `deleted_at` (timestamp): Quando foi deletado

---

### 6.3 UUID como Chave Primária

**Padrão:** Todas as tabelas usam `id` do tipo `char(36)` (UUID em formato string).

**Formato:** ex: `550e8400-e29b-41d4-a716-446655440000`

---

### 6.4 Status como ENUM

Muitas tabelas de negócio usam enums para estados:
- `planos_entregas.status`: INCLUIDO, HOMOLOGANDO, ATIVO, CONCLUIDO, AVALIADO, SUSPENSO, CANCELADO
- `planos_trabalhos.status`: INCLUIDO, AGUARDANDO_ASSINATURA, ATIVO, CONCLUIDO, AVALIADO, SUSPENSO, CANCELADO
- `atividades.status`: INCLUIDO, INICIADO, PAUSADO, CONCLUIDO

---

### 6.5 Dados Estruturados como JSON

Várias tabelas usam colunas JSON para flexibilidade:
- `planos_entregas_entregas.meta`: JSON com estrutura de meta
- `planos_entregas_entregas.realizado`: JSON com estrutura de realizado
- `atividades.etiquetas`, `atividades.checklist`: JSON

---

### 6.6 Decimais para Percentuais e Proporções

**Padrão:** `decimal(5,2)` para valores de 0-100 ou 0-1000:
- `planos_entregas_entregas.progresso_esperado`: Decimal (ex: 100.00)
- `planos_entregas_entregas.progresso_realizado`: Decimal (ex: 75.50)
- `planos_trabalhos_entregas.forca_trabalho`: Decimal (ex: 40.00 para 40%)

---

## 7. Tabelas Críticas para os Indicadores OCDE/PGD

As **6 tabelas principais** para calcular os indicadores I02-I08:

```
INDICADORES I02, I03, I04 (Execução de Entregas)
└── planos_entregas_entregas
    ├── progresso_esperado (meta planejada)
    ├── progresso_realizado (meta executada)
    ├── unidade_id
    └── deleted_at

INDICADORES I05, I06 (Distribuição de Entregas)
└── planos_trabalhos_entregas
    ├── forca_trabalho (% dedicação)
    ├── plano_trabalho_id
    ├── plano_entrega_entrega_id
    └── planos_trabalhos
        ├── usuario_id (servidor)
        ├── unidade_id
        └── data_inicio, data_fim

INDICADORES I07, I08 (Horas por Entrega)
└── planos_trabalhos_entregas + planos_trabalhos + planos_entregas_entregas
    ├── Cálculo de dias úteis (descarta fins de semana + feriados)
    ├── Conversão para horas
    └── Alocação por forca_trabalho
```

---

## 8. Feriados Nacionais (Tabela de Suporte)

| Tabela | Descrição |
|---|---|
| `feriados` | Feriados nacionais e municipais |

Campos: `data_feriado`, `feriado_movel`, `descricao`, `cidade_id`, `entidade_id`

---

## 9. Documentação e Rastreabilidade

| Tabela | Descrição |
|---|---|
| `documentos` | Documentos vinculados (requisições, entregas, etc.) |
| `comentarios` | Comentários em entregas, atividades, projetos |
| `audits` | Log de auditoria (quem fez o quê, quando) |

---

## 10. Contagem de Registros (Validação)

Snapshot do dump importado:

| Tabela | Total | Ativos (`deleted_at IS NULL`) |
|---|---|---|
| `planos_entregas_entregas` | ~14.7k | ~14.7k |
| `planos_trabalhos` | ~3.5k | ~3.5k |
| `planos_trabalhos_entregas` | ~15k+ | ~15k+ |
| `usuarios` | ~1.5k | ~1.5k |
| `unidades` | ~200+ | ~150+ |
| `planos_entregas` | ~100+ | ~50+ |

---

## 11. Relações Principais (ER Diagram em Texto)

```
usuarios
├── id (PK)
├── nome, email, cpf, matricula
├── situacao_funcional, situacao_siape
├── tipo_modalidade_id (FK → tipos_modalidades)
└── participa_pgd

unidades
├── id (PK)
├── sigla, nome, path (hierarquia)
├── unidade_pai_id (FK → unidades) [AUTORREFERÊNCIA]
└── entidade_id (FK → entidades)

planos_trabalhos
├── id (PK)
├── numero, status, carga_horaria
├── data_inicio, data_fim
├── usuario_id (FK → usuarios)
├── unidade_id (FK → unidades)
├── tipo_modalidade_id (FK → tipos_modalidades)
└── deleted_at

planos_trabalhos_entregas
├── id (PK)
├── plano_trabalho_id (FK → planos_trabalhos)
├── plano_entrega_entrega_id (FK → planos_entregas_entregas)
├── forca_trabalho (%), descricao
└── deleted_at

planos_entregas
├── id (PK)
├── numero, nome, status
├── data_inicio, data_fim
├── unidade_id (FK → unidades)
├── programa_id (FK → programas)
└── deleted_at

planos_entregas_entregas (CRÍTICA)
├── id (PK)
├── descricao, descricao_entrega
├── progresso_esperado, progresso_realizado ← METAS
├── data_inicio, data_fim, homologado
├── meta, realizado (JSON)
├── plano_entrega_id (FK → planos_entregas)
├── unidade_id (FK → unidades)
├── entrega_pai_id (FK → planos_entregas_entregas) [AUTORREFERÊNCIA]
└── deleted_at
```

---

## 12. Próximos Passos

1. **Implementar Indicadores I09, I10, I11** → Tabela `avaliacoes` + `tipos_avaliacoes_notas`
2. **Investigar campo I01** → Encontrar tabela com regimes de trabalho detalhados
3. **Validar feriados** → Atualizar lista de feriados móveis conforme necessário
