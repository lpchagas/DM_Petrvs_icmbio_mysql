"""Testes de lib/docs_sql.py — extração e adaptação de SQL documentada em markdown.

Usa fixtures sintéticas em tests/fixtures/docs_sql_sinteticos/ — nenhum
indicador real é referenciado, para não acoplar o teste ao conteúdo de
docs/ocde/06.X.X-iXX.md (que pode mudar por razões de negócio).
"""
from __future__ import annotations

import pytest

from lib.docs_sql import (
    adapt_for_jdbc,
    extract_first_sql_block,
    extract_indicator_sql,
    extract_python_string,
    read_doc,
    set_period,
)

pytestmark = pytest.mark.unit

DOC_COM_VARIAVEL = "tests/fixtures/docs_sql_sinteticos/doc_com_variavel.md"
DOC_APENAS_BLOCO = "tests/fixtures/docs_sql_sinteticos/doc_apenas_bloco.md"


class TestExtractPythonString:
    def test_extrai_bloco_pela_variavel(self):
        markdown = read_doc(DOC_COM_VARIAVEL)
        sql = extract_python_string(markdown, "SQL_I99")
        assert "FROM unidades u" in sql
        assert "JOIN planos_entregas pe" in sql

    def test_variavel_inexistente_levanta_erro(self):
        markdown = read_doc(DOC_COM_VARIAVEL)
        with pytest.raises(ValueError):
            extract_python_string(markdown, "SQL_INEXISTENTE")


class TestExtractFirstSqlBlock:
    def test_extrai_bloco_fenced(self):
        markdown = read_doc(DOC_APENAS_BLOCO)
        sql = extract_first_sql_block(markdown)
        assert "FROM unidades u" in sql
        assert "deleted_at IS NULL" in sql

    def test_sem_bloco_fenced_levanta_erro(self):
        with pytest.raises(ValueError):
            extract_first_sql_block("texto sem sql nenhum")


class TestExtractIndicatorSql:
    def test_usa_variavel_sql_ixx_quando_existe(self):
        sql = extract_indicator_sql(DOC_COM_VARIAVEL, "99")
        assert "FROM unidades u" in sql

    def test_cai_para_bloco_fenced_quando_nao_ha_variavel(self):
        sql = extract_indicator_sql(DOC_APENAS_BLOCO, "01")
        assert "deleted_at IS NULL" in sql


class TestAdaptForJdbc:
    def test_prefixa_tabela_em_from_e_join(self):
        sql = "SELECT * FROM unidades u JOIN planos_entregas pe ON pe.unidade_id = u.id"
        adapted = adapt_for_jdbc(sql)
        assert "FROM petrvs_icmbio_unidades" in adapted
        assert "JOIN petrvs_icmbio_planos_entregas" in adapted

    def test_nao_duplica_prefixo_ja_existente(self):
        sql = "SELECT * FROM petrvs_icmbio_unidades u"
        adapted = adapt_for_jdbc(sql)
        assert adapted.count("petrvs_icmbio_petrvs_icmbio_") == 0
        assert "FROM petrvs_icmbio_unidades" in adapted

    def test_converte_date_para_cast(self):
        sql = "WHERE date(pe.data_inicio) >= data_inicio"
        adapted = adapt_for_jdbc(sql)
        assert "CAST(pe.data_inicio AS DATE)" in adapted
        assert "date(pe.data_inicio)" not in adapted.lower()

    def test_remove_json_unquote_regressao_bug_historico(self):
        """Regressão: JSON_UNQUOTE não existe no Denodo VQL (bug histórico do Eixo 4)."""
        sql = "SELECT JSON_UNQUOTE(u.nome) FROM unidades u"
        adapted = adapt_for_jdbc(sql)
        assert "JSON_UNQUOTE" not in adapted
        assert "u.nome" in adapted


class TestSetPeriod:
    def test_substitui_placeholders_ini_fim(self):
        sql = "WHERE data >= CAST('{ini}' AS DATE) AND data <= CAST('{fim}' AS DATE)"
        result = set_period(sql, "2025-07-01", "2025-09-30")
        assert "'2025-07-01'" in result
        assert "'2025-09-30'" in result
        assert "{ini}" not in result and "{fim}" not in result

    def test_substitui_literal_data_inicio_data_fim(self):
        """set_period patcha o primeiro par CAST(...) AS data_inicio/data_fim
        do bloco `parametros` — o padrão real usado nos scripts IND_XX.1_run.py."""
        sql = read_doc(DOC_COM_VARIAVEL)
        result = set_period(sql, "2026-05-01", "2026-08-31")
        assert "CAST('2026-05-01' AS DATE) AS data_inicio" in result
        assert "CAST('2026-08-31' AS DATE) AS data_fim" in result
        assert "2026-01-01" not in result
        assert "2026-04-30" not in result
