"""Testes de ocde/relatorios/classificador.py — semáforos e limiares por indicador."""
from __future__ import annotations

import math

import pytest

from ocde.relatorios.classificador import (
    AMARELO,
    CINZA,
    LIMIARES,
    VERDE,
    VERMELHO,
    painel_semaforo,
    semaforo,
    semaforo_eixo1,
    semaforo_eixo2,
    semaforo_eixo3,
    semaforo_eixo4,
)

pytestmark = pytest.mark.unit


class TestSemaforoNoneENan:
    def test_none_e_cinza(self):
        assert semaforo(None, "i02") == CINZA

    def test_nan_e_cinza(self):
        assert semaforo(math.nan, "i02") == CINZA

    def test_indicador_desconhecido_usa_default_80_60_maior(self):
        assert semaforo(90.0, "indicador_inexistente") == VERDE
        assert semaforo(70.0, "indicador_inexistente") == AMARELO
        assert semaforo(50.0, "indicador_inexistente") == VERMELHO


@pytest.mark.parametrize("ind", sorted(LIMIARES.keys()))
class TestSemaforoPorIndicador:
    """Testa os 3 lados do limiar de cada indicador, respeitando `maior`.

    i06 e i10 são invertidos (maior=False: valor menor é melhor) — o teste é
    parametrizado sobre TODOS os indicadores de LIMIARES para não deixar
    passar despercebido um caso invertido testado só "por simetria".
    """

    def test_lado_verde(self, ind):
        cfg = LIMIARES[ind]
        # no limiar exato (>=/<=) deve cair em VERDE
        assert semaforo(cfg["lv"], ind) == VERDE

    def test_lado_vermelho(self, ind):
        cfg = LIMIARES[ind]
        if cfg["maior"]:
            valor_ruim = cfg["la"] - 1.0
        else:
            valor_ruim = cfg["la"] + 1.0
        assert semaforo(valor_ruim, ind) == VERMELHO

    def test_lado_amarelo(self, ind):
        cfg = LIMIARES[ind]
        la, lv = cfg["la"], cfg["lv"]
        meio = (la + lv) / 2
        # só é um caso amarelo válido se meio estiver estritamente entre la e lv
        if meio in (la, lv):
            pytest.skip("Limiares adjacentes sem faixa amarela intermediária.")
        assert semaforo(meio, ind) == AMARELO


def test_i06_e_i10_sao_invertidos():
    """i06 (concentração) e i10 (% inadequado): valor MENOR é melhor."""
    assert LIMIARES["i06"]["maior"] is False
    assert LIMIARES["i10"]["maior"] is False
    # valor baixo de concentração -> verde; valor alto -> vermelho
    assert semaforo(10.0, "i06") == VERDE
    assert semaforo(80.0, "i06") == VERMELHO
    assert semaforo(2.0, "i10") == VERDE
    assert semaforo(20.0, "i10") == VERMELHO


class TestSemaforoEixo1:
    def test_sempre_informativo(self):
        assert semaforo_eixo1() == "ℹ️ Informativo"


class TestSemaforoEixo2:
    def test_pior_caso_vence_vermelho(self):
        assert semaforo_eixo2(media_i02=90.0, media_i04=10.0) == VERMELHO

    def test_pior_caso_vence_amarelo(self):
        assert semaforo_eixo2(media_i02=90.0, media_i04=70.0) == AMARELO

    def test_ambos_verdes(self):
        assert semaforo_eixo2(media_i02=90.0, media_i04=90.0) == VERDE

    def test_ambos_cinza(self):
        assert semaforo_eixo2(media_i02=None, media_i04=None) == CINZA


class TestSemaforoEixo3:
    def test_delegado_para_i06(self):
        assert semaforo_eixo3(10.0) == semaforo(10.0, "i06")
        assert semaforo_eixo3(80.0) == VERMELHO


class TestSemaforoEixo4:
    def test_pior_caso_vence_vermelho(self):
        assert semaforo_eixo4(media_i09=4.5, perc_i10=20.0, coer_i12=95.0) == VERMELHO

    def test_todos_cinza(self):
        assert semaforo_eixo4(None, None, None) == CINZA

    def test_todos_verdes(self):
        assert semaforo_eixo4(media_i09=4.0, perc_i10=2.0, coer_i12=95.0) == VERDE


def test_painel_semaforo_gera_tabela_markdown():
    tabela = painel_semaforo({"Eixo 2 — Execução": VERDE, "Eixo 4 — Avaliação": VERMELHO})
    assert "| Área | Situação |" in tabela
    assert "| Eixo 2 — Execução | 🟢 Verde |" in tabela
    assert "| Eixo 4 — Avaliação | 🔴 Vermelho |" in tabela
