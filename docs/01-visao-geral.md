# Visao Geral do Projeto

## Para quem e este documento

Este documento e para **qualquer perfil** — gestores, analistas ou equipe tecnica. Se voce e gestor e quer entender os indicadores sem SQL, comece pelo [08-guia-rapido-gestores.md](08-guia-rapido-gestores.md).

---

## 1. O que e o DM_Petrvs_icmbio_mysql

Este projeto e um conjunto de **consultas SQL e documentacao** para calcular os **indicadores OCDE/PGD do ICMBio** diretamente dos dados originais do PETRVS, sem nenhuma transformacao intermediaria.

**Em linguagem simples:** imagine que o PETRVS e um grande arquivo de tabelas de dados. Este projeto e o conjunto de formulas e instrucoes para extrair as metricas que voce precisa dessas tabelas, sem criar copias ou versoes modificadas dos dados.

---

## 2. Quando usar este caminho

| Situacao | Recomendacao |
| --- | --- |
| Validar a origem dos dados | Este projeto |
| Auditoria ou investigacao pontual | Este projeto |
| Ambiente sem Docker | Este projeto |
| Dashboards recorrentes e automatizados | DM_Petrvs_icmbio_postgre |
| ETL completo com dimensoes e fatos | DM_Petrvs_icmbio_postgre |

---

## 3. Fluxo de funcionamento

```text
Dump PETRVS (.sql)
       |
       v
MySQL Server 8.0 local (banco de dados instalado no Windows)
       |
       v
DBeaver (ferramenta de consulta — interface grafica)
       |
       v
Resultado exportavel para Excel ou CSV
```

Nao ha transformacao de dados. As consultas leem diretamente as tabelas originais do PETRVS.

---

## 4. Como o PETRVS organiza os dados — analogia para entender

O PETRVS trabalha com dois tipos de planos. Entender a diferenca e essencial para interpretar os indicadores.

### Plano de Entregas (nivel da unidade)

E o contrato de resultados da **unidade**. A CGOV, por exemplo, define no inicio do semestre quais entregas vai produzir e qual e a meta numerica de cada uma.

No banco de dados, isso fica em duas tabelas:

- `planos_entregas`: o "cabecalho" do plano (periodo, unidade, status)
- `planos_entregas_entregas`: cada entrega individual (meta planejada, meta executada)

### Plano de Trabalho (nivel do servidor)

E a agenda individual de cada servidor. O servidor declara em quais entregas da unidade vai trabalhar e qual percentual da sua carga horaria vai dedicar a cada uma.

No banco de dados, isso fica em:

- `planos_trabalhos`: o plano do servidor (quem, qual unidade, periodo)
- `planos_trabalhos_entregas`: o vinculo entre o plano do servidor e cada entrega (com o percentual de dedicacao, campo `forca_trabalho`)

**A pergunta que os indicadores respondem:** as metas foram atingidas? O esforco foi distribuido de forma equilibrada entre as entregas e os servidores?

---

## 5. Tabelas do PETRVS utilizadas pelas consultas

| Tabela | Papel nos indicadores |
| --- | --- |
| `planos_entregas_entregas` | Metas planejadas e executadas (I02, I03, I04) |
| `planos_trabalhos_entregas` | Vinculo servidor × entrega + percentual dedicacao (I05, I06, I07, I08) |
| `planos_trabalhos` | Plano de trabalho do servidor (I05 a I08) |
| `planos_entregas` | Contexto do ciclo de planejamento (I07, I08) |
| `unidades` | Sigla e nome da unidade (todos os indicadores) |
| `usuarios` | Nome do servidor (I05, I06) |

---

## 6. Diferenca em relacao ao projeto datamart

| Aspecto | Este projeto (mysql) | Projeto datamart (postgre) |
| --- | --- | --- |
| Banco de dados | MySQL local | PostgreSQL (container) |
| Docker | Nao necessario | Necessario |
| Transformacao de dados | Nenhuma | ETL stage -> dim -> fato |
| Dashboards Superset | Nao | Sim |
| Complexidade de setup | Baixa | Media/alta |
| Fidelidade a origem | Maxima | Media (dados transformados) |

---

## 7. Requisito tecnico

Os indicadores I05, I06, I07 e I08 usam **window functions** (`RANK()`, `AVG() OVER`) e **CTEs recursivas** (`WITH RECURSIVE`), que exigem **MySQL 8.0 ou superior**.

Confirme a versao instalada antes de continuar:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --version
```

O resultado deve mostrar `8.0.x`. Versoes anteriores nao suportam esses recursos e retornarao erro ao executar os indicadores I05 a I08.
