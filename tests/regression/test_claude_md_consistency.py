"""Sanidade de rastreabilidade: CLAUDE.md §11 × artefatos_local/validacao/.

Este teste é diferente dos demais em tests/regression/: ele não verifica uma
regressão de CÓDIGO, verifica uma DÍVIDA DE PROCESSO. Ver tests/README.md
("Por que test_claude_md_consistency.py pode ficar vermelho") antes de
"consertar" uma falha aqui — a correção certa quase sempre é escrever o
relatório A5 que falta, não editar este teste.

Regra (docs/09-protocolo-validacao-indicadores.md §3, Fase 2): um indicador
só pode estar marcado ✅ na coluna A5 da tabela de status de CLAUDE.md §11 se
o arquivo `artefatos_local/validacao/IND_XX.5_relatorio_validacao_*.md`
correspondente existir fisicamente.

CLAUDE.md é local/gitignored (contém credenciais) — este teste é ignorado
(skip) se o arquivo não existir no ambiente atual.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.regression

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
VALIDACAO_DIR = PROJECT_ROOT / "artefatos_local" / "validacao"

# Linha de tabela: | I01 | ✅ | ✅ | ⬜ | ✅ prelim | 137+10.367 | mensal PT | ... |
_ROW_RE = re.compile(
    r"^\|\s*I(\d{2})\s*\|\s*(?P<a1>[^|]*)\|\s*(?P<a2>[^|]*)\|\s*(?P<a3>[^|]*)\|\s*(?P<a5>[^|]*)\|"
)


def _status_por_indicador() -> dict[str, str]:
    """Faz o parsing da tabela de status de CLAUDE.md §11 → {indicador: valor_da_coluna_A5}."""
    if not CLAUDE_MD.exists():
        pytest.skip("CLAUDE.md não existe neste ambiente (arquivo local/gitignored).")
    texto = CLAUDE_MD.read_text(encoding="utf-8")
    status: dict[str, str] = {}
    for linha in texto.splitlines():
        match = _ROW_RE.match(linha.strip())
        if not match:
            continue
        status[f"I{match.group(1)}"] = match.group("a5").strip()
    return status


def _tem_a5_fisico(indicador: str) -> bool:
    if not VALIDACAO_DIR.exists():
        return False
    padrao = f"IND_{indicador[1:]}.5_relatorio_validacao_*.md"
    return any(VALIDACAO_DIR.glob(padrao))


def test_tabela_de_status_foi_encontrada_e_parseada():
    status = _status_por_indicador()
    assert status, (
        "Não encontrei nenhuma linha da tabela de status (CLAUDE.md §11) — "
        "o formato da tabela pode ter mudado; revisar _ROW_RE."
    )


@pytest.mark.parametrize("indicador", [f"I{i:02d}" for i in range(1, 13)])
def test_indicador_aprovado_tem_a5_fisico(indicador):
    status = _status_por_indicador()
    valor_a5 = status.get(indicador)
    if valor_a5 is None:
        pytest.skip(f"{indicador} não está na tabela de status de CLAUDE.md §11.")
    if not valor_a5.startswith("✅"):
        pytest.skip(f"{indicador} não está marcado ✅ em A5 (valor atual: {valor_a5!r}).")
    assert _tem_a5_fisico(indicador), (
        f"{indicador} está marcado '{valor_a5}' na coluna A5 de CLAUDE.md §11, mas não há "
        f"nenhum arquivo IND_{indicador[1:]}.5_relatorio_validacao_*.md em "
        f"{VALIDACAO_DIR} — dívida de rastreabilidade, escrever o A5 (ver /p5-gerar-a5)."
    )
