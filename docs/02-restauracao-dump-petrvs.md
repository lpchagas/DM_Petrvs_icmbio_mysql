# Restauracao do dump do PETRVS (MySQL local, sem Docker)

Este guia cobre a restauracao do dump do PETRVS em um MySQL Server instalado localmente no Windows, sem uso de containers.

## 1. Arquivo de dump esperado

O dump e um arquivo `.sql` gerado pelo MySQL do servidor do PETRVS. No ambiente ICMBio, o arquivo identificado foi:

- `C:\_dump\D.PGD.MGI.001.DUMP.20260226ICMBIO.sql`
- Formato: dump SQL MySQL
- Banco de origem: `petrvs_icmbio`
- Versao de origem: MySQL 8.0.32
- Tamanho: superior a 4 GB

Ajuste o caminho conforme o arquivo disponivel no seu ambiente.

## 2. Pre-requisitos

- MySQL Server 8.0 instalado no Windows
- Acesso ao usuario `root` do MySQL local

Confirme a instalacao:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --version
```

Se o comando nao for reconhecido, adicione o caminho ao PATH da sessao:

```powershell
$env:Path += ";C:\Program Files\MySQL\MySQL Server 8.0\bin"
mysql --version
```

## 3. Preparar as variaveis de ambiente para os comandos

```powershell
$mysqlExe = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
$dumpFile = "C:\_dump\D.PGD.MGI.001.DUMP.20260226ICMBIO.sql"
$dbName   = "petrvs_icmbio"
```

## 4. Criar o banco local

```powershell
& $mysqlExe -u root -p -e "CREATE DATABASE IF NOT EXISTS $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## 5. Tratar erro de DEFINER (se necessario)

Alguns dumps do PETRVS contem objetos com `DEFINER` apontando para usuario especifico de producao (ex: `pgd@10.190.136.185`). Isso causa erro:

```text
ERROR 1449 (HY000): The user specified as a definer does not exist
```

Se isso ocorrer, crie o usuario de compatibilidade antes de importar:

```powershell
& $mysqlExe -u root -p -e "CREATE USER IF NOT EXISTS 'pgd'@'10.190.136.185' IDENTIFIED BY 'Temp@1234'; GRANT ALL PRIVILEGES ON *.* TO 'pgd'@'10.190.136.185'; FLUSH PRIVILEGES;"
```

Depois recrie o banco limpo:

```powershell
& $mysqlExe -u root -p -e "DROP DATABASE IF EXISTS $dbName; CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## 6. Importar o dump

```powershell
& $mysqlExe -u root -p $dbName -e "source C:/_dump/D.PGD.MGI.001.DUMP.20260226ICMBIO.sql"
```

Dumps grandes (4 GB+) demoram varios minutos. Aguarde o termino sem interromper.

## 7. Validar a importacao

Confirme se as tabelas principais existem:

```powershell
& $mysqlExe -u root -p -D $dbName -e "SHOW TABLES LIKE '%entrega%';"
& $mysqlExe -u root -p -D $dbName -e "SELECT COUNT(*) AS total FROM planos_entregas_entregas WHERE deleted_at IS NULL;"
```

No ambiente validado, o total esperado em `planos_entregas_entregas` com registros ativos foi **14727**.

Validacao completa das tabelas necessarias:

```sql
show tables like 'unidades';
show tables like 'usuarios';
show tables like 'planos_entregas';
show tables like 'planos_entregas_entregas';
show tables like 'planos_trabalhos';
show tables like 'planos_trabalhos_entregas';
```

Contagens basicas:

```sql
select count(*) from unidades;
select count(*) from usuarios;
select count(*) from planos_entregas;
select count(*) from planos_entregas_entregas;
```

Se todas retornarem numeros maiores que zero, a restauracao esta completa.

## 8. Proximo passo

Com o banco restaurado, conecte no DBeaver seguindo [docs/03-acesso-direto-mysql-dbeaver.md](03-acesso-direto-mysql-dbeaver.md).

## 9. Erros comuns

### Charset incorreto

O dump usa `utf8mb4`. O MySQL 8.0 ja suporta isso por padrao — nao e necessario configuracao adicional.

### Processo muito lento

Arquivos acima de 4 GB demoram. Acompanhe o uso de disco no Gerenciador de Tarefas enquanto aguarda.

### Banco nao existe no inicio

O passo 4 cria o banco antes da importacao. Se o banco ja existir de uma tentativa anterior com erro, use o `DROP DATABASE` do passo 5 para recriar limpo.
