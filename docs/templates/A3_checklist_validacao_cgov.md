# A3 — Checklist de Validação Manual CGOV

**Indicador:** IXX — `<nome do indicador>`
**Período analisado:** `<ex.: T4-2025, Q1-2026, M03-2026>`
**Data da consulta:** DD.MM.AAAA
**Validador(es) CGOV:** `<nome(s)>`

Preencher e salvar como
`artefatos_local/validacao/IND_XX.3_PETRVS_consulta_DD.MM.AAAA.pdf`
(ou, para confirmação verbal, ver seção "Confirmação verbal" ao final —
**não deixe a validação sem nenhum artefato físico**: o objetivo deste
checklist é fechar a lacuna A3→A5 identificada em CLAUDE.md §11, onde
indicadores aparecem como validados sem nenhum rastro salvo em
`artefatos_local/validacao/`.)

Instruções gerais: `docs/09-protocolo-validacao-indicadores.md` §3 (Fase 2).

---

## 1. Unidades amostradas (3–5, perfis variados)

| # | Unidade (sigla) | Perfil (grande/pequena, plano avaliado/ativo) | Valor no PETRVS (sistema ao vivo) | Valor no CSV A2 | Bate? |
|---|---|---|---|---|---|
| 1 | | | | | ☐ Sim ☐ Não |
| 2 | | | | | ☐ Sim ☐ Não |
| 3 | | | | | ☐ Sim ☐ Não |
| 4 (opcional) | | | | | ☐ Sim ☐ Não |
| 5 (opcional) | | | | | ☐ Sim ☐ Não |

## 2. Hipóteses sobre divergências encontradas

Para cada linha "Não" acima, registrar uma hipótese (mesmo que preliminar —
será refinada na Fase 3/A4 pelo analista técnico):

- H1: `<hipótese>`
- H2: `<hipótese>`

## 3. Veredito

☐ **Confirma** — valores do CSV A2 batem com o PETRVS nas unidades amostradas, sem ressalvas
☐ **Confirma com ressalvas** — bate na maioria, mas há hipóteses a investigar (preencher seção 2)
☐ **Diverge** — descolamento relevante entre A2 e PETRVS; aguardar diagnóstico A4/A5 antes de publicar

## 4. Confirmação verbal (usar somente quando não houver PDF de consulta)

Se a validação ocorreu em reunião/conversa informal em vez de consulta
documentada no PETRVS, preencher aqui em vez da seção 1 — isso formaliza
o padrão "✅ verbal" já usado em CLAUDE.md §11, em vez de deixá-lo sem
nenhum registro:

- Data: DD.MM.AAAA
- Quem confirmou (nome, cargo): `<nome>`
- Meio (reunião presencial, chamada, e-mail, chat): `<meio>`
- Resumo do que foi confirmado: `<texto livre>`

---

**Próximo passo:** entregar este checklist preenchido ao analista técnico
para a Fase 3 (`/p4-gerar-a4`) — diagnóstico técnico e elaboração do
relatório A5 (`IND_XX.5_relatorio_validacao_DD.MM.AAAA.md` em
`artefatos_local/validacao/`). **Um indicador só deve ser marcado ✅ em
CLAUDE.md §11 depois que o A5 correspondente existir fisicamente nessa
pasta** — ver `tests/regression/test_claude_md_consistency.py`.
