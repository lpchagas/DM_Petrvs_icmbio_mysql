"""Testes de lib/csv_utils.py — limpeza de valores, escrita CSV pipe-delimited."""
from __future__ import annotations

import csv

import pytest

from lib.csv_utils import (
    PROJECT_ROOT,
    artifact_month,
    clean,
    diagnostic_csv_dir,
    indicator_csv_dir,
    write_pipe_csv,
)

pytestmark = pytest.mark.unit


class TestClean:
    def test_none_retorna_default(self):
        assert clean(None) == ""
        assert clean(None, default="N/D") == "N/D"

    def test_quebras_de_linha_viram_barra(self):
        assert clean("linha1\nlinha2") == "linha1 / linha2"
        assert clean("linha1\r\nlinha2") == "linha1 / linha2"

    def test_strip_espacos(self):
        assert clean("  valor  ") == "valor"

    def test_string_vazia_apos_strip_retorna_default(self):
        assert clean("   ", default="vazio") == "vazio"

    def test_numero_vira_string(self):
        assert clean(42) == "42"
        assert clean(3.5) == "3.5"


class TestArtifactMonth:
    def test_formato_ano_mes(self):
        from datetime import date

        assert artifact_month(date(2026, 6, 15)) == "2026-06"

    def test_mes_com_um_digito_e_zero_padded(self):
        from datetime import date

        assert artifact_month(date(2026, 1, 1)) == "2026-01"


class TestDirBuilders:
    def test_indicator_csv_dir_usa_mes_explicito(self):
        path = indicator_csv_dir("2026-06")
        assert path == PROJECT_ROOT / "artefatos_local" / "ocde" / "entregas" / "2026-06"

    def test_diagnostic_csv_dir_usa_mes_explicito(self):
        path = diagnostic_csv_dir("2026-06")
        assert path == PROJECT_ROOT / "artefatos_local" / "ocde" / "diagnosticos" / "2026-06"

    def test_diretorios_sao_distintos(self):
        assert indicator_csv_dir("2026-06") != diagnostic_csv_dir("2026-06")


class TestWritePipeCsv:
    def test_round_trip_pipe_delimiter(self, tmp_path):
        target = tmp_path / "sub" / "saida.csv"
        columns = ["periodo", "unidade", "valor"]
        rows = [["T3-2025", "ICMBio-SEDE", "80"], ["T4-2025", "ICMBio-SEDE", "85"]]
        write_pipe_csv(target, columns, rows)

        assert target.exists()
        with target.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = list(csv.reader(handle, delimiter="|"))
        assert reader[0] == columns
        assert reader[1:] == rows

    def test_cria_diretorios_pai(self, tmp_path):
        target = tmp_path / "a" / "b" / "c" / "saida.csv"
        write_pipe_csv(target, ["col"], [["v"]])
        assert target.exists()

    def test_encoding_utf8_sig_grava_bom(self, tmp_path):
        target = tmp_path / "saida.csv"
        write_pipe_csv(target, ["col"], [["v"]])
        raw = target.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")

    def test_valores_sao_limpos_na_escrita(self, tmp_path):
        target = tmp_path / "saida.csv"
        write_pipe_csv(target, ["col"], [[None], ["texto\ncom quebra"]])
        with target.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = list(csv.reader(handle, delimiter="|"))
        assert reader[1] == [""]
        assert reader[2] == ["texto / com quebra"]
