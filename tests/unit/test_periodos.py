"""Testes de lib/periodos.py — regra de segmentação temporal dos indicadores.

Piloto da suíte: função pura, sem I/O, sem mocks. `today` é sempre passado
explicitamente — nunca `date.today()` real — para reprodutibilidade.
"""
from __future__ import annotations

from datetime import date

import pytest

from lib.periodos import build_periods, build_periods_pe, build_periods_pt, period_metadata

pytestmark = pytest.mark.unit


def _labels(periods):
    return [p[0] for p in periods]


def _status_by_label(periods):
    return {p[0]: p[4] for p in periods}


# ---------------------------------------------------------------------------
# build_periods_pe — Plano de Entregas (trimestral 2025, quadrimestral 2026+)
# ---------------------------------------------------------------------------

class TestBuildPeriodsPe:
    def test_meio_do_t3_2025_so_traz_t3(self):
        periods = build_periods_pe(date(2025, 7, 15))
        assert _labels(periods) == ["T3-2025"]
        assert _status_by_label(periods)["T3-2025"] == "em_andamento"

    def test_fim_de_2025_t3_encerrado_t4_em_andamento(self):
        periods = build_periods_pe(date(2025, 12, 31))
        status = _status_by_label(periods)
        assert status["T3-2025"] == "encerrado"
        assert status["T4-2025"] == "em_andamento"

    def test_inicio_2026_traz_q1_em_andamento(self):
        periods = build_periods_pe(date(2026, 1, 1))
        status = _status_by_label(periods)
        assert status["Q1-2026"] == "em_andamento"
        # nenhum período de 2026 além de Q1 deve existir ainda
        assert "Q2-2026" not in status

    @pytest.mark.parametrize(
        "today, expected_status",
        [
            (date(2026, 4, 30), "em_andamento"),  # borda exata: end >= current
            (date(2026, 5, 1), "encerrado"),      # dia seguinte à borda
        ],
    )
    def test_borda_exata_de_fim_de_periodo(self, today, expected_status):
        periods = build_periods_pe(today)
        assert _status_by_label(periods)["Q1-2026"] == expected_status

    def test_transicao_q1_para_q2(self):
        periods = build_periods_pe(date(2026, 5, 1))
        status = _status_by_label(periods)
        assert status["Q1-2026"] == "encerrado"
        assert status["Q2-2026"] == "em_andamento"

    @pytest.mark.parametrize(
        "today",
        [
            date(2025, 1, 15),
            date(2025, 6, 30),
            date(2025, 7, 1),
            date(2026, 12, 31),
            date(2027, 3, 1),
        ],
    )
    def test_h1_2025_nunca_aparece(self, today):
        """T1-2025 e T2-2025 são excluídos intencionalmente em qualquer today."""
        labels = _labels(build_periods_pe(today))
        assert "T1-2025" not in labels
        assert "T2-2025" not in labels

    def test_datas_futuras_nao_sao_geradas(self):
        periods = build_periods_pe(date(2025, 7, 1))
        assert _labels(periods) == ["T3-2025"]

    def test_virada_de_ano_2026_para_2027(self):
        periods = build_periods_pe(date(2027, 1, 15))
        labels = _labels(periods)
        assert "Q3-2026" in labels
        assert "Q1-2027" in labels
        assert "Q2-2027" not in labels

    def test_alias_build_periods_e_build_periods_pe(self):
        assert build_periods is build_periods_pe


# ---------------------------------------------------------------------------
# build_periods_pt — Plano de Trabalho (trimestral 2025, mensal 2026+)
# ---------------------------------------------------------------------------

class TestBuildPeriodsPt:
    def test_meio_do_t3_2025_so_traz_t3(self):
        periods = build_periods_pt(date(2025, 8, 1))
        assert _labels(periods) == ["T3-2025"]

    @pytest.mark.parametrize(
        "today",
        [date(2025, 1, 1), date(2025, 6, 30)],
    )
    def test_h1_2025_nunca_aparece(self, today):
        labels = _labels(build_periods_pt(today))
        assert "T1-2025" not in labels
        assert "T2-2025" not in labels

    def test_janeiro_2026_gera_apenas_m01(self):
        periods = build_periods_pt(date(2026, 1, 5))
        labels = _labels(periods)
        assert "M01-2026" in labels
        assert "M02-2026" not in labels

    def test_fim_de_2026_gera_os_12_meses(self):
        periods = build_periods_pt(date(2026, 12, 31))
        labels = _labels(periods)
        for month in range(1, 13):
            assert f"M{month:02d}-2026" in labels
        assert _status_by_label(periods)["M12-2026"] == "em_andamento"

    def test_virada_de_ano_2026_para_2027(self):
        periods = build_periods_pt(date(2027, 1, 15))
        labels = _labels(periods)
        # todos os 12 meses de 2026 devem estar presentes e encerrados
        for month in range(1, 13):
            label = f"M{month:02d}-2026"
            assert label in labels
        assert _status_by_label(periods)["M12-2026"] == "encerrado"
        assert "M01-2027" in labels
        assert "M02-2027" not in labels

    @pytest.mark.parametrize(
        "today, expected_status",
        [
            (date(2026, 3, 31), "em_andamento"),  # borda exata do último dia de março
            (date(2026, 4, 1), "encerrado"),
        ],
    )
    def test_borda_exata_de_fim_de_mes(self, today, expected_status):
        periods = build_periods_pt(today)
        assert _status_by_label(periods)["M03-2026"] == expected_status


# ---------------------------------------------------------------------------
# period_metadata — contrato de colunas usado por todos os 12 scripts A1
# ---------------------------------------------------------------------------

def test_period_metadata_colunas_exatas_e_ordem():
    assert period_metadata() == [
        "ciclo_tipo",
        "periodo",
        "periodo_inicio",
        "periodo_fim",
        "periodo_status",
        "duracao_dias",
    ]
