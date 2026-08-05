"""Testes de ocde/relatorios/metricas.py — séries, rankings e variações, com DataFrames sintéticos."""
from __future__ import annotations

import pandas as pd
import pytest

from ocde.relatorios.metricas import (
    calcular_serie,
    pct_unidades_em_faixa,
    ranking_unidades,
    variacao_por_unidade,
)

pytestmark = pytest.mark.unit


def _df():
    return pd.DataFrame(
        {
            "periodo": ["T3-2025", "T3-2025", "T4-2025", "T4-2025", "T4-2025"],
            "unidade_sigla": ["ICMBio-A", "ICMBio-B", "ICMBio-A", "ICMBio-B", "ICMBio-C"],
            "valor": [80.0, 60.0, 90.0, 50.0, None],
        }
    )


class TestCalcularSerie:
    def test_df_vazio_retorna_lista_vazia(self):
        assert calcular_serie(pd.DataFrame(), "valor") == []

    def test_df_none_retorna_lista_vazia(self):
        assert calcular_serie(None, "valor") == []

    def test_coluna_inexistente_retorna_lista_vazia(self):
        assert calcular_serie(_df(), "coluna_que_nao_existe") == []

    def test_calcula_media_por_periodo_em_ordem_cronologica(self):
        resultado = calcular_serie(_df(), "valor")
        assert [r.periodo for r in resultado] == ["T3-2025", "T4-2025"]
        assert resultado[0].media == 70.0  # média de 80 e 60
        assert resultado[0].n == 2

    def test_ignora_nan_no_denominador(self):
        resultado = calcular_serie(_df(), "valor")
        # T4-2025 tem 3 linhas mas uma é NaN -> n deve ser 2, não 3
        t4 = next(r for r in resultado if r.periodo == "T4-2025")
        assert t4.n == 2
        assert t4.media == 70.0  # média de 90 e 50

    def test_delta_pct_primeiro_periodo_e_none(self):
        resultado = calcular_serie(_df(), "valor")
        assert resultado[0].delta_pct is None

    def test_delta_pct_calculado_no_periodo_seguinte(self):
        resultado = calcular_serie(_df(), "valor")
        # média T3=70, média T4=70 -> variação 0%
        assert resultado[1].delta_pct == 0.0

    def test_periodo_com_todos_nan_e_pulado(self):
        df = pd.DataFrame(
            {
                "periodo": ["T3-2025", "T4-2025"],
                "unidade_sigla": ["ICMBio-A", "ICMBio-B"],
                "valor": [None, 50.0],
            }
        )
        resultado = calcular_serie(df, "valor")
        assert [r.periodo for r in resultado] == ["T4-2025"]


class TestRankingUnidades:
    def test_df_vazio_retorna_df_vazio(self):
        assert ranking_unidades(pd.DataFrame(), "valor", "T3-2025").empty

    def test_coluna_unidade_ausente_retorna_df_vazio(self):
        df = pd.DataFrame({"periodo": ["T3-2025"], "valor": [1.0]})
        assert ranking_unidades(df, "valor", "T3-2025").empty

    def test_ranking_ascendente(self):
        resultado = ranking_unidades(_df(), "valor", "T4-2025", asc=True)
        assert list(resultado["unidade_sigla"]) == ["ICMBio-B", "ICMBio-A"]

    def test_ranking_descendente(self):
        resultado = ranking_unidades(_df(), "valor", "T4-2025", asc=False)
        assert list(resultado["unidade_sigla"]) == ["ICMBio-A", "ICMBio-B"]

    def test_unidade_duplicada_e_agregada_pela_media(self):
        df = pd.DataFrame(
            {
                "periodo": ["T3-2025"] * 3,
                "unidade_sigla": ["ICMBio-A", "ICMBio-A", "ICMBio-B"],
                "valor": [10.0, 30.0, 50.0],
            }
        )
        resultado = ranking_unidades(df, "valor", "T3-2025")
        assert len(resultado) == 2
        row_a = resultado[resultado["unidade_sigla"] == "ICMBio-A"].iloc[0]
        assert row_a["valor"] == 20.0  # média de 10 e 30


class TestVariacaoPorUnidade:
    def test_df_vazio_retorna_df_vazio(self):
        assert variacao_por_unidade(pd.DataFrame(), "valor", "T3-2025", "T4-2025").empty

    def test_calcula_delta_entre_dois_periodos(self):
        resultado = variacao_por_unidade(_df(), "valor", "T3-2025", "T4-2025")
        row_a = resultado[resultado["unidade_sigla"] == "ICMBio-A"].iloc[0]
        assert row_a["anterior"] == 80.0
        assert row_a["atual"] == 90.0
        assert row_a["delta"] == 10.0
        assert row_a["delta_pct"] == pytest.approx(12.5)

    def test_unidade_ausente_em_um_periodo_e_excluida_por_inner_join(self):
        resultado = variacao_por_unidade(_df(), "valor", "T3-2025", "T4-2025")
        # ICMBio-C só existe em T4-2025 -> não deve aparecer (inner join)
        assert "ICMBio-C" not in resultado["unidade_sigla"].values

    def test_anterior_zero_nao_gera_divisao_por_zero(self):
        df = pd.DataFrame(
            {
                "periodo": ["T3-2025", "T4-2025"],
                "unidade_sigla": ["ICMBio-A", "ICMBio-A"],
                "valor": [0.0, 10.0],
            }
        )
        resultado = variacao_por_unidade(df, "valor", "T3-2025", "T4-2025")
        assert resultado.iloc[0]["delta_pct"] is None


class TestPctUnidadesEmFaixa:
    def test_df_vazio_retorna_zero(self):
        assert pct_unidades_em_faixa(pd.DataFrame(), "valor", "T3-2025", 0, 100) == 0.0

    def test_periodo_sem_dados_retorna_zero(self):
        assert pct_unidades_em_faixa(_df(), "valor", "PERIODO-INEXISTENTE", 0, 100) == 0.0

    def test_calcula_percentual_na_faixa(self):
        # T4-2025: valores 90, 50 (NaN descartado) -> faixa [50, 90) contém só 50 -> 50%
        resultado = pct_unidades_em_faixa(_df(), "valor", "T4-2025", 50, 90)
        assert resultado == 50.0

    def test_faixa_aberta_sem_maximo(self):
        resultado = pct_unidades_em_faixa(_df(), "valor", "T4-2025", 0)
        assert resultado == 100.0
