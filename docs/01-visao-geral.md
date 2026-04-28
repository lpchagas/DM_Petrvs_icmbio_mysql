# Visao geral do projeto

## 1. O que e o DM_Petrvs_icmbio_mysql

Este projeto oferece consultas SQL e documentacao para analisar o **Programa de Gestao e Desempenho (PGD)** do ICMBio diretamente da base operacional do PETRVS, sem necessidade de datamart, Docker ou transformacoes intermediarias.

O foco e simplicidade: instalar MySQL local, restaurar o dump, abrir o DBeaver e executar as consultas.

## 2. Quando usar este caminho

| Situacao | Recomendacao |
|---|---|
| Validar a origem dos dados | Este projeto |
| Auditoria ou investigacao pontual | Este projeto |
| Ambiente sem Docker | Este projeto |
| Dashboards recorrentes e automatizados | DM_Petrvs_icmbio_postgre |
| ETL completo com dimensoes e fatos | DM_Petrvs_icmbio_postgre |

## 3. Fluxo de funcionamento

```
Dump PETRVS (.sql)
       |
       v
MySQL Server 8.0 local
       |
       v
DBeaver (consultas SQL diretas)
       |
       v
Resultado / exportacao para planilha
```

Nao ha carga de dados intermediaria. Voce consulta as tabelas originais do PETRVS diretamente.

## 4. Tabelas do PETRVS utilizadas pelas consultas

- `unidades`
- `usuarios`
- `planos_entregas`
- `planos_entregas_entregas`
- `planos_trabalhos`
- `planos_trabalhos_entregas`

## 5. Diferenca em relacao ao projeto datamart

| Aspecto | Este projeto (mysql) | Projeto datamart (postgre) |
|---|---|---|
| Banco de dados | MySQL local | PostgreSQL (container) |
| Docker | Nao necessario | Necessario |
| Transformacao de dados | Nenhuma | ETL stage -> dim -> fato |
| Dashboards Superset | Nao | Sim |
| Complexidade de setup | Baixa | Media/alta |
| Fidelidade a origem | Maxima | Media (dados transformados) |

## 6. Requisito tecnico importante

Os indicadores I05, I06, I07 e I08 usam **window functions** e **CTEs recursivas**, que exigem **MySQL 8.0 ou superior**.

Se o seu ambiente usar versao anterior, verifique:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --version
```
