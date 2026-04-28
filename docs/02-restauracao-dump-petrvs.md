# Restauracao do dump do PETRVS (MySQL local, sem Docker)

Este guia cobre a restauracao do dump do PETRVS em um MySQL Server instalado localmente no Windows, sem uso de containers.

**Perfil:** analista ou tecnico com acesso ao arquivo de dump. Nao e necessario para gestores — veja [08-guia-rapido-gestores.md](08-guia-rapido-gestores.md).

---

## Resumo das etapas

| Etapa | O que fazer | Tempo estimado |
| --- | --- | --- |
| 1 | Verificar que MySQL 8.0 esta instalado | 1 min |
| 2 | Localizar o arquivo de dump | 1 min |
| 3 | Criar o banco de dados vazio | 2 min |
| 4 | (Se necessario) Tratar erro de DEFINER | 3 min |
| 5 | Importar o dump | 15-40 min |
| 6 | Validar a importacao | 5 min |

**Tempo total:** 25 a 50 minutos (a maior parte e aguardar a importacao).

---

## 1. Arquivo de dump esperado

O dump e um arquivo `.sql` gerado pelo MySQL do servidor do PETRVS. No ambiente ICMBio, o arquivo identificado foi:

- Caminho: `C:\_dump\D.PGD.MGI.001.DUMP.20260226ICMBIO.sql`
- Formato: dump SQL MySQL
- Banco de origem: `petrvs_icmbio`
- Versao de origem: MySQL 8.0.32
- Tamanho: superior a 4 GB

Ajuste o caminho conforme o arquivo disponivel no seu ambiente.

---

## 2. Pre-requisitos

- MySQL Server 8.0 instalado no Windows
- Acesso ao usuario `root` do MySQL local

Confirme a instalacao abrindo o **PowerShell** e executando:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --version
```

O resultado deve mostrar algo como `mysql  Ver 8.0.32 for Win64`. Se o comando nao for reconhecido, adicione o caminho ao PATH da sessao:

```powershell
$env:Path += ";C:\Program Files\MySQL\MySQL Server 8.0\bin"
mysql --version
```

---

## 3. Preparar as variaveis para os comandos

Abra o **PowerShell** e defina as variaveis abaixo. Assim voce evita repetir caminhos longos nos passos seguintes.

```powershell
$mysqlExe = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
$dumpFile = "C:\_dump\D.PGD.MGI.001.DUMP.20260226ICMBIO.sql"
$dbName   = "petrvs_icmbio"
```

Mantenha o PowerShell aberto — as variaveis precisam estar ativas para os proximos comandos.

---

## 4. Criar o banco local

```powershell
& $mysqlExe -u root -p -e "CREATE DATABASE IF NOT EXISTS $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

O MySQL vai pedir sua senha de root. Digite e pressione Enter. Se o banco ja existir de uma tentativa anterior com erro, use o comando do passo 5 para recriar limpo.

---

## 5. Tratar erro de DEFINER (se necessario)

Alguns dumps do PETRVS contem objetos com `DEFINER` apontando para usuario especifico de producao (ex: `pgd@10.190.136.185`). Isso causa o erro:

```text
ERROR 1449 (HY000): The user specified as a definer does not exist
```

**Se esse erro aparecer**, execute os dois blocos abaixo antes de tentar importar novamente:

**5a. Criar o usuario de compatibilidade:**

```powershell
& $mysqlExe -u root -p -e "CREATE USER IF NOT EXISTS 'pgd'@'10.190.136.185' IDENTIFIED BY 'Temp@1234'; GRANT ALL PRIVILEGES ON *.* TO 'pgd'@'10.190.136.185'; FLUSH PRIVILEGES;"
```

**5b. Recriar o banco limpo:**

```powershell
& $mysqlExe -u root -p -e "DROP DATABASE IF EXISTS $dbName; CREATE DATABASE $dbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

---

## 6. Importar o dump

```powershell
& $mysqlExe -u root -p $dbName -e "source C:/_dump/D.PGD.MGI.001.DUMP.20260226ICMBIO.sql"
```

Dumps grandes (4 GB+) demoram varios minutos. Aguarde o termino sem interromper o processo. Voce pode acompanhar o uso de disco no **Gerenciador de Tarefas** — enquanto o MySQL esta gravando, o disco vai aparecer em uso.

O processo termina quando o PowerShell exibe o prompt novamente (`PS C:\...>`).

---

## 7. Validar a importacao

Confirme que as tabelas principais existem e contem dados:

```powershell
& $mysqlExe -u root -p -D $dbName -e "SHOW TABLES LIKE '%entrega%';"
```

Deve mostrar pelo menos:

- `planos_entregas`
- `planos_entregas_entregas`

Contagem de registros ativos (o valor esperado no dump ICMBio e **14727**):

```powershell
& $mysqlExe -u root -p -D $dbName -e "SELECT COUNT(*) AS total FROM planos_entregas_entregas WHERE deleted_at IS NULL;"
```

Validacao completa das 6 tabelas necessarias para os indicadores (execute no DBeaver ou no PowerShell):

```sql
show tables like 'unidades';
show tables like 'usuarios';
show tables like 'planos_entregas';
show tables like 'planos_entregas_entregas';
show tables like 'planos_trabalhos';
show tables like 'planos_trabalhos_entregas';
```

Se todas retornarem o nome da tabela, a restauracao esta completa.

---

## Checklist final

Antes de passar para o proximo passo, confirme:

- [ ] MySQL 8.0 instalado e respondendo ao comando `--version`
- [ ] Banco `petrvs_icmbio` criado
- [ ] Importacao concluida sem erros fatais
- [ ] `planos_entregas_entregas` com ~14.727 registros ativos
- [ ] As 6 tabelas necessarias existem

---

## 8. Proximo passo

Com o banco restaurado, conecte no DBeaver seguindo [docs/03-acesso-direto-mysql-dbeaver.md](03-acesso-direto-mysql-dbeaver.md).

---

## Erros comuns

### Charset incorreto

O dump usa `utf8mb4`. O MySQL 8.0 ja suporta isso por padrao — nao e necessario configuracao adicional.

### Processo muito lento

Arquivos acima de 4 GB demoram. Acompanhe o uso de disco no Gerenciador de Tarefas enquanto aguarda.

### Banco nao existe no inicio

O passo 4 cria o banco antes da importacao. Se o banco ja existir de uma tentativa anterior com erro, use o `DROP DATABASE` do passo 5b para recriar limpo.

### Servico MySQL parado

Se o MySQL nao responder, verifique se o servico esta ativo: **Gerenciador de Tarefas > Servicos > MySQL80 > Iniciar**.
