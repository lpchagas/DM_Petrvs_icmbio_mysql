# DM_Petrvs_icmbio_mysql

Exploração direta dos dados do PETRVS via MySQL local + DBeaver, sem Docker e sem datamart.

## O que este projeto faz

Disponibiliza consultas SQL e documentação para calcular os **indicadores OCDE/PGD do ICMBio** diretamente da base operacional do PETRVS, sem necessidade de ETL, PostgreSQL ou containers.

## Quando usar este projeto

- Validação da fonte original de dados
- Análise ad hoc e auditoria
- Ambiente sem Docker disponível
- Exploração antes de decidir usar o datamart completo

## Pré-requisitos

| Ferramenta | Versão mínima | Observação |
|---|---|---|
| MySQL Server | 8.0 | Necessário para window functions e CTEs recursivas |
| DBeaver Community | qualquer | Ferramenta de consulta gráfica |

Não é necessário Docker, PostgreSQL, Python ou Flask.

## Estrutura do projeto

```
docs/
  01-visao-geral.md                   Conceito e fluxo do projeto
  02-restauracao-dump-petrvs.md       Como restaurar o dump MySQL localmente
  03-acesso-direto-mysql-dbeaver.md   Como conectar no MySQL via DBeaver
  04-configuracao-dbeaver.md          Configuração do DBeaver
  05-contexto-ocde-pgd.md             Contexto estratégico dos indicadores OCDE/PGD
  06-indicadores-ocde-mysql.md        Consultas SQL dos indicadores (I02 a I08)
  07-estrutura-banco-dados.md         Arquitetura técnica completa do banco PETRVS (130+ tabelas)
  08-guia-rapido-gestores.md          Guia sem SQL para gestores — interpretar indicadores sem técnica
```

## Início rápido

**Para gestores (sem SQL):** leia [docs/08-guia-rapido-gestores.md](docs/08-guia-rapido-gestores.md) — entenda os indicadores e como interpretar os resultados sem precisar de banco de dados.

**Para analistas (setup técnico):**

1. Instale MySQL 8.0 e DBeaver Community no Windows
2. Restaure o dump seguindo [docs/02-restauracao-dump-petrvs.md](docs/02-restauracao-dump-petrvs.md)
3. Conecte no banco seguindo [docs/03-acesso-direto-mysql-dbeaver.md](docs/03-acesso-direto-mysql-dbeaver.md)
4. Execute as consultas de [docs/06-indicadores-ocde-mysql.md](docs/06-indicadores-ocde-mysql.md)

## Indicadores disponíveis

| Indicador | Descrição |
|---|---|
| I02 | Taxa de cumprimento das entregas (por unidade) |
| I03 | Taxa de cumprimento de metas por entrega (por entrega) |
| I04 | Índice de atingimento de metas (score médio por unidade) |
| I05 | Distribuição das entregas entre os servidores |
| I06 | Grau de responsabilidade pelas entregas |
| I07 | Horas por entrega — planejadas |
| I08 | Proporção de horas por entrega — planejadas |

## Projeto relacionado

O projeto [DM_Petrvs_icmbio_postgre](https://github.com/lpchagas/DM_Petrvs_icmbio_postgre) oferece o fluxo completo com ETL, datamart PostgreSQL e dashboards Superset.
