# Guia de Extração Mensal dos Indicadores OCDE/PGD — ICMBio

Este guia descreve **quando e como** gerar os CSVs dos 12 indicadores OCDE/PGD
para alimentar o Painel Power BI do ICMBio — sem precisar entender programação.
Basta copiar os comandos e seguir os passos.

**Analogia para gestores:** os scripts funcionam como um relatório automático do
sistema. Você executa o comando, o script busca os dados no PETRVS via Denodo e
salva o resultado na pasta certa, já formatado para o Excel.

---

## 1. Periodicidade dos indicadores

Os indicadores se dividem em dois grupos com cadências diferentes a partir de 2026:

| Cadência | Instrumento base | Indicadores | Períodos gerados |
| --- | --- | --- | --- |
| **Mensal** | Plano de Trabalho (PT) | I01, I05, I06, I09, I10, I11 | M01-2026 … M12-2026 |
| **Quadrimestral** | Plano de Entrega (PE) | I02, I03, I04, I07, I08, I12 | Q1-2026, Q2-2026, Q3-2026 |

> **Histórico 2025 (trimestral):** todos os 12 indicadores também incluem os
> períodos T1-2025, T2-2025, T3-2025 e T4-2025 em cada execução — esses períodos
> estão encerrados e não mudam mais.

### Por que as cadências são diferentes?

Os Planos de Trabalho individuais passaram a ter ciclos mensais em 2026 (M01 a
M12), enquanto os Planos de Entrega das unidades continuam seguindo ciclos
quadrimestrais (Q1: jan–abr, Q2: mai–ago, Q3: set–dez). Cada indicador é
atualizado no ritmo do instrumento que usa como fonte principal.

A lógica de períodos está em `lib/periodos.py`:

- `build_periods_pe()` — usado por I02, I03, I04, I07, I08, I12
- `build_periods_pt()` — usado por I01, I05, I06, I09, I10, I11

---

## 2. Calendário anual 2026

Execute os scripts **logo após o fechamento do período** — quando o próximo
período já começou e o anterior está encerrado. Períodos em aberto
(`periodo_status = em_andamento`) geram resultados parciais e não devem ser
usados como base definitiva no Power BI.

| Mês de execução | Período encerrado | O que rodar | Scripts |
| --- | --- | --- | --- |
| Fevereiro | M01-2026 (jan) | PT mensais | I01, I05, I06, I09, I10, I11 |
| Março | M02-2026 (fev) | PT mensais | I01, I05, I06, I09, I10, I11 |
| Abril | M03-2026 (mar) | PT mensais | I01, I05, I06, I09, I10, I11 |
| **Maio** | M04-2026 (abr) + **Q1-2026** (jan–abr) | **PT mensais + PE quadrimestrais** | **I01–I12** |
| Junho | M05-2026 (mai) | PT mensais | I01, I05, I06, I09, I10, I11 |
| Julho | M06-2026 (jun) | PT mensais | I01, I05, I06, I09, I10, I11 |
| Agosto | M07-2026 (jul) | PT mensais | I01, I05, I06, I09, I10, I11 |
| **Setembro** | M08-2026 (ago) + **Q2-2026** (mai–ago) | **PT mensais + PE quadrimestrais** | **I01–I12** |
| Outubro | M09-2026 (set) | PT mensais | I01, I05, I06, I09, I10, I11 |
| Novembro | M10-2026 (out) | PT mensais | I01, I05, I06, I09, I10, I11 |
| Dezembro | M11-2026 (nov) | PT mensais | I01, I05, I06, I09, I10, I11 |
| **Janeiro 2027** | M12-2026 (dez) + **Q3-2026** (set–dez) | **PT mensais + PE quadrimestrais** | **I01–I12** |

> **Resumo prático:** rodar **todos os 12 indicadores juntos apenas três vezes
> no ano** (maio, setembro e janeiro), e só os 6 indicadores PT nos demais meses.
> Nos três meses de rodada completa, o CSV dos PE substituirá a versão anterior
> no Power BI com os dados do quadrimestre fechado.

---

## 3. CSVs esperados por execução

Referência de nomes de arquivo, volume de dados e tamanho aproximado
(valores do run de produção de 17/06/2026 — crescem mensalmente):

| # | Indicador | Arquivo CSV | Linhas | Tamanho |
|---|-----------|-------------|--------|---------|
| 1 | I01 — Regime de trabalho (resumo) | `IND_01.2_v1_proporcao_mensal_AAAAMMDD_HHMM.csv` | ~137 | ~8 KB |
| 2 | I01 — Regime de trabalho (por unidade) | `IND_01.2_v2_proporcao_unidade_mensal_AAAAMMDD_HHMM.csv` | ~10.367 | ~1 MB |
| 3 | I02 — Taxa de cumprimento das entregas | `IND_02.2_taxa_cumprimento_temporal_AAAAMMDD_HHMM.csv` | ~1.935 | ~345 KB |
| 4 | I03 — Taxa de cumprimento por entrega | `IND_03.2_taxa_cumprimento_temporal_AAAAMMDD_HHMM.csv` | ~16.219 | ~7 MB |
| 5 | I04 — Índice de atingimento de metas | `IND_04.2_score_atingimento_metas_AAAAMMDD_HHMM.csv` | ~1.935 | ~323 KB |
| 6 | I05 — Distribuição de entregas por servidor | `IND_05.2_distribuicao_entregas_servidores_AAAAMMDD_HHMM.csv` | ~9.546 | ~1,8 MB |
| 7 | I06 — Grau de responsabilidade por entrega | `IND_06.2_grau_responsabilidade_entregas_AAAAMMDD_HHMM.csv` | ~4.921 | ~643 KB |
| 8 | I07 — Horas por entrega (absoluto) | `IND_07.2_horas_por_entrega_AAAAMMDD_HHMM.csv` | ~25.307 | ~6,8 MB |
| 9 | I08 — Proporção de horas por entrega (%) | `IND_08.2_proporcao_horas_entrega_AAAAMMDD_HHMM.csv` | ~25.307 | ~5,6 MB |
| 10 | I09 — Média das avaliações do PT | `IND_09.2_media_avaliacao_pt_AAAAMMDD_HHMM.csv` | ~1.996 | ~273 KB |
| 11 | I10 — Percentual de avaliações inadequadas | `IND_10.2_perc_inadequado_pt_AAAAMMDD_HHMM.csv` | ~1.996 | ~263 KB |
| 12 | I11 — Percentual de avaliações excepcionais | `IND_11.2_perc_excepcional_pt_AAAAMMDD_HHMM.csv` | ~1.996 | ~265 KB |
| 13 | I12 — Coerência PT × PE | `IND_12.2_coerencia_pt_pe_AAAAMMDD_HHMM.csv` | ~1.295 | ~190 KB |

> Os números de linhas e tamanhos aumentam a cada mês à medida que novos dados
> são registrados no PETRVS.

---

## 4. Pré-requisitos

Verifique os itens abaixo **uma única vez** antes da primeira execução.
Nas rodadas seguintes, basta executar os scripts.

### Checklist de pré-requisitos

- [ ] **IP liberado pelo Dataprev** — sem isso, a conexão falha silenciosamente.
  Se você consegue acessar o PETRVS pelo DBeaver, o IP já está liberado.
- [ ] **DBeaver instalado** em `C:\Program Files\DBeaver\` — o Python usa o Java
  embutido no DBeaver.
- [ ] **Driver Denodo disponível** em
  `C:\Users\<seu_usuario>\AppData\Roaming\DBeaverData\drivers\remote\drivers\jdbc\9\denodo-vdp-jdbcdriver.jar`
  (o arquivo **com extensão `.jar`** — não apenas o `denodo-vdp-jdbcdriver` sem
  extensão). Ver seção de troubleshooting se necessário.
- [ ] **Arquivo `.env` configurado** — o arquivo `.env` na raiz do projeto deve
  existir com suas credenciais. Veja a seção abaixo.
- [ ] **Python instalado** — abra o PowerShell e execute `python --version`.
  Deve retornar `Python 3.x.x`.
- [ ] **jpype instalado** — execute `python -c "import jpype; print('OK')"`.
  Se retornar erro, execute `pip install jpype1`.

### Configuração do arquivo `.env`

O arquivo `.env` fica na raiz do projeto (`pgd-ocde-icmbio\.env`) e
contém as credenciais de acesso ao Denodo. Ele **nunca é publicado no repositório**
(está no `.gitignore`). Copie o `.env.example` como `.env` e preencha:

```
DENODO_USER=<seu_cpf_sem_pontos>
DENODO_PASSWORD=<sua_senha_denodo>
DENODO_DRIVER_PATH=C:/Users/<seu_usuario>/AppData/Roaming/DBeaverData/drivers/remote/drivers/jdbc/9/denodo-vdp-jdbcdriver.jar
DENODO_HOST=denodo-pgd.dataprev.gov.br
DENODO_PORT=443
DENODO_DATABASE=petrvs_icmbio
JAVA_HOME=C:/Program Files/DBeaver/jre
```

> **Atenção:** se sua senha do Denodo mudar, atualize `DENODO_PASSWORD`.
> Se outro usuário for executar em outra máquina, substitua `<seu_usuario>` pelo
> nome de usuário Windows correspondente.

---

## 5. Preparação antes de cada rodada

```powershell
# 1. Atualizar o repositório local
git pull

# 2. Verificar que o .env está configurado
Get-Content .env

# 3. Testar a conexão sem abrir o Denodo
python ocde/indicadores/IND_02.1_run.py --dry-run
```

O `--dry-run` mostra o instrumento (PE ou PT), o documento-fonte, a SQL adaptada
e o destino em `artefatos_local/` sem abrir conexão com o Denodo.

---

## 6. Execução dos scripts

### 6a. Executar todos os 12 indicadores de uma vez (recomendado)

Um único bloco PowerShell gera os 13 CSVs automaticamente, reporta o status de
cada indicador e lista os que tiveram erro ao final.

Abra o **PowerShell** (tecla Windows → "PowerShell" → Enter), cole o bloco abaixo
e pressione Enter. Aguarde de 5 a 15 minutos dependendo da conexão com o Dataprev:

```powershell
cd "C:\Projetos\pgd-ocde-icmbio"

$indicadores = @(
    @{script="IND_01.1_run.py"; nome="I01 - Regime de trabalho"},
    @{script="IND_02.1_run.py"; nome="I02 - Taxa cumprimento entregas"},
    @{script="IND_03.1_run.py"; nome="I03 - Taxa cumprimento por entrega"},
    @{script="IND_04.1_run.py"; nome="I04 - Índice atingimento metas"},
    @{script="IND_05.1_run.py"; nome="I05 - Distribuição entregas servidores"},
    @{script="IND_06.1_run.py"; nome="I06 - Grau responsabilidade"},
    @{script="IND_07.1_run.py"; nome="I07 - Horas por entrega (absoluto)"},
    @{script="IND_08.1_run.py"; nome="I08 - Proporção horas por entrega (%)"},
    @{script="IND_09.1_run.py"; nome="I09 - Média avaliações PT"},
    @{script="IND_10.1_run.py"; nome="I10 - % Avaliações inadequadas"},
    @{script="IND_11.1_run.py"; nome="I11 - % Avaliações excepcionais"},
    @{script="IND_12.1_run.py"; nome="I12 - Coerência PT x PE"}
)

$erros = @()
foreach ($ind in $indicadores) {
    Write-Host "`n>>> $($ind.nome)" -ForegroundColor Cyan
    python "ocde/indicadores/$($ind.script)"
    if ($LASTEXITCODE -ne 0) {
        $erros += $ind.nome
        Write-Host "  ERRO no $($ind.nome)" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Green
if ($erros.Count -eq 0) {
    Write-Host "CONCLUÍDO: todos os indicadores foram gerados com sucesso!" -ForegroundColor Green
} else {
    Write-Host "CONCLUÍDO COM ERROS nos seguintes indicadores:" -ForegroundColor Yellow
    $erros | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}
Write-Host "Arquivos salvos em: artefatos_local\ocde\entregas\$(Get-Date -Format 'yyyy-MM')" -ForegroundColor Green
```

Quando terminar, os CSVs estarão em:

```
artefatos_local\ocde\entregas\2026-06\
```

(a pasta muda automaticamente para o mês corrente — ex: `2026-07` em julho)

---

### 6b. Meses com só indicadores PT (9 meses no ano)

Execute os 6 indicadores baseados em Plano de Trabalho:

```powershell
python ocde/indicadores/IND_01.1_run.py
python ocde/indicadores/IND_05.1_run.py
python ocde/indicadores/IND_06.1_run.py
python ocde/indicadores/IND_09.1_run.py
python ocde/indicadores/IND_10.1_run.py
python ocde/indicadores/IND_11.1_run.py
```

### 6c. Meses com todos os indicadores — maio, setembro e janeiro (3 meses no ano)

Execute os 12 indicadores na ordem abaixo (PT primeiro, PE depois):

```powershell
# PT mensais
python ocde/indicadores/IND_01.1_run.py
python ocde/indicadores/IND_05.1_run.py
python ocde/indicadores/IND_06.1_run.py
python ocde/indicadores/IND_09.1_run.py
python ocde/indicadores/IND_10.1_run.py
python ocde/indicadores/IND_11.1_run.py

# PE quadrimestrais
python ocde/indicadores/IND_02.1_run.py
python ocde/indicadores/IND_03.1_run.py
python ocde/indicadores/IND_04.1_run.py
python ocde/indicadores/IND_07.1_run.py
python ocde/indicadores/IND_08.1_run.py
python ocde/indicadores/IND_12.1_run.py
```

Para forçar uma pasta de destino específica (útil para retroativos):

```powershell
python ocde/indicadores/IND_02.1_run.py --month 2026-05
```

### 6d. Executar um indicador específico

Use quando precisar gerar ou re-executar apenas um indicador. Primeiro navegue
até a raiz do projeto:

```powershell
cd "C:\Projetos\pgd-ocde-icmbio"
```

Depois execute o indicador desejado:

| Indicador | Comando | O que mostra |
|-----------|---------|-------------|
| **I01** | `python ocde/indicadores/IND_01.1_run.py` | Gera 2 arquivos: resumo nacional + detalhamento por unidade |
| **I02** | `python ocde/indicadores/IND_02.1_run.py` | % das entregas de cada unidade concluídas no período |
| **I03** | `python ocde/indicadores/IND_03.1_run.py` | Status de cada entrega individual (concluída / em andamento / não iniciada) |
| **I04** | `python ocde/indicadores/IND_04.1_run.py` | Score médio de atingimento das metas por unidade (0 a 100+) |
| **I05** | `python ocde/indicadores/IND_05.1_run.py` | Quantas entregas cada servidor está responsável por unidade |
| **I06** | `python ocde/indicadores/IND_06.1_run.py` | Quantos servidores compartilham cada entrega e com que % de força de trabalho |
| **I07** | `python ocde/indicadores/IND_07.1_run.py` | Total de horas planejadas para cada entrega em cada unidade |
| **I08** | `python ocde/indicadores/IND_08.1_run.py` | % da capacidade total da unidade alocado em cada entrega |
| **I09** | `python ocde/indicadores/IND_09.1_run.py` | Nota média (1 a 5) das avaliações dos servidores por unidade |
| **I10** | `python ocde/indicadores/IND_10.1_run.py` | % das avaliações com nota "Inadequado" por unidade |
| **I11** | `python ocde/indicadores/IND_11.1_run.py` | % das avaliações com nota "Excepcional" por unidade |
| **I12** | `python ocde/indicadores/IND_12.1_run.py` | Se a avaliação individual (PT) está alinhada com a avaliação coletiva (PE) da unidade |

Os CSVs são salvos em `artefatos_local/ocde/entregas/AAAA-MM/`.

---

## 7. Como abrir os CSVs no Excel

Os arquivos usam **pipe (`|`)** como separador em vez de vírgula ou ponto-e-vírgula.
Isso evita que descrições de entregas (que frequentemente contêm `;`) corrompam
o arquivo.

### Passos para abrir corretamente

1. Abra o Excel.
2. Menu **Dados** → **Obter Dados** → **De Arquivo** → **De Texto/CSV**.
3. Navegue até `artefatos_local\ocde\entregas\AAAA-MM\`.
4. Selecione o arquivo desejado.
5. Na janela de importação, altere o **Delimitador** para **Personalizado** e
   digite `|` (pipe).
6. Clique em **Carregar**.

> **Dica:** se você importar uma vez e salvar como `.xlsx`, não precisa repetir
> o processo. Para ter os dados mais recentes, reimporte o CSV atualizado.

---

## 8. Fluxo após extração

### Rotina mensal recomendada

```
Primeiro dia útil do mês:
  1. Executar todos os 12 scripts (seção 6a)
  2. Confirmar que todos os 13 CSVs foram gerados
  3. Abrir os CSVs no Excel para verificação visual rápida
  4. Enviar à COCAGE/Power BI conforme protocolo vigente

Até o dia 5 do mês:
  5. Revisar e encaminhar os arquivos de entrega
```

### Calendário de execução

| Quando | O que fazer |
|--------|-------------|
| **Primeiro dia útil do mês** | Executar todos os 12 scripts (seção 6a) |
| **Até o dia 5 do mês** | Revisar os CSVs e enviar à COCAGE |
| **A qualquer momento** | Executar um indicador específico após correção ou solicitação pontual |
| **Antes de qualquer commit** | Executar o checklist `docs/12-seguranca-publicacao.md` |

---

## 9. Organização dos arquivos

Arquivos públicos do repositório:

```text
docs/                         documentação pública
ocde/indicadores/          executores IND_XX.1_run.py
lib/                  funções comuns sem credenciais
```

Arquivos locais, **nunca versionados** (caminhos gerenciados por `lib/csv_utils.py`):

```text
artefatos_local/
  ocde/
    entregas/
      AAAA-MM/            CSVs de indicadores prontos para envio à COCAGE/Power BI
                          IND_XX.2_<nome>_AAAAMMDD_HHMM.csv (todos os 12 indicadores)
    diagnosticos/
      AAAA-MM/            CSVs diagnósticos A4 (uso interno — não enviar)
                          IND_XX.4_qN_<descricao>.csv
      IND_XX.4_diagnostico_DD.MM.AAAA.py
  validacao/              Relatórios A5 e PDFs A3
                          IND_XX.5_relatorio_validacao_DD.MM.AAAA.md
                          IND_XX.3_PETRVS_consulta_DD.MM.AAAA.pdf
  docs_internos/          Protocolo de validação e docs não publicáveis
  backup_scripts_a1/      Cópias locais dos scripts A1 (backup jun 2026)
  historico/              Artefatos legados (dump e validação inicial mai/2026)
```

Os caminhos são gerenciados por `lib/csv_utils.py`:

- `indicator_csv_dir()` → `artefatos_local/ocde/entregas/AAAA-MM/`
- `diagnostic_csv_dir()` → `artefatos_local/ocde/diagnosticos/AAAA-MM/`

---

## 10. Importação no Power BI

Os CSVs gerados usam **pipe (`|`) como delimitador** e **UTF-8 com BOM** como
codificação — configure assim ao importar:

- **Delimitador:** pipe `|`
- **Codificação:** UTF-8 (a opção "UTF-8 com BOM" resolve automaticamente
  problemas com acentos)
- **Primeira linha como cabeçalho:** sim
- **Tipos de dado:** deixar o Power BI inferir; ajustar manualmente colunas de
  percentual (`DECIMAL`) e de data (`DATE`)

Para manter o painel sempre atualizado:

1. Gere os CSVs conforme o calendário da seção 2
2. Substitua os arquivos anteriores na pasta de destino do Power BI
3. Clique em "Atualizar" no Power BI Desktop

> **Atenção:** os CSVs têm nomes com timestamp
> (`IND_02.2_taxa_cumprimento_temporal_20260614_2050.csv`). Configure o Power BI
> para apontar para a **pasta** e não para um arquivo específico, usando a função
> `Folder.Files` — assim uma nova execução não quebra o relatório.

---

## 11. Auditoria dos CSVs

Cada script executa uma auditoria estrutural básica ao final:

- quantidade de linhas de dados
- quantidade de colunas
- consistência da largura das linhas no CSV

Antes de importar para o Power BI, verifique no terminal se a auditoria não
apontou `ALERTA`. Se apontar, rode `/p3b-auditar` para investigar antes de
compartilhar os resultados.

---

## 12. Solução de problemas frequentes

### Erro: "Configure DENODO_USER, DENODO_PASSWORD..."

**Causa:** o arquivo `.env` não existe ou ainda tem os placeholders padrão.

**Solução:** abra `.env` com o Bloco de Notas e preencha as credenciais conforme
a seção 4.

---

### Erro: "JVM não iniciada" ou "No module named 'jpype'"

**Causa:** o jpype não está instalado no ambiente Python atual.

**Solução:**

```powershell
pip install jpype1
```

Se o erro persistir, verifique se `JAVA_HOME` no `.env` aponta para o diretório
correto do DBeaver (`C:/Program Files/DBeaver/jre`).

---

### Erro: "Connection refused" ou timeout sem mensagem

**Causa:** IP não liberado pelo Dataprev, ou VPN corporativa bloqueando.

**Solução:**

1. Teste a conexão no DBeaver — se o DBeaver conectar, o script também conecta.
2. Se o DBeaver também falhar: solicitar liberação de IP ao responsável pelo
   acesso Denodo no ICMBio.
3. Em home office: verificar se a VPN do ICMBio está ativa.

---

### Erro: arquivo `.jar` não encontrado

**Causa:** o DBeaver atualizou o driver Denodo e o arquivo `.jar` foi substituído.

**Solução:** execute no PowerShell (substituindo `<seu_usuario>` pelo seu usuário
Windows):

```powershell
$dir = "C:\Users\<seu_usuario>\AppData\Roaming\DBeaverData\drivers\remote\drivers\jdbc\9"
Copy-Item "$dir\denodo-vdp-jdbcdriver" "$dir\denodo-vdp-jdbcdriver.jar" -Force
Write-Host "Driver copiado com sucesso."
```

---

### Um indicador gerou 0 linhas

**Causa mais comum:** período futuro (ex: Q3-2026 ainda sem dados suficientes
no PETRVS), ou filtro temporal sem correspondência nos dados.

**Como verificar:**

```powershell
python ocde/indicadores/IND_XX.1_run.py --dry-run
```

Isso mostra o que seria executado sem conectar ao Denodo.

---

### O CSV está corrompido no Excel (tudo em uma coluna)

**Causa:** o Excel tentou abrir com delimitador errado.

**Solução:** siga os passos da seção 7, garantindo que o delimitador seja `|` (pipe).

---

## 13. Resultados dos testes em produção (17/06/2026)

Todos os 12 indicadores foram testados com conexão real ao Denodo antes da
publicação deste guia:

| Indicador | Períodos executados | Total de linhas geradas | Status |
|-----------|---------------------|------------------------|--------|
| I01 | Mensal (inferido dos planos) | 137 (v1) + 10.367 (v2) | ✅ OK |
| I02 | T1-T4/2025 + Q1-Q2/2026 | 1.935 linhas | ✅ OK |
| I03 | T1-T4/2025 + Q1-Q2/2026 | 16.219 linhas | ✅ OK |
| I04 | T1-T4/2025 + Q1-Q2/2026 | 1.935 linhas | ✅ OK |
| I05 | T1-T4/2025 + Q1-Q2/2026 | 9.546 linhas | ✅ OK |
| I06 | T1-T4/2025 + Q1-Q2/2026 | 4.921 linhas | ✅ OK |
| I07 | T1-T4/2025 + Q1-Q2/2026 | 25.307 linhas | ✅ OK |
| I08 | T1-T4/2025 + Q1-Q2/2026 | 25.307 linhas | ✅ OK |
| I09 | T1-T4/2025 + Q1-Q2/2026 | 1.996 linhas | ✅ OK |
| I10 | T1-T4/2025 + Q1-Q2/2026 | 1.996 linhas | ✅ OK |
| I11 | T1-T4/2025 + Q1-Q2/2026 | 1.996 linhas | ✅ OK |
| I12 | T1-T4/2025 + Q1-Q2/2026 | 1.295 linhas | ✅ OK |

---

## 14. Prompts para ferramentas de IA

Prompts prontos para as principais ferramentas de IA disponíveis no projeto.
Adapte substituindo `XX` pelo número do indicador e `ERRO` pela mensagem real.

### Claude Code (recomendado — tem acesso ao contexto completo do projeto)

**Executar a extração mensal completa:**
```
Execute a extração mensal completa dos 12 indicadores OCDE. Rode todos os scripts em
ocde/indicadores/ em sequência, registre os resultados (linhas geradas por período e
por indicador) e me informe quais funcionaram e quais falharam. Se houver erros, diagnostique
a causa com base no CLAUDE.md e nos logs.
```

**Diagnosticar um erro específico:**
```
O script IND_XX.1_run.py falhou com o seguinte erro:
[cole aqui a mensagem de erro completa]

Com base no projeto pgd-ocde-icmbio e no CLAUDE.md, identifique a causa e proponha
a correção. Leve em conta que o banco é acessado via Denodo VQL (não MySQL), que funções
MySQL como json_unquote(), date_add() e WITH RECURSIVE não funcionam, e que os nomes de
tabela precisam do prefixo petrvs_icmbio_ no JDBC.
```

**Verificar se um CSV foi gerado corretamente:**
```
Analise o arquivo artefatos_local/ocde/entregas/AAAA-MM/IND_XX.2_*.csv e verifique:
1. Quantas linhas foram geradas por período (T1-2025 a Q2-2026)?
2. Há linhas com campos vazios no campo unidade_sigla?
3. Os valores numéricos estão dentro dos intervalos esperados (percentuais entre 0 e 100)?
4. Compare com os resultados esperados na seção 11 do CLAUDE.md.
```

**Gerar relatório de qualidade dos dados:**
```
Leia todos os CSVs gerados em artefatos_local/ocde/entregas/AAAA-MM/ e produza um relatório
resumido de qualidade com: total de linhas por indicador, períodos que retornaram 0 linhas,
unidades que aparecem em todos os indicadores e unidades com dados ausentes em algum indicador.
```

**Atualizar a documentação de um indicador:**
```
O indicador IXX teve sua lógica ajustada conforme a validação registrada no CLAUDE.md seção 11.
Execute o /atualizar-docs para atualizar a ficha docs/06.X.X-iXX.md refletindo o estado atual
do script e do último relatório de validação.
```

### GitHub Copilot (Chat / Inline — útil para código dentro do editor)

**Explicar um erro no terminal:**
```
@terminal Esse é o erro do script Python que executa o indicador IXX do projeto PETRVS:
[cole o erro]
Explique o que significa e sugira como corrigir considerando que o banco é Denodo VQL
(não MySQL) e não suporta json_unquote() nem WITH RECURSIVE.
```

**Gerar um script de verificação rápida:**
```
@workspace Baseando-se nos scripts em ocde/indicadores/ e em lib/, crie um script
Python chamado verificar_csvs.py que: (1) liste todos os CSVs em artefatos_local/ocde/entregas/[mês
atual]/; (2) para cada CSV, mostre nome, número de linhas e colunas; (3) alerte se algum CSV
tiver 0 linhas. Use delimitador pipe (|) e encoding utf-8-sig.
```

### Gemini / ChatGPT — análise de dados e geração de relatórios

**Interpretar resultados de um indicador:**
```
Tenho um CSV com resultados do Indicador I09 (Média das Avaliações do Plano de Trabalho
por Unidade) do ICMBio. A escala de notas é: 1=Não executado, 2=Inadequado, 3=Adequado,
4=Alto desempenho, 5=Excepcional. Com base nas linhas abaixo, identifique as 5 unidades
com melhor e pior desempenho e proponha uma narrativa para apresentar à liderança do ICMBio:
[cole aqui 20–30 linhas do CSV]
```

**Adaptar uma query MySQL para Denodo VQL:**
```
Adapte a query MySQL abaixo para Denodo VQL. Regras obrigatórias:
- Substituir DATE(campo) por CAST(campo AS DATE)
- Substituir JSON_UNQUOTE(campo) pelo campo diretamente
- Substituir WITH RECURSIVE por aritmética de datas: (data_fim - data_inicio) + 1
- Adicionar prefixo petrvs_icmbio_ em todos os nomes de tabela

Query MySQL original:
[cole a query aqui]
```

---

## 15. Validação manual pela CGOV

Quando houver validação pela equipe CGOV:

- salve PDFs de consulta PETRVS em `artefatos_local/validacao/`
- copie `ocde/diagnosticos/IND_XX.4_diagnostico_template.py` para
  `artefatos_local/ocde/diagnosticos/` e preencha as queries locais
- salve CSVs diagnósticos em `artefatos_local/ocde/diagnosticos/AAAA-MM/`
- salve relatórios internos em `artefatos_local/validacao/`

Esses arquivos podem conter dados operacionais e não devem ser publicados.

---

## 16. Antes de publicar alterações no repositório

Execute a checklist de `docs/12-seguranca-publicacao.md`. Se qualquer busca
apontar CPF, senha, CSV, PDF, relatório interno ou script local com credencial,
interrompa a publicação e corrija antes do commit.

---

## 17. Notas técnicas

### Periodicidade dos instrumentos (regra ICMBio vigente desde 2026)

| Instrumento | 2025 | 2026 |
|-------------|------|------|
| Plano de Entregas (PE) | Trimestral (T1–T4) | Quadrimestral (Q1–Q3) |
| Plano de Trabalho (PT) | Trimestral (T1–T4) | **Mensal (M01–M12)** |

- Scripts de I02, I03, I04, I07, I08, I12 (baseados em PE): `build_periods_pe()` → ciclos quadrimestrais em 2026
- Scripts de I01, I05, I06, I09, I10, I11 (baseados em PT): `build_periods_pt()` → ciclos mensais em 2026

### Correções aplicadas em 17/06/2026

Dois problemas foram corrigidos durante a preparação para produção:

1. **I08 — CTE recursiva incompatível com Denodo:** o script usava `WITH RECURSIVE`
   e funções MySQL (`date_add`, `dayofweek`, `concat`) para gerar calendário de dias
   úteis. Denodo VQL não suporta CTEs recursivas. Reescrito com aritmética de datas
   proporcional, mesma abordagem do I07.

2. **I09/I10/I11/I12 — `json_unquote()` inexistente no Denodo:** as queries usavam
   `JSON_UNQUOTE(tan.nota)`. Removido automaticamente na camada de adaptação
   (`adapt_for_jdbc` em `lib/docs_sql.py`), mantendo o
   `TRIM(BOTH '"' FROM ...)` externo que já faz a remoção de aspas quando necessário.
