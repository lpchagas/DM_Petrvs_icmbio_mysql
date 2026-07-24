# pgd-ocde-icmbio — Indicadores OCDE/PGD via Denodo

Consultas SQL e documentação para calcular os **12 indicadores OCDE/PGD** do ICMBio diretamente do banco PETRVS em tempo real, via Denodo (MGI/Dataprev). Sem Docker, sem ETL, sem instalação de banco de dados local.

Desenvolvido pela Coordenação de Governança (CGOV/ICMBio) no âmbito do piloto OCDE/MGI para transformação do PGD em instrumento de gestão de desempenho.

> **Para outros órgãos da APF:** este repositório pode ser reutilizado por qualquer instituição que utilize o PETRVS e tenha acesso ao Denodo do MGI/Dataprev. As queries funcionam sem modificação — basta apontar para o schema do seu órgão.

---

## Para quem não programa: como ler este projeto

Este repositório mistura três tipos de conteúdo. Se você é gestor ou analista de negócio, o que interessa está quase sempre na primeira coluna:

| Se você quer... | Vá para... |
| --- | --- |
| Entender o que cada indicador mede, sem código | [docs/08-guia-rapido-gestores.md](docs/08-guia-rapido-gestores.md) |
| Ver o contexto do piloto OCDE/PGD e por que ele existe | [docs/05-contexto-ocde-pgd.md](docs/05-contexto-ocde-pgd.md) |
| Consultar a ficha técnica de um indicador específico (I01–I12) | [docs/ocde/06-indicadores-ocde-mysql.md](docs/ocde/06-indicadores-ocde-mysql.md) |
| Pegar os números já prontos (CSV/planilha) | Pasta `artefatos_local/` — só existe no computador de quem já rodou o processo; não fica no GitHub |
| Rodar as consultas você mesmo | Seções "Início rápido" abaixo |

Tudo o que aparece como pasta com nome técnico (`lib/`, `ocde/relatorios/` etc.) é código de apoio — você não precisa abrir esses arquivos para entender os resultados.

---

## Pré-requisitos

| Ferramenta | Para quê | Como obter |
| --- | --- | --- |
| DBeaver Community | Executar as queries SQL | [dbeaver.io/download](https://dbeaver.io/download/) — gratuito |
| Acesso ao Denodo | Credenciais + IP liberado | Solicitar ao gestor responsável pelo PGD no seu órgão |
| VS Code + Python | Apenas para o Notebook Jupyter ou os scripts mensais | Opcional — só se quiser usar a Opção B ou C |

Não é necessário MySQL, Docker, PostgreSQL ou qualquer banco de dados local.

---

## Início rápido

### Para gestores (sem SQL)

Leia [docs/08-guia-rapido-gestores.md](docs/08-guia-rapido-gestores.md) — entenda os indicadores e interprete os resultados sem precisar executar código.

---

### Para analistas — Opção A: DBeaver (recomendado)

1. Configure a conexão Denodo no DBeaver seguindo [docs/03-acesso-direto-denodo-dbeaver.md](docs/03-acesso-direto-denodo-dbeaver.md) (detalhamento em [docs/04-configuracao-dbeaver.md](docs/04-configuracao-dbeaver.md))
2. Abra o índice do manual: [docs/ocde/06-indicadores-ocde-mysql.md](docs/ocde/06-indicadores-ocde-mysql.md)
3. Navegue até o indicador desejado e copie a query para um SQL Editor
4. Ajuste as datas no bloco `parametros` e execute com `Ctrl + A` > `Ctrl + Enter`

---

### Para analistas — Opção B: Jupyter Notebook no VS Code

#### Passo 1 — Clone ou baixe este repositório

```bash
git clone https://github.com/lpchagas/pgd-ocde-icmbio.git
```

Ou clique em **Code > Download ZIP** no GitHub e extraia a pasta.

#### Passo 2 — Copie o arquivo de configuração

Na pasta do projeto, localize o arquivo `.env.example`. Faça uma cópia e renomeie para `.env`:

```text
.env.example  →  .env
```

#### Passo 3 — Preencha suas credenciais

Abra o arquivo `.env` com o Bloco de Notas e preencha com as credenciais fornecidas pelo gestor responsável pelo PGD no seu órgão:

```ini
DENODO_USER=seu_cpf_aqui
DENODO_PASSWORD=sua_senha_aqui
DENODO_DRIVER_PATH=C:/Users/SEU_USUARIO/AppData/Roaming/DBeaverData/...
```

> O arquivo `.env` fica apenas no seu computador. Ele não vai para o GitHub. Sua senha nunca sai da sua máquina.

#### Passo 4 — Execute o notebook

Abra o arquivo `consultas_denodo_template.ipynb` no VS Code e execute as células em ordem.

Guia completo para quem nunca usou Python: [docs/10-jupyter-guia-iniciantes.md](docs/10-jupyter-guia-iniciantes.md)

Guia passo a passo por indicador (qual query colar, quais parâmetros ajustar, como exportar): [ocde/indicadores/guia-jupyter/](ocde/indicadores/guia-jupyter/) — um arquivo `IND_XX_guia_jupyter.md` para cada um dos 12 indicadores.

---

### Para rotina mensal — Scripts Python sanitizados

Os scripts em `ocde/indicadores/` geram os CSVs mensais dos indicadores sem armazenar credenciais no código. Eles leem a conexão do arquivo local `.env` e salvam as saídas em `artefatos_local/` (pasta ignorada pelo git, presente só no computador de quem executa).

Exemplo:

```powershell
python ocde/indicadores/IND_02.1_run.py
```

Fluxo completo, calendário mensal e checklist: [docs/11-guia-extracao-mensal.md](docs/11-guia-extracao-mensal.md)

Checklist de segurança antes de publicar: [docs/12-seguranca-publicacao.md](docs/12-seguranca-publicacao.md)

---

## Indicadores disponíveis

| # | Indicador | Eixo | Documento |
| --- | --- | --- | --- |
| I01 | Proporção de servidores por regime de trabalho | 1. Trabalho Remoto | [06.1.1-i01.md](docs/ocde/06.1.1-i01.md) |
| I02 | Taxa de cumprimento das entregas por unidade | 2. Execução | [06.2.1-i02.md](docs/ocde/06.2.1-i02.md) |
| I03 | Taxa de cumprimento de metas por entrega | 2. Execução | [06.2.2-i03.md](docs/ocde/06.2.2-i03.md) |
| I04 | Índice de atingimento de metas — score médio | 2. Execução | [06.2.3-i04.md](docs/ocde/06.2.3-i04.md) |
| I05 | Distribuição das entregas entre os servidores | 3. Carga de Trabalho | [06.3.1-i05.md](docs/ocde/06.3.1-i05.md) |
| I06 | Grau de responsabilidade pelas entregas | 3. Carga de Trabalho | [06.3.2-i06.md](docs/ocde/06.3.2-i06.md) |
| I07 | Horas por entrega — planejadas (absoluto) | 3. Carga de Trabalho | [06.3.3-i07.md](docs/ocde/06.3.3-i07.md) |
| I08 | Proporção de horas por entrega — planejadas (%) | 3. Carga de Trabalho | [06.3.4-i08.md](docs/ocde/06.3.4-i08.md) |
| I09 | Média da avaliação do Plano de Trabalho por unidade | 4. Desempenho e Avaliação | [06.4.1-i09.md](docs/ocde/06.4.1-i09.md) |
| I10 | Percentual de avaliações inadequadas | 4. Desempenho e Avaliação | [06.4.2-i10.md](docs/ocde/06.4.2-i10.md) |
| I11 | Percentual de avaliações excepcionais | 4. Desempenho e Avaliação | [06.4.3-i11.md](docs/ocde/06.4.3-i11.md) |
| I12 | Coerência entre avaliação do PT e do PE | 4. Desempenho e Avaliação | [06.4.4-i12.md](docs/ocde/06.4.4-i12.md) |

Índice navegável com descrição completa de cada indicador: [docs/ocde/06-indicadores-ocde-mysql.md](docs/ocde/06-indicadores-ocde-mysql.md)

---

## Estrutura do projeto — o que cada pasta faz

A tabela abaixo descreve **todas as pastas de primeiro nível** do repositório e para que servem. As marcadas como "código" só interessam a quem programa; as demais são de interesse geral.

| Pasta | Tipo | Finalidade |
| --- | --- | --- |
| **`docs/`** | 📄 Documentação | Manual do projeto: visão geral, guia para gestores, contexto OCDE/PGD, fichas técnicas dos 12 indicadores, protocolos de validação e segurança. É o ponto de entrada para entender o "o quê" e o "porquê" — veja detalhamento abaixo. |
| **`ocde/`** | ⚙️ Código | Scripts que calculam os 12 indicadores OCDE/PGD a partir do Denodo (a iniciativa principal deste repositório). Inclui os scripts de extração mensal, os módulos de relatório gerencial e os templates de diagnóstico. |
| **`mgi/`** | ⚙️ Código (embrionário) | Reservado para futuros indicadores solicitados diretamente pelo MGI, além dos 12 já validados com o ICMBio. Hoje contém apenas a estrutura inicial. |
| **`lib/`** | ⚙️ Código | Biblioteca compartilhada usada por todos os scripts de indicadores: conexão com o Denodo, definição dos períodos de análise (mensal/trimestral/quadrimestral), limpeza e exportação de CSV, checagens automáticas de qualidade. Nada aqui precisa ser lido por quem só consome os resultados. |
| **`artefatos_local/`** | 📊 Dados (não versionado) | Onde ficam os CSVs prontos (por mês, por indicador) depois que alguém executa a extração. **Não existe no GitHub** — só no computador de quem rodou o processo e sincroniza via OneDrive. É aqui que estão as planilhas que alimentam o Power BI/COCAGE. |
| **`cgov/`** | 🔒 Privado (não versionado) | Análises internas ad hoc da Coordenação de Governança. Fica em uma pasta do OneDrive "linkada" ao projeto (Junction) — nunca é publicada no GitHub. |
| **`setup/`** | 🔒 Privado (não versionado) | Scripts de configuração do ambiente local (backup, criação dos links privados). Uso exclusivo de quem administra o repositório na própria máquina. |
| **`.claude/` / `.codex/` / `.agents/`** | 🤖 Automação | Comandos e automações ("skills") usadas pelos assistentes de IA (Claude Code, Codex, Antigravity) que ajudam a manter este projeto. Não afeta os resultados dos indicadores. |
| **`.venv/`** | ⚙️ Ambiente técnico | Ambiente Python isolado do projeto (dependências). Gerado automaticamente — nunca precisa ser aberto manualmente. |

> As pastas `cgov/` e `setup/` aparecem no Explorador de Arquivos porque são *Junctions* (atalhos do Windows) apontando para pastas do OneDrive fora do repositório Git. Elas nunca sobem para o GitHub. Detalhes em [docs/13-organizacao-publico-privado.md](docs/13-organizacao-publico-privado.md).

### Dentro de `docs/` — o manual do projeto

| Arquivo/Pasta | Conteúdo |
| --- | --- |
| [01-visao-geral.md](docs/01-visao-geral.md) | Conceito do projeto, como funciona o fluxo via Denodo, comparação com a versão anterior (datamart/ETL) |
| [03-acesso-direto-denodo-dbeaver.md](docs/03-acesso-direto-denodo-dbeaver.md) | Como conectar no Denodo usando o DBeaver |
| [04-configuracao-dbeaver.md](docs/04-configuracao-dbeaver.md) | Configuração detalhada do driver e da conexão no DBeaver |
| [05-contexto-ocde-pgd.md](docs/05-contexto-ocde-pgd.md) | Contexto do piloto OCDE/PGD, perfil do ICMBio, achados quantitativos gerais |
| [07-estrutura-banco-dados.md](docs/07-estrutura-banco-dados.md) | Dicionário das tabelas e campos do banco PETRVS usados nos cálculos |
| [08-guia-rapido-gestores.md](docs/08-guia-rapido-gestores.md) | **Ponto de partida para quem não programa** — o que cada indicador significa e como interpretá-lo |
| [09-protocolo-validacao-indicadores.md](docs/09-protocolo-validacao-indicadores.md) | Como cada indicador é validado (etapas A1 a A5) antes de virar dado oficial |
| [10-jupyter-guia-iniciantes.md](docs/10-jupyter-guia-iniciantes.md) | Passo a passo para usar o Notebook Jupyter sem experiência prévia em Python |
| [11-guia-extracao-mensal.md](docs/11-guia-extracao-mensal.md) | Calendário e comandos da rotina mensal de extração dos indicadores |
| [12-seguranca-publicacao.md](docs/12-seguranca-publicacao.md) | Checklist para evitar vazamento de credenciais e dados pessoais antes de publicar |
| [13-organizacao-publico-privado.md](docs/13-organizacao-publico-privado.md) | O que é público (GitHub), privado (OneDrive) e local em cada pasta |
| `docs/ocde/` | As **fichas técnicas dos 12 indicadores** (uma por indicador) + 4 fichas de eixo + o índice geral [06-indicadores-ocde-mysql.md](docs/ocde/06-indicadores-ocde-mysql.md) |
| `docs/cgov/` e `docs/mgi/` | Páginas públicas de apresentação das iniciativas CGOV e MGI (sem dados sensíveis) |

### Dentro de `ocde/` — o motor dos indicadores

| Subpasta | Conteúdo |
| --- | --- |
| `indicadores/` | Um script por indicador (`IND_01.1_run.py` a `IND_12.1_run.py`). Cada um se conecta ao Denodo, roda a query oficial e salva o CSV do período. |
| `indicadores/guia-jupyter/` | Guias `IND_XX_guia_jupyter.md` (um por indicador) com o passo a passo para rodar a mesma query manualmente pelo Notebook Jupyter (Opção B), sem precisar executar o script Python. |
| `relatorios/` | Módulos que leem os CSVs já extraídos e montam análises gerenciais (classificação de desempenho, métricas agregadas, geração de relatório). |
| `diagnosticos/` | Modelo (template) usado para investigar achados inesperados de um indicador antes de fechar a validação. |

---

## Ciclo de vida de um indicador (resumo)

1. **Extração (A1/A2):** o script Python roda a query no Denodo e gera o CSV do mês → `artefatos_local/ocde/entregas/AAAA-MM/`
2. **Validação manual (A3):** a equipe CGOV analisa os números e aponta inconsistências ou confirma a leitura
3. **Diagnóstico (A4):** se necessário, um script investigativo aprofunda um achado específico
4. **Relatório de validação (A5):** documento final que registra a decisão técnica sobre o indicador

Protocolo completo: [docs/09-protocolo-validacao-indicadores.md](docs/09-protocolo-validacao-indicadores.md)

---

## Projeto relacionado

[DM_Petrvs_icmbio_postgre](https://github.com/lpchagas/DM_Petrvs_icmbio_postgre) — fluxo completo com ETL, datamart PostgreSQL e dashboards Apache Superset. Indicado quando o objetivo é monitoramento contínuo com visualizações prontas, em vez de análise ad hoc via SQL.
