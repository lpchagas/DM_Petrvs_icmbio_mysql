"""Testes unitários de lib/estrutura_organizacional.py — sem I/O externo, sem rede."""
from __future__ import annotations

import pytest

from lib.estrutura_organizacional import (
    NAO_MAPEADO,
    MesogrupoLookup,
    _ler_dicionario,
    _ler_estrutura,
    _normalizar,
    insert_mesogrupo_column,
    load_mesogrupo_lookup,
)

pytestmark = pytest.mark.unit


# ── Fixtures de arquivo sintéticas ──────────────────────────────────────────

ESTRUTURA_SCHEMA_LINE = '1\tListSchema={"schemaXmlList":["fake metadata row — deve ser ignorada"]}\n'

ESTRUTURA_HEADER = (
    "uorg_nome,sigla,status,uorg_nome-completo,estrut_ord,macrogrupo,mesogrupo,"
    "microgrupo,tipo,icmbio_id,id_mae,hierarquia,grupo_cnuc,grupo_ugt,ugt_nome,"
    "cargo_cod,cargo,siorg_id,siorg_nome,pontos,siorg_ord,siape_nome,siape__id,origem\n"
)


def _linha_estrutura(uorg_nome, sigla, uorg_nome_completo, mesogrupo, icmbio_id):
    campos = [
        uorg_nome, sigla, "Ativo", uorg_nome_completo, "00.00", "Sede", mesogrupo,
        "MICRO", "Coordenação", icmbio_id, "", "00", "", "", "", "", "", "",
        "", "", "", "", "", "",
    ]
    return ",".join(f'"{c}"' if c else "" for c in campos) + "\n"


@pytest.fixture
def estrutura_csv(tmp_path):
    conteudo = (
        ESTRUTURA_SCHEMA_LINE
        + ESTRUTURA_HEADER
        + _linha_estrutura("Cord. de Governança", "CGOV", "Coordenação de Governança", "Presidência", "10.0008")
        + _linha_estrutura("Cord. Territorial Belém", "CT-BELEM", "Coordenação Territorial Belém", "GR2 Sede", "22.0001")
        # Unidade de Conservação sem sigla própria — só resolvível por icmbio_id ou nome.
        + _linha_estrutura("PARNA Cabo Orange", "", "Parque Nacional do Cabo Orange", "UC na GR1", "21.0099")
    )
    caminho = tmp_path / "ICMBIO_estrutura.csv"
    caminho.write_text(conteudo, encoding="utf-8-sig")
    return caminho


@pytest.fixture
def dicionario_csv(tmp_path):
    linhas = [
        "unidade_sigla;unidade_nome;match;uorg_nome;icmbio_id",
        "CGOV;Coordenacao de Governanca;1;Coordenação de Governança;10.0008",
        "PARNACABORANGE;Parque Nacional Cabo Orange;1;Parque Nacional do Cabo Orange;21.0099",
        "UNIDADEEXTINTA;Unidade Extinta Sem Match;0;Unidades extintas;",
    ]
    caminho = tmp_path / "dicionario_petrvs_digiteca_v2.csv"
    # Encoding real do arquivo fornecido pela CGOV é cp1252 (Windows-1252).
    caminho.write_bytes(("\r\n".join(linhas) + "\r\n").encode("cp1252"))
    return caminho


# ── Parsing ──────────────────────────────────────────────────────────────────


class TestParsingArquivos:
    def test_le_estrutura_pulando_linha_de_metadado(self, estrutura_csv):
        por_id, por_sigla, por_nome = _ler_estrutura(estrutura_csv)
        assert por_sigla["CGOV"] == "Presidência"
        assert por_id["10.0008"] == "Presidência"

    def test_le_dicionario_apenas_match_1(self, dicionario_csv):
        por_sigla = _ler_dicionario(dicionario_csv)
        assert por_sigla["CGOV"] == "10.0008"
        assert "UNIDADEEXTINTA" not in por_sigla  # match=0 — descartada

    def test_arquivo_inexistente_retorna_vazio(self, tmp_path):
        por_id, por_sigla, por_nome = _ler_estrutura(tmp_path / "nao_existe.csv")
        assert por_id == {} and por_sigla == {} and por_nome == {}
        assert _ler_dicionario(tmp_path / "nao_existe.csv") == {}


# ── Resolução em cadeia (níveis 1-4) ────────────────────────────────────────


class TestResolucaoMesogrupo:
    def test_nivel1_resolve_via_dicionario_e_icmbio_id(self, estrutura_csv, dicionario_csv):
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        assert lookup.resolve("CGOV", "Coordenacao de Governanca") == "Presidência"

    def test_nivel1_resolve_unidade_de_conservacao_sem_sigla_propria(self, estrutura_csv, dicionario_csv):
        # PARNACABORANGE só existe na estrutura via icmbio_id (não tem sigla lá).
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        assert lookup.resolve("PARNACABORANGE", "Parque Nacional Cabo Orange") == "UC na GR1"

    def test_nivel2_resolve_via_sigla_direta_quando_fora_do_dicionario(self, estrutura_csv, dicionario_csv):
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        assert lookup.resolve("CT-BELEM", "Coordenacao Territorial de Belem") == "GR2 Sede"

    def test_nivel3_resolve_via_nome_quando_sigla_nao_bate_em_nada(self, estrutura_csv, dicionario_csv):
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        assert lookup.resolve("SIGLA-INEXISTENTE", "Coordenação de Governança") == "Presidência"

    def test_nivel4_nao_mapeado_quando_nada_resolve(self, estrutura_csv, dicionario_csv):
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        assert lookup.resolve("XYZ-DESCONHECIDA", "Unidade Totalmente Desconhecida") == NAO_MAPEADO

    def test_unidade_marcada_extinta_no_dicionario_fica_nao_mapeada(self, estrutura_csv, dicionario_csv):
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        assert lookup.resolve("UNIDADEEXTINTA", "Unidade Extinta Sem Match") == NAO_MAPEADO

    def test_arquivos_inexistentes_tudo_nao_mapeado_sem_excecao(self, tmp_path):
        lookup = load_mesogrupo_lookup(tmp_path / "a.csv", tmp_path / "b.csv")
        assert lookup.resolve("QUALQUER", "Qualquer Nome") == NAO_MAPEADO


# ── insert_mesogrupo_column ─────────────────────────────────────────────────


class TestInsertMesogrupoColumn:
    def test_insere_logo_apos_unidade_nome(self, estrutura_csv, dicionario_csv):
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        columns = ["periodo", "unidade_sigla", "unidade_nome", "total"]
        rows = [["T1", "CGOV", "Coordenacao de Governanca", 10]]

        new_columns, new_rows = insert_mesogrupo_column(columns, rows, lookup)

        assert new_columns == ["periodo", "unidade_sigla", "unidade_nome", "mesogrupo", "total"]
        assert new_rows == [["T1", "CGOV", "Coordenacao de Governanca", "Presidência", 10]]

    def test_no_op_quando_colunas_de_unidade_nao_existem(self, estrutura_csv, dicionario_csv):
        """Caso do CSV v1 do I01 — visão institucional, sem unidade_sigla/unidade_nome."""
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        columns = ["periodo", "modalidade", "total_servidores", "percentual"]
        rows = [["T1", "Presencial", 10, 50.0]]

        new_columns, new_rows = insert_mesogrupo_column(columns, rows, lookup)

        assert new_columns == columns
        assert new_rows == rows

    def test_unidade_nao_mapeada_recebe_marcador_explicito(self, estrutura_csv, dicionario_csv):
        lookup = load_mesogrupo_lookup(estrutura_csv, dicionario_csv)
        columns = ["unidade_sigla", "unidade_nome"]
        rows = [["DESCONHECIDA", "Unidade Desconhecida"]]

        _, new_rows = insert_mesogrupo_column(columns, rows, lookup)

        assert new_rows[0][2] == NAO_MAPEADO


# ── Normalização ─────────────────────────────────────────────────────────────


class TestNormalizar:
    def test_remove_acento_maiusculiza_e_colapsa_espacos(self):
        assert _normalizar("  Coordenação   de Governança  ") == "COORDENACAO DE GOVERNANCA"

    def test_none_ou_vazio_retorna_string_vazia(self):
        assert _normalizar(None) == ""
        assert _normalizar("") == ""
