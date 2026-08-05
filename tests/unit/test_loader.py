"""Testes de ocde/relatorios/loader.py — parsing de rótulos de período e carga de CSVs."""
from __future__ import annotations

import pandas as pd
import pytest

from ocde.relatorios.classificador import LIMIARES
from ocde.relatorios.loader import (
    _NUM,
    filter_unidade,
    load_ind,
    periodo_sort_key,
    periodos_encerrados,
    ultimo_periodo_encerrado,
    dois_ultimos_periodos,
)

pytestmark = pytest.mark.unit


class TestPeriodoSortKey:
    @pytest.mark.parametrize(
        "label, expected",
        [
            ("T1-2025", (2025, 1)),
            ("T3-2025", (2025, 7)),
            ("T4-2025", (2025, 10)),
            ("M01-2026", (2026, 1)),
            ("M12-2026", (2026, 12)),
            ("Q1-2026", (2026, 1)),
            ("Q2-2026", (2026, 5)),
            ("Q3-2026", (2026, 9)),
        ],
    )
    def test_labels_validos(self, label, expected):
        assert periodo_sort_key(label) == expected

    def test_ordena_trimestral_antes_de_quadrimestral_do_ano_seguinte(self):
        labels = ["Q1-2026", "T4-2025", "T3-2025"]
        assert sorted(labels, key=periodo_sort_key) == ["T3-2025", "T4-2025", "Q1-2026"]

    @pytest.mark.parametrize("label", ["", "malformado", "X9-2026", "M99"])
    def test_label_malformado_vai_para_o_fim(self, label):
        assert periodo_sort_key(label) == (9999, 0)


def test_todo_indicador_de_limiares_tem_colunas_numericas_no_loader():
    """Consistência cruzada classificador.LIMIARES × loader._NUM.

    Se um indicador ganha um limiar de semáforo mas não tem suas colunas
    numéricas declaradas no loader, os valores chegam como string ao
    classificador e o semáforo falha silenciosamente (comparação de string).
    """
    for ind in LIMIARES:
        chave = ind.replace("i", "")  # "i02" -> "02"
        assert chave in _NUM or any(k.startswith(chave) for k in _NUM), (
            f"Indicador {ind} tem limiar em classificador.LIMIARES mas nenhuma "
            f"entrada correspondente em loader._NUM."
        )


class TestFilterUnidade:
    def _df(self):
        return pd.DataFrame({"unidade_sigla": ["ICMBio-SEDE", "ICMBio-PARNA"], "valor": [1, 2]})

    def test_sem_unidade_retorna_df_original(self):
        df = self._df()
        assert filter_unidade(df, None) is df

    def test_filtra_por_substring_case_insensitive(self):
        resultado = filter_unidade(self._df(), "sede")
        assert list(resultado["unidade_sigla"]) == ["ICMBio-SEDE"]

    def test_unidade_nao_encontrada_retorna_dados_nacionais(self, capsys):
        resultado = filter_unidade(self._df(), "UNIDADE-INEXISTENTE")
        assert len(resultado) == 2  # fallback para o DataFrame completo
        assert "não encontrada" in capsys.readouterr().err


class TestPeriodosEncerrados:
    def test_filtra_apenas_encerrados(self):
        df = pd.DataFrame(
            {
                "periodo": ["T3-2025", "T4-2025"],
                "periodo_status": ["encerrado", "em_andamento"],
            }
        )
        resultado = periodos_encerrados(df)
        assert list(resultado["periodo"]) == ["T3-2025"]

    def test_sem_coluna_status_retorna_tudo(self):
        df = pd.DataFrame({"periodo": ["T3-2025"]})
        assert len(periodos_encerrados(df)) == 1


class TestUltimoEDoisUltimosPeriodos:
    def _df(self):
        return pd.DataFrame(
            {
                "periodo": ["T3-2025", "T4-2025", "Q1-2026"],
                "periodo_status": ["encerrado", "encerrado", "em_andamento"],
            }
        )

    def test_ultimo_periodo_encerrado(self):
        assert ultimo_periodo_encerrado(self._df()) == "T4-2025"

    def test_ultimo_periodo_encerrado_sem_dados_retorna_vazio(self):
        df = pd.DataFrame({"periodo": [], "periodo_status": []})
        assert ultimo_periodo_encerrado(df) == ""

    def test_dois_ultimos_periodos(self):
        assert dois_ultimos_periodos(self._df()) == ("T3-2025", "T4-2025")

    def test_dois_ultimos_periodos_com_um_so_periodo(self):
        df = pd.DataFrame({"periodo": ["T3-2025"], "periodo_status": ["encerrado"]})
        assert dois_ultimos_periodos(df) == ("", "T3-2025")

    def test_dois_ultimos_periodos_sem_dados(self):
        df = pd.DataFrame({"periodo": [], "periodo_status": []})
        assert dois_ultimos_periodos(df) == ("", "")


class TestLoadInd:
    def test_sem_arquivos_retorna_none(self, tmp_path):
        assert load_ind(tmp_path, "99") is None

    def test_carrega_csv_mais_recente_e_converte_colunas_numericas(self, tmp_path):
        (tmp_path / "IND_02.2_taxa_20260601_1000.csv").write_text(
            "unidade_sigla|taxa_cumprimento_perc\nICMBio-SEDE|80.5\n",
            encoding="utf-8-sig",
        )
        (tmp_path / "IND_02.2_taxa_20260701_1000.csv").write_text(
            "unidade_sigla|taxa_cumprimento_perc\nICMBio-SEDE|85.0\n",
            encoding="utf-8-sig",
        )
        df = load_ind(tmp_path, "02")
        assert df is not None
        assert len(df) == 1
        assert df["taxa_cumprimento_perc"].iloc[0] == 85.0  # pegou o arquivo mais recente (glob ordenado)
        assert pd.api.types.is_numeric_dtype(df["taxa_cumprimento_perc"])
