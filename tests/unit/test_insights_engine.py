"""Testes de ocde/relatorios/insights_engine.py — só as funções auxiliares puras.

As funções `insights_eixoN` completas geram texto narrativo longo; testá-las
por igualdade literal de string seria frágil (qualquer ajuste de redação
quebraria o teste sem indicar um bug real). Em vez disso, testamos aqui só o
contrato das funções auxiliares (`_sorted_periodos`, `_enc`, `_ult`,
`_delta_str`) e um teste de fumaça (não quebra com DataFrame vazio) para
cada `insights_eixoN`.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ocde.relatorios.insights_engine import (
    _delta_str,
    _enc,
    _sorted_periodos,
    _ult,
    insights_eixo1,
    insights_eixo2,
    insights_eixo3,
    insights_eixo4,
)

pytestmark = pytest.mark.unit


class TestSortedPeriodos:
    def test_ordena_cronologicamente(self):
        df = pd.DataFrame({"periodo": ["Q1-2026", "T4-2025", "T3-2025"]})
        assert _sorted_periodos(df) == ["T3-2025", "T4-2025", "Q1-2026"]

    def test_remove_duplicatas(self):
        df = pd.DataFrame({"periodo": ["T3-2025", "T3-2025", "T4-2025"]})
        assert _sorted_periodos(df) == ["T3-2025", "T4-2025"]


class TestEnc:
    def test_none_retorna_df_vazio(self):
        assert _enc(None).empty

    def test_filtra_por_status_encerrado(self):
        df = pd.DataFrame({"periodo_status": ["encerrado", "em_andamento"]})
        assert len(_enc(df)) == 1

    def test_sem_coluna_status_retorna_tudo(self):
        df = pd.DataFrame({"periodo": ["T3-2025"]})
        assert len(_enc(df)) == 1


class TestUlt:
    def test_none_retorna_string_vazia(self):
        assert _ult(None) == ""

    def test_retorna_ultimo_periodo_encerrado(self):
        df = pd.DataFrame(
            {"periodo": ["T3-2025", "T4-2025"], "periodo_status": ["encerrado", "encerrado"]}
        )
        assert _ult(df) == "T4-2025"

    def test_sem_periodos_encerrados_retorna_vazio(self):
        df = pd.DataFrame({"periodo": ["Q1-2026"], "periodo_status": ["em_andamento"]})
        assert _ult(df) == ""


class TestDeltaStr:
    def test_none_retorna_vazio(self):
        assert _delta_str(None) == ""

    def test_melhora_acima_de_5(self):
        assert "melhora" in _delta_str(10.0)
        assert "▲" in _delta_str(10.0)

    def test_queda_abaixo_de_menos_5(self):
        assert "queda" in _delta_str(-10.0)
        assert "▼" in _delta_str(-10.0)

    def test_estavel_dentro_de_mais_menos_5(self):
        assert "estável" in _delta_str(2.0)
        assert "estável" in _delta_str(-2.0)
        assert "estável" in _delta_str(0.0)

    @pytest.mark.parametrize("delta", [5.0, -5.0])
    def test_borda_exata_de_5_e_estavel(self, delta):
        """delta > 5 / delta < -5 são estritos — exatamente 5 ainda é 'estável'."""
        assert "estável" in _delta_str(delta)


# ---------------------------------------------------------------------------
# Testes de fumaça: insights_eixoN não devem quebrar com entradas degeneradas
# (DataFrame vazio, None, ou uma única unidade) — não validamos o texto.
# ---------------------------------------------------------------------------

class TestInsightsSmokeTests:
    """Cada insights_eixoN retorna (insights: list[str], recomendacoes: list[str])."""

    def test_eixo1_nao_quebra_com_none(self):
        ins, rec = insights_eixo1(None, None)
        assert isinstance(ins, list) and isinstance(rec, list)

    def test_eixo1_nao_quebra_com_dfs_vazios(self):
        vazio = pd.DataFrame()
        ins, rec = insights_eixo1(vazio, vazio)
        assert isinstance(ins, list) and isinstance(rec, list)

    def test_eixo2_nao_quebra_com_dfs_e_series_vazias(self):
        vazio = pd.DataFrame()
        ins, rec = insights_eixo2(vazio, [], vazio, [], vazio, [])
        assert isinstance(ins, list) and isinstance(rec, list)

    def test_eixo3_nao_quebra_com_dfs_e_series_vazias(self):
        vazio = pd.DataFrame()
        ins, rec = insights_eixo3(vazio, [], vazio, vazio, [], vazio, [])
        assert isinstance(ins, list) and isinstance(rec, list)

    def test_eixo4_nao_quebra_com_dfs_e_series_vazias(self):
        vazio = pd.DataFrame()
        ins, rec = insights_eixo4(vazio, [], vazio, [], vazio, [], vazio)
        assert isinstance(ins, list) and isinstance(rec, list)
