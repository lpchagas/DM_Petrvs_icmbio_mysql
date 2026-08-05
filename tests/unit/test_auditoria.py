"""Testes de lib/auditoria.py — checagem leve de CSVs de indicadores gerados."""
from __future__ import annotations

from pathlib import Path

import pytest

from lib.auditoria import audit_csv

pytestmark = pytest.mark.unit


def test_arquivo_inexistente(tmp_path):
    messages = audit_csv(tmp_path / "nao_existe.csv")
    assert len(messages) == 1
    assert "nao encontrado" in messages[0]


def test_csv_vazio(fixtures_dir):
    messages = audit_csv(fixtures_dir / "csv_corrompidos" / "vazio.csv")
    assert messages == ["ERRO: CSV vazio."]


def test_csv_ok_sem_alertas(fixtures_dir):
    messages = audit_csv(fixtures_dir / "csv_bons" / "ok.csv")
    joined = " ".join(messages)
    assert "Linhas de dados: 2" in joined
    assert "Colunas: 3" in joined
    assert "Estrutura CSV OK" in joined
    assert not any("ALERTA" in m for m in messages)


def test_csv_com_largura_divergente_gera_alerta(fixtures_dir):
    messages = audit_csv(fixtures_dir / "csv_corrompidos" / "largura_divergente.csv")
    joined = " ".join(messages)
    assert "ALERTA" in joined
    assert "1 linhas com quantidade de colunas divergente" in joined
