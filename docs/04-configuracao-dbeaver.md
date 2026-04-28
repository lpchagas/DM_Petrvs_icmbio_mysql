# Configuração do DBeaver para este projeto

Este documento cobre configuracoes uteis do DBeaver para trabalhar com o banco `petrvs_icmbio`.

## 1. Configuracoes recomendadas na conexao MySQL

Na tela de configuracao da conexao (`Edit Connection`):

### Aba Connection

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Port | `3306` |
| Database | `petrvs_icmbio` |
| User | `root` |
| Password | sua senha |

Marque **Save password locally** para nao precisar digitar toda vez.

### Aba Driver Properties

Se aparecer erro de autenticacao ou chave publica:

| Propriedade | Valor |
|---|---|
| `allowPublicKeyRetrieval` | `true` |
| `useSSL` | `false` |

## 2. Como abrir um SQL Editor

1. Clique com o botao direito na conexao `petrvs_icmbio`.
2. Clique em `SQL Editor`.
3. Clique em `New SQL Script`.

Ou use o atalho `Ctrl+]` com a conexao selecionada.

## 3. Como executar uma consulta

- Selecionar parte do SQL e apertar `Ctrl+Enter` para executar apenas a selecao.
- `Ctrl+Enter` sem selecao executa o bloco onde o cursor esta.
- `Ctrl+A` + `Ctrl+Enter` executa o script inteiro.

## 4. Como exportar resultado para planilha

Apos executar a consulta:

1. Clique com o botao direito no grid de resultados.
2. Clique em `Export Results`.
3. Escolha `CSV` ou `XLSX`.
4. Siga o assistente e escolha a pasta de destino.

## 5. Como salvar uma consulta como arquivo SQL

1. No editor SQL aberto, pressione `Ctrl+S`.
2. Escolha um nome e pasta.
3. O arquivo sera salvo como `.sql` e pode ser reaberto depois.

## 6. Como trabalhar com multiplas abas

O DBeaver permite abrir varias abas de SQL Editor ao mesmo tempo. Isso e util para:

- Executar a consulta de auditoria em uma aba e o indicador em outra.
- Comparar resultados lado a lado.

Use `Ctrl+]` repetidamente para abrir novas abas.

## 7. Limite de recursao para CTEs recursivas (I07 e I08)

Os indicadores I07 e I08 usam CTEs recursivas para gerar o calendario. Para periodos maiores que 1 ano, execute antes da consulta:

```sql
SET SESSION cte_max_recursion_depth = 5000;
```

Para 1 ano (365 dias), o limite padrao de 1000 ja e suficiente.

## 8. Configurar execucao automatica do SET SESSION

Se quiser que o limite de recursao seja configurado automaticamente ao conectar:

1. Va em `Edit Connection` > `Connection` > `Initialization`.
2. No campo `Initial SQL`, adicione:

```sql
SET SESSION cte_max_recursion_depth = 5000;
```

Isso executa o comando toda vez que o DBeaver abrir a conexao.

## 9. Vantagens do DBeaver para este projeto

- Trabalha com MySQL e PostgreSQL no mesmo programa (util se voce tambem usar o datamart).
- Exporta resultados para CSV/XLSX sem instalar nada adicional.
- Permite abrir e comparar varios scripts ao mesmo tempo.
- Visualiza estrutura das tabelas graficamente (diagrama ER).
