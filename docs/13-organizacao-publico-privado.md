# Organização público-privado do projeto pgd-ocde-icmbio

> **Para quem é este documento:** qualquer pessoa que trabalhe neste projeto — analista, gestor ou técnico — independentemente do nível de familiaridade com Git ou linha de comando.

---

## 1. Por que separar o que é público do que é privado?

Este projeto lida com dados do PETRVS que incluem informações funcionais de servidores públicos. Ao mesmo tempo, a metodologia dos indicadores é um bem público que beneficia todos os órgãos da APF que usam o sistema.

A separação garante que:
- **A metodologia e os scripts** sejam compartilháveis com outros órgãos — ficam no GitHub
- **Suas credenciais de acesso** (CPF e senha do Denodo) jamais apareçam online
- **Os dados extraídos** (CSVs com nomes de unidades e servidores) fiquem fora do repositório
- **As análises internas da CGOV** (ad-hoc, contexto institucional específico) fiquem restritas ao OneDrive
- **O contexto dos assistentes de IA** (CLAUDE.md, AGENTS.md etc.) — que contém credenciais e caminhos locais — não seja publicado

---

## 2. O que fica onde

### Repositório público (GitHub — `pgd-ocde-icmbio`)

Tudo aqui é **versionado e publicável**. Não contém dados pessoais, senhas nem análises internas.

```
C:\Projetos\pgd-ocde-icmbio\
├── docs/                         Documentação técnica e de negócio
│   ├── 01–13 *.md                Documentos compartilhados do projeto
│   ├── ocde/                     Fichas técnicas dos 12 indicadores OCDE (I01–I12)
│   ├── mgi/                      Documentação MGI (em construção)
│   └── cgov/                     Placeholder público (sem análises — apenas README)
├── lib/                          Módulos Python compartilhados
│   ├── denodo_config.py          Leitura do .env e conexão JDBC
│   ├── periodos.py               build_periods_pe() e build_periods_pt()
│   ├── csv_utils.py              clean(), delimitador pipe
│   ├── auditoria.py              Avisos de qualidade de dados
│   ├── monthly_runner.py         Loop mensal para execução em lote
│   └── docs_sql.py               Extração da SQL canônica dos docs
├── ocde/                         Iniciativa OCDE/PGD ICMBio
│   ├── indicadores/              Scripts IND_XX.1_run.py sanitizados (I01–I12)
│   ├── relatorios/               Módulos de análise e relatório gerencial
│   └── diagnosticos/             Template público de diagnóstico (IND_XX.4_template)
├── mgi/                          Placeholder — indicadores MGI (em construção)
│   └── indicadores/
├── .env.example                  Modelo do .env — sem senhas reais
├── consultas_denodo_template.ipynb  Notebook público sem credenciais
└── README.md
```

### Pasta privada (OneDrive — `pgd-ocde-icmbio-privado`)

Tudo aqui é **local e sincronizado via nuvem**. Nunca vai para o GitHub.

```
C:\Users\<SEU_USUARIO>\OneDrive - ICMBio\projetos\pgd-ocde-icmbio-privado\
├── artefatos_local/
│   ├── ocde/
│   │   ├── entregas/YYYY-MM/     CSVs mensais para entrega à COCAGE/Power BI
│   │   └── diagnosticos/YYYY-MM/ Scripts A4 e CSVs de diagnóstico interno
│   ├── validacao/                Relatórios A5 e PDFs de consulta A3
│   ├── docs_internos/            Documentação local não publicável
│   ├── historico/                Artefatos de fases anteriores
│   └── backup_scripts_a1/        Cópias de segurança dos scripts A1
├── cgov/                         Análises internas CGOV (privadas)
│   └── analises/
│       └── objetivos_processos/  I03 enriquecido com objetivos e cadeia de valor
├── setup/                        Scripts de configuração de ambiente local
│   ├── configurar_env.ps1        Gera .env com caminhos desta máquina
│   └── criar_links_privados.ps1  Recria as pontes em um novo computador
└── assistentes/
    ├── CLAUDE.md                 Contexto e instruções para o Claude Code
    ├── AGENTS.md                 Contexto para o Codex/OpenAI
    ├── PROJECT.md                Contexto para o Antigravity Desktop
    ├── .claude/                  Configurações locais do Claude Code
    ├── .codex/                   Configurações locais do Codex
    └── .agents/                  Configurações locais do Antigravity
```

### O que fica apenas local (nem GitHub, nem OneDrive)

| Arquivo | Por que não vai a lugar nenhum |
|---------|-------------------------------|
| `.env` | Contém sua senha em texto puro — **nunca** sincronizar na nuvem |

> **Recomendação de segurança:** armazene sua senha do Denodo em um gerenciador de senhas (Bitwarden, KeePass, 1Password). Assim, mesmo que precise reconfigurar o `.env`, a senha está disponível com segurança.

---

## 3. Como o VS Code "enxerga" tudo junto

Na pasta do projeto você verá as pastas `artefatos_local`, `cgov`, `setup`, `.claude`, `.codex` e `.agents` como se estivessem ali, e os arquivos `CLAUDE.md`, `AGENTS.md` e `PROJECT.md` também. Mas eles são **pontes** (Junctions e HardLinks do Windows) que apontam para o OneDrive.

```
C:\Projetos\pgd-ocde-icmbio\
├── artefatos_local  →→→ [ponte] →→→ OneDrive\...\artefatos_local
├── cgov             →→→ [ponte] →→→ OneDrive\...\cgov
├── setup            →→→ [ponte] →→→ OneDrive\...\setup
├── .claude          →→→ [ponte] →→→ OneDrive\...\assistentes\.claude
├── .codex           →→→ [ponte] →→→ OneDrive\...\assistentes\.codex
├── .agents          →→→ [ponte] →→→ OneDrive\...\assistentes\.agents
├── CLAUDE.md        →→→ [ponte] →→→ OneDrive\...\assistentes\CLAUDE.md
├── AGENTS.md        →→→ [ponte] →→→ OneDrive\...\assistentes\AGENTS.md
└── PROJECT.md       →→→ [ponte] →→→ OneDrive\...\assistentes\PROJECT.md
```

Do ponto de vista do VS Code e dos scripts Python, é como se tudo estivesse na mesma pasta. O Git, porém, ignora essas pontes (o `.gitignore` as lista explicitamente).

---

## 4. Configurar um computador novo (notebook ou desktop)

Ao trabalhar em uma máquina diferente pela primeira vez, siga esta sequência:

### Passo 1 — Clonar o repositório

```powershell
git clone https://github.com/lpchagas/pgd-ocde-icmbio "C:\Projetos\pgd-ocde-icmbio"
cd "C:\Projetos\pgd-ocde-icmbio"
```

### Passo 2 — Aguardar o OneDrive sincronizar

Verifique se a pasta `pgd-ocde-icmbio-privado` aparece em:
`C:\Users\SEU_USUARIO\OneDrive - ICMBio\projetos\`

O ícone do OneDrive na bandeja do sistema deve mostrar sincronização concluída (sem seta de refresh).

### Passo 3 — Criar as pontes

```powershell
.\setup\criar_links_privados.ps1
```

Este script cria as Junctions e HardLinks que conectam o projeto ao OneDrive — incluindo `artefatos_local`, `cgov`, `setup`, `.claude`, `.codex`, `.agents` e os arquivos de contexto dos assistentes de IA. Só precisa ser executado uma vez por computador.

### Passo 4 — Gerar o `.env` desta máquina

```powershell
.\setup\configurar_env.ps1
```

O script detecta automaticamente o nome de usuário Windows e o caminho do driver Denodo instalado pelo DBeaver. Ao final, abre instruções para você preencher apenas CPF e senha.

### Passo 5 — Instalar dependências Python

```powershell
pip install jpype1 pandas matplotlib seaborn python-dotenv
```

### Passo 6 — Testar a conexão

```powershell
python ocde/indicadores/IND_02.1_run.py
```

Se retornar dados, o ambiente está configurado corretamente.

---

## 5. O problema do `.env` em dois computadores

Os scripts Python leem **todos** os caminhos do arquivo `.env`, então não há nada hardcoded no código. Mas o `.env` precisa ser ajustado para cada máquina porque:

| Variável | Por que muda entre máquinas |
|----------|----------------------------|
| `DENODO_USER` | Igual em todas as máquinas (seu CPF) |
| `DENODO_PASSWORD` | Igual em todas (sua senha) |
| `JAVA_HOME` | Geralmente igual, mas pode variar se o DBeaver foi instalado fora do caminho padrão |
| `DENODO_DRIVER_PATH` | **Muda sempre** — depende do nome de usuário Windows e do número de versão do driver (ex.: `/9/` pode virar `/10/` após atualização do DBeaver) |

**O `configurar_env.ps1` resolve isso automaticamente** — ele busca o caminho correto do driver na máquina atual, independentemente do nome de usuário ou versão do driver.

### O que é compartilhado entre os dois computadores

| Item | Compartilhado? | Como |
|------|----------------|------|
| Scripts OCDE (`ocde/indicadores/`) | Sim | Git (`git pull`) |
| Módulos Python (`lib/`) | Sim | Git (`git pull`) |
| Documentação (`docs/`) | Sim | Git (`git pull`) |
| Análises CGOV (`cgov/`) | Sim | OneDrive (automático) |
| Scripts de setup (`setup/`) | Sim | OneDrive (automático) |
| CSVs mensais (`artefatos_local/ocde/entregas/`) | Sim | OneDrive (automático) |
| Diagnósticos e relatórios | Sim | OneDrive (automático) |
| Contexto dos assistentes de IA | Sim | OneDrive (automático) |
| `.env` com credenciais | **Não** | Cada máquina tem o seu próprio |

---

## 6. Rotina de trabalho recomendada

### Ao começar a trabalhar

```
1. git pull                     → pega código e documentação atualizados
2. Aguardar OneDrive sincronizar → artefatos, cgov e contexto de IA já disponíveis
3. Verificar .env presente       → se não, rodar configurar_env.ps1
```

### Ao terminar o trabalho

```
1. git add / git commit / git push   → apenas arquivos públicos (ocde/, lib/, docs/, setup/)
   [o .gitignore bloqueia tudo que for sensível]
2. OneDrive sincroniza automaticamente → artefatos e análises cgov ficam disponíveis no outro computador
```

### O que NUNCA fazer

- `git add .env` — bloqueado pelo .gitignore, mas nunca forçar
- `git add cgov/` — análises CGOV são privadas; ficam no OneDrive
- Copiar credenciais nos comentários de commit ou nos nomes de arquivo
- Mover CSVs para dentro de `docs/` ou `ocde/` — essas pastas são públicas
- Colocar o `.env` no OneDrive — senha em texto puro na nuvem é risco desnecessário

---

## 7. Cuidados com LGPD e dados pessoais

Os CSVs gerados pelos scripts de indicadores podem conter:
- Siglas e nomes de unidades organizacionais
- Contagens de servidores por unidade
- Médias de avaliação por unidade

Esses dados são **funcionais e institucionais**, não nominais. Ainda assim:

- Mantenha-os em `artefatos_local/` (OneDrive — nunca no GitHub)
- Ao compartilhar resultados por e-mail ou apresentação, exporte apenas tabelas agregadas
- Nunca inclua CPFs nos CSVs de entrega (as queries não expõem CPF individualmente, apenas contagens)
- O acesso ao Denodo (que contém dados nominais completos) é protegido por CPF + senha individual e IP liberado pelo Dataprev

---

## 8. Diferença entre as três camadas de armazenamento

| Camada | O que vai | Quem acessa | Voltado para |
|--------|-----------|-------------|--------------|
| **GitHub** (público) | Código, documentação, templates | Qualquer pessoa | Replicação por outros órgãos da APF |
| **OneDrive** (privado/nuvem) | Artefatos, `cgov/`, contexto de IA, resultados | Você (e colegas com acesso ao OneDrive ICMBio) | Continuidade entre seus computadores |
| **Local apenas** | `.env` com credenciais | Só você, nesta máquina | Segurança — senha não vai a lugar nenhum |

---

## 9. Proteção contra perda acidental e backup de redundância

### Por que isso importa

A pasta `OneDrive - ICMBio\projetos\` contém as pontes que conectam o projeto ao OneDrive. Se ela for apagada ou movida acidentalmente, todas as 6 junctions do projeto ficam quebradas e as pastas `artefatos_local`, `cgov`, `setup`, `.claude`, `.codex` e `.agents` aparecem vazias.

O OneDrive recupera arquivos deletados da lixeira da nuvem (por até 93 dias), mas a resincronização pode levar horas. Para minimizar o risco, duas medidas preventivas estão em vigor:

### Medida 1 — Arquivo sentinela

Um arquivo `LEIA-ME_NAO_DELETAR.txt` fica na raiz de `OneDrive - ICMBio\projetos\`. Ele serve de alerta visual antes de qualquer deleção acidental no Explorer ou no OneDrive web.

Para recriar o sentinela (caso seja necessário):

```powershell
.\setup\criar_links_privados.ps1   # verifica se a pasta privada existe
```

### Medida 2 — Backup de redundância no Google Drive

O script `setup\backup_privado.ps1` copia incrementalmente as partes não regeneráveis do projeto para o Google Drive, criando uma segunda cópia independente do OneDrive ICMBio.

**O que é copiado:**

| Pasta | Conteúdo | Por que incluir |
| --- | --- | --- |
| `assistentes\` | CLAUDE.md, skills, .claude/, .codex/ | Não versionado no Git |
| `cgov\` | Análises internas CGOV | Privadas e únicas |
| `setup\` | configurar_env.ps1, criar_links_privados.ps1 | Scripts de recuperação do ambiente |
| `artefatos_local\validacao\` | Relatórios A5 e PDFs A3 | Resultado de trabalho manual — não regenerável |
| `artefatos_local\ocde\diagnosticos\` | Scripts A4 e CSVs de diagnóstico | Registro de investigações — não regenerável |
| `artefatos_local\docs_internos\` | Documentação local | Não versionada |
| `artefatos_local\historico\` | Artefatos de fases anteriores | Referência histórica |

**O que NÃO é copiado (economiza espaço — regenerável):**

| Pasta | Por que excluir |
| --- | --- |
| `artefatos_local\ocde\entregas\` | CSVs mensais dos 12 indicadores — regeneráveis em minutos via `python IND_XX.1_run.py` |
| `artefatos_local\ocde\analises\` | Gráficos PNG — regeneráveis via `/graficos-indicadores` |
| `artefatos_local\ocde\relatorios\` | Relatórios Markdown — regeneráveis via `/relatorio-gerencial` |

**Como executar:**

```powershell
.\setup\backup_privado.ps1
```

O script usa `robocopy` (nativo do Windows) com cópia incremental — só sincroniza o que mudou, sem duplicar dados desnecessariamente.

**Quando executar:**

- Após validar e salvar relatórios A5 importantes
- Após atualizar arquivos de contexto dos assistentes de IA (CLAUDE.md etc.)
- **Antes de reorganizar pastas no OneDrive** ← evita exatamente o incidente que motivou esta seção
- Semanalmente como rotina preventiva

### Recuperação em caso de perda

Se a pasta `projetos\` for deletada do OneDrive:

1. **Recuperar do Google Drive** (imediato): a pasta `My Drive\_projetos\pgd-ocde-icmbio-privado\` contém a última cópia do backup.
2. **Copiar de volta para o OneDrive**: restaurar manualmente para `OneDrive - ICMBio\projetos\pgd-ocde-icmbio-privado\`.
3. **Aguardar sincronização** do OneDrive.
4. **Recriar as junctions**: `.\setup\criar_links_privados.ps1`
5. **Restaurar os CSVs de entregas** (se necessário): reexecutar os scripts `IND_XX.1_run.py` para cada indicador — os dados vêm do Denodo em tempo real.

---

## 10. Resolução de problemas comuns

### "As pastas `artefatos_local`, `cgov`, `.claude` etc. aparecem vazias após clonar o repositório"

Normal — elas não são versionadas no Git. Execute `criar_links_privados.ps1` para recriar as pontes com o OneDrive.

### "A pasta `cgov` não foi criada pelo script de links"

O script exibe `IGNORADO (cgov): destino não existe ainda` se a pasta `cgov/` ainda não existir no OneDrive. Nesse caso:

1. Crie a estrutura manualmente no OneDrive:

   ```powershell
   New-Item -ItemType Directory "$env:USERPROFILE\OneDrive - ICMBio\projetos\pgd-ocde-icmbio-privado\cgov\analises\objetivos_processos" -Force
   ```

2. Aguarde o OneDrive sincronizar
3. Execute `criar_links_privados.ps1` novamente

### "O script Python falha com erro de driver JAR"

O `DENODO_DRIVER_PATH` no `.env` está errado para esta máquina. Execute `configurar_env.ps1` novamente para detectar o caminho correto.

### "O DBeaver atualizou e os scripts pararam de funcionar"

O número de versão do driver mudou (ex.: de `/9/` para `/10/`). Execute `configurar_env.ps1` — ele detecta automaticamente o novo caminho. Lembre também de copiar o arquivo sem extensão como `.jar` conforme descrito no `README.md`.

### "Não encontro a pasta OneDrive - ICMBio no meu computador"

O OneDrive pode ter um nome diferente nesta máquina (ex.: apenas "OneDrive"). Edite a linha `$PRIVADO` no início do `criar_links_privados.ps1` para apontar para o caminho correto.
