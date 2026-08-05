# Suíte de testes automatizados — pgd-ocde-icmbio

Protocolo de verificação de código complementar ao processo humano CGOV
(`docs/09-protocolo-validacao-indicadores.md`). Ver seção "Divisão de
responsabilidade" abaixo.

## Como rodar

```powershell
cd C:\Projetos\pgd-ocde-icmbio
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # uma vez
.venv\Scripts\python.exe -m pytest tests/ -v --tb=short
```

Ou via skill: `/verificar-consistencia`.

## Marcadores (`pytest.ini_options.markers` em `pyproject.toml`)

| Marcador | O que cobre | Depende de rede/Denodo? |
| --- | --- | --- |
| `unit` | Funções puras de `lib/` e `ocde/relatorios/` — períodos, CSV, semáforos, métricas | Não |
| `regression` | Bugs históricos documentados (escala Eixo 4, unidade I07/I08) + sanidade de documentação | Não |
| `integration` | Execução real contra o Denodo (não existe hoje — reservado) | Sim — **skip por padrão** (`addopts = "not integration"`) |

## Divisão de responsabilidade: testes automatizados × CGOV

- **Testes automatizados (`tests/`)** verificam **sintaxe, estrutura e regressão**:
  a query SQL embutida em cada `IND_XX.1_run.py` contém o padrão correto
  (ex.: `(6 - tan.sequencia)`, não `JSON_UNQUOTE`), o CSV gerado tem a
  estrutura esperada, a lógica de períodos não vaza dados de H1/2025. Rodam
  em segundos, sem conexão ao Denodo, e pegam regressões de código.
- **A equipe CGOV (artefato A3, `docs/09-protocolo-validacao-indicadores.md`)**
  verifica **semântica de negócio e realidade dos dados**: os números batem
  com o que o gestor vê no PETRVS ao vivo para uma amostra de 3-5 unidades.
  Nenhum teste automatizado substitui isso — é o único jeito de saber se a
  *interpretação* do indicador está certa, não só se o código está
  sintaticamente correto.

Um script pode passar 100% dos testes automatizados e ainda estar
semanticamente errado (ex.: usar o critério de "concluída" errado); só a
CGOV pega isso. Por isso a Fase 6 do protocolo (checklist A3) formaliza
esse gate humano em vez de tentar substituí-lo por código.

## Por que não há mock de JDBC/jpype

Decisão deliberada (não um gap): mockar `jpype`/`java.sql.Connection` teria
custo alto (simular `ResultSet`, `Statement`, tipos JDBC) e baixo retorno —
o mock testaria a si mesmo, não a query SQL real. A correção da query só é
validada contra o Denodo real (papel do A3/CGOV) ou, estaticamente, pelos
testes de regressão em `tests/regression/test_a1_scripts_static.py` que
fazem `grep` estrutural no texto-fonte. Se no futuro for necessário testar
contra Denodo real, usar `tests/integration/` com `@pytest.mark.integration`
(ignorado por padrão).

## Por que `test_claude_md_consistency.py` pode ficar vermelho

Esse teste (`tests/regression/test_claude_md_consistency.py`) verifica que
todo indicador marcado ✅ em `CLAUDE.md` §11 tem um arquivo A5 físico em
`artefatos_local/validacao/`. Na criação desta suíite (agosto/2026), **nenhum
A5 existe fisicamente** apesar de a maioria dos indicadores estar marcada
como validada — uma dívida de rastreabilidade real, não um bug de teste.
Esse teste fica vermelho **por design** até os relatórios A5 serem escritos
(ver `docs/templates/A3_checklist_validacao_cgov.md` e Fase 6 do protocolo).
Não "conserte" o teste — conserte a dívida documental.

## Estrutura

```
tests/
  conftest.py                    fixtures compartilhadas (project_root, fixtures_dir)
  unit/                           testes de funções puras, sem I/O externo
  regression/                     regressão de bugs históricos + sanidade de docs
  integration/                    reservado para testes contra Denodo real (skip por padrão)
  fixtures/
    csv_bons/                     CSVs sintéticos válidos
    csv_corrompidos/               CSVs sintéticos com defeitos propositais
    docs_sql_sinteticos/           docs .md sintéticos para lib/docs_sql.py
```
