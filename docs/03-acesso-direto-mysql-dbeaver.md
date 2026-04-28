# Acesso Direto ao MySQL via DBeaver

Este guia cobre a conexao no banco `petrvs_icmbio` (MySQL local) pelo DBeaver e as primeiras consultas de validacao.

**Perfil:** analista ou tecnico que vai executar as consultas SQL. Se voce e gestor buscando interpretar os resultados sem SQL, consulte [08-guia-rapido-gestores.md](08-guia-rapido-gestores.md).

## 1. Pre-requisito

O dump deve estar restaurado no MySQL local. Se ainda nao restaurou, siga [docs/02-restauracao-dump-petrvs.md](02-restauracao-dump-petrvs.md) primeiro.

## 2. Instalar o DBeaver

1. Baixe o instalador do **DBeaver Community** (versao gratuita).
2. Instale normalmente no Windows.
3. Abra o programa.

Se o DBeaver pedir para baixar o driver do MySQL na primeira conexao, aceite. E um download automatico e seguro.

## 3. Criar a conexao no DBeaver

1. Clique em `New Database Connection` (icone de tomada no topo esquerdo).
2. Escolha `MySQL`.
3. Preencha os campos:

   | Campo | Valor |
   | --- | --- |
   | Host | `localhost` |
   | Port | `3306` |
   | Database | `petrvs_icmbio` |
   | User | `root` |
   | Password | sua senha do MySQL local |

4. Clique em `Test Connection`.
5. Se aparecer sucesso, clique em `Finish`.

## 4. Primeira consulta de validacao

Abra um SQL Editor (botao direito na conexao > `SQL Editor` > `New SQL Script`) e execute:

```sql
show tables;
```

Voce deve ver a lista de tabelas do PETRVS, incluindo `planos_entregas_entregas`, `planos_trabalhos`, `unidades`, entre outras.

## 5. Consultas de validacao dos dados

Confirme que os dados estao presentes:

```sql
select count(*) as total_entregas_ativas
from planos_entregas_entregas
where deleted_at is null;
```

```sql
select count(*) as total_unidades
from unidades
where deleted_at is null;
```

## 6. Consulta de exploração inicial das entregas

```sql
select
  id,
  descricao,
  descricao_entrega,
  coalesce(nullif(trim(descricao), ''), nullif(trim(descricao_entrega), '')) as nome_entrega
from planos_entregas_entregas
limit 200;
```

## 7. Consulta com vinculo a unidade

```sql
select
    pee.id,
    u.sigla as unidade_sigla,
    u.nome  as unidade_nome,
    coalesce(nullif(trim(pee.descricao), ''), nullif(trim(pee.descricao_entrega), '')) as nome_entrega,
    case
        when pee.deleted_at is null then 'ATIVO'
        else 'EXCLUIDO'
    end as status_registro
from planos_entregas_entregas pee
left join unidades u on u.id = pee.unidade_id
order by u.sigla, pee.id;
```

## 8. Proximo passo

Com o ambiente validado, execute os indicadores OCDE/PGD seguindo [docs/06-indicadores-ocde-mysql.md](06-indicadores-ocde-mysql.md).

## 9. Problemas comuns

### O DBeaver nao conecta em localhost:3306

- Verifique se o servico `MySQL80` esta ativo no Windows (Servicos > MySQL80 > Iniciar).
- Verifique se a porta 3306 nao esta bloqueada por firewall.

### O DBeaver pede para baixar driver

Isso e normal. Aceite o download.

### O banco abre, mas nao aparecem tabelas

Verifique se o banco correto esta selecionado: o nome deve ser `petrvs_icmbio` (nao `mysql`, `sys` etc.).

### Erro de autenticacao

O MySQL 8.0 usa `caching_sha2_password` por padrao. Se o DBeaver reclamar de plugin de autenticacao, va em `Connection > Driver properties` e defina `allowPublicKeyRetrieval=true`.
