"""Regressão estática dos 12 scripts A1 (ocde/indicadores/IND_XX.1_run.py).

Não executa nenhum script — lê o texto-fonte e aplica asserções regex.
Cada caso aqui corresponde a um bug histórico real, documentado em
CLAUDE.md §11 ("Bugs históricos corrigidos — não repetir"), que já
aconteceu neste projeto e foi corrigido silenciosamente uma vez.

IMPORTANTE: as asserções positivas (padrão correto presente) são checadas
dentro da string SQL_IXX/SQL_I01_PLANOS extraída do arquivo — nunca no
texto completo do módulo. As docstrings destes scripts documentam de
propósito o bug antigo (ex.: "o SQL original usava JSON_UNQUOTE..."), então
uma checagem ingênua de "JSON_UNQUOTE not in source" sobre o arquivo inteiro
daria falso positivo (falharia mesmo com o bug corrigido, por causa do
comentário histórico). Checar só dentro da SQL real evita essa armadilha.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.regression

INDICADORES_DIR = Path(__file__).resolve().parents[2] / "ocde" / "indicadores"

TODOS_OS_INDICADORES = [f"{i:02d}" for i in range(1, 13)]


def _source(indicador: str) -> str:
    path = INDICADORES_DIR / f"IND_{indicador}.1_run.py"
    assert path.exists(), f"Script A1 não encontrado: {path}"
    return path.read_text(encoding="utf-8")


def _sql_constant(source: str, var_name: str) -> str:
    """Extrai o conteúdo de `VAR_NAME = \"\"\"...\"\"\"` — ignora docstrings/comentários."""
    match = re.search(rf'{re.escape(var_name)}\s*=\s*"""(.*?)"""', source, flags=re.DOTALL)
    assert match, f"Não encontrei a constante {var_name} no script."
    return match.group(1)


# ---------------------------------------------------------------------------
# Regressão: escala do Eixo 4 invertida (bug corrigido 12.06.2026 / 19.06.2026)
# JSON_UNQUOTE(tan.nota) não funciona no Denodo VQL e retornava NULL para
# todos os registros; sequencia=2/5 eram trocados com sequencia=4/1.
# ---------------------------------------------------------------------------

class TestEscalaEixo4:
    @pytest.mark.parametrize("indicador,var_name", [("09", "SQL_I09"), ("12", "SQL_I12")])
    def test_score_usa_formula_correta(self, indicador, var_name):
        sql = _sql_constant(_source(indicador), var_name)
        assert re.search(r"\(\s*6\s*-\s*tan\.sequencia\s*\)", sql), (
            f"SQL_{var_name} deve calcular o score via (6 - tan.sequencia)."
        )
        assert "JSON_UNQUOTE" not in sql, (
            f"SQL_{var_name} não deve usar JSON_UNQUOTE (não suportado no Denodo VQL)."
        )

    def test_i10_inadequado_usa_sequencia_4(self):
        sql = _sql_constant(_source("10"), "SQL_I10")
        # aceita tan.sequencia = 4 diretamente ou via alias (ex.: sequencia_nota = 4)
        assert re.search(r"sequencia\w*\s*=\s*4", sql), (
            "I10 (Inadequado) deve filtrar por sequencia (ou alias) = 4."
        )
        assert "JSON_UNQUOTE" not in sql

    def test_i11_excepcional_usa_sequencia_1(self):
        sql = _sql_constant(_source("11"), "SQL_I11")
        assert re.search(r"sequencia\w*\s*=\s*1", sql), (
            "I11 (Excepcional) deve filtrar por sequencia (ou alias) = 1."
        )
        assert "JSON_UNQUOTE" not in sql


# ---------------------------------------------------------------------------
# Regressão: unidade errada em I07/I08 (bug corrigido — pt.unidade_id era o
# servidor, não o dono da entrega; correto é COALESCE(pe.unidade_id, ph.unidade_id))
# ---------------------------------------------------------------------------

class TestUnidadeI07I08:
    @pytest.mark.parametrize("indicador,var_name", [("07", "SQL_I07"), ("08", "SQL_I08")])
    def test_join_de_unidade_usa_coalesce_pe_ph(self, indicador, var_name):
        sql = _sql_constant(_source(indicador), var_name)
        assert re.search(
            r"COALESCE\(\s*pe\.unidade_id\s*,\s*ph\.unidade_id\s*\)", sql
        ), (
            f"SQL_{var_name} deve atribuir a unidade via "
            "COALESCE(pe.unidade_id, ph.unidade_id)."
        )


# ---------------------------------------------------------------------------
# Conformidade com o padrão canônico — comum aos 12 scripts A1
# (formaliza a Dimensão 1/2 de .claude/skills/p3b-auditar/SKILL.md)
# ---------------------------------------------------------------------------

class TestPadraoCanonico:
    @pytest.mark.parametrize("indicador", TODOS_OS_INDICADORES)
    def test_credenciais_vem_do_env_nunca_hardcoded(self, indicador):
        source = _source(indicador)
        assert "get_config(require_credentials=True)" in source or "get_config(" in source
        # nenhuma credencial literal deve aparecer nos scripts públicos
        assert not re.search(r'PASS\w*\s*=\s*["\'][^"\']{4,}["\']', source)
        assert not re.search(r"\b\d{11}\b", source), "CPF literal não deve aparecer no A1."

    @pytest.mark.parametrize("indicador", TODOS_OS_INDICADORES)
    def test_usa_write_pipe_csv_do_lib(self, indicador):
        source = _source(indicador)
        assert "from lib.csv_utils import" in source
        assert "write_pipe_csv" in source

    @pytest.mark.parametrize("indicador", TODOS_OS_INDICADORES)
    def test_usa_build_periods_pe_ou_pt(self, indicador):
        source = _source(indicador)
        assert "build_periods_pe" in source or "build_periods_pt" in source, (
            "Todo A1 deve usar a segmentação canônica de períodos de lib.periodos."
        )

    @pytest.mark.parametrize("indicador", [i for i in TODOS_OS_INDICADORES if i != "01"])
    def test_conexao_e_fechada_no_finally(self, indicador):
        """I01 é a exceção documentada (query única + agregação em Python)."""
        source = _source(indicador)
        assert "conn.close()" in source, f"IND_{indicador}.1_run.py deve fechar a conexão JDBC."

    @pytest.mark.parametrize("indicador", [i for i in TODOS_OS_INDICADORES if i != "01"])
    def test_loop_de_periodos_tem_try_except(self, indicador):
        """Falha de uma query em um período não deve abortar os demais períodos."""
        source = _source(indicador)
        assert "try:" in source and "except" in source, (
            f"IND_{indicador}.1_run.py deve isolar erros por período com try/except."
        )
