"""Lookup de mesogrupo institucional (estrutura organizacional do ICMBio).

Cruza duas planilhas mantidas pela CGOV em artefatos_local/ocde/diagnosticos/
(não versionadas — locais):

  ICMBIO_estrutura.csv
    Export do SharePoint com a estrutura organizacional completa. Peculiaridade:
    a linha 1 do arquivo é metadado de schema do SharePoint (JSON), a linha 2 é
    o cabeçalho real, e os dados começam na linha 3. Delimitador vírgula,
    encoding utf-8-sig. Colunas usadas: sigla, icmbio_id, mesogrupo.

  dicionario_petrvs_digiteca_v2.csv
    Planilha-ponte fornecida pela CGOV ligando a sigla de unidade como
    cadastrada no PETRVS ao icmbio_id oficial da estrutura ICMBio, com
    validação manual (coluna match=1). Delimitador ";", encoding cp1252
    (Windows-1252 — NÃO é utf-8). Colunas: unidade_sigla, unidade_nome, match,
    uorg_nome, icmbio_id. A v1 desta planilha usava uma numeração de
    icmbio_id divergente de ICMBIO_estrutura.csv; a v2 corrige isso — os
    valores de icmbio_id das duas planilhas já vêm no mesmo formato
    (ex. "21.0020") e podem ser cruzados diretamente.

Cadeia de resolução do mesogrupo por unidade (unidade_sigla, unidade_nome —
como aparecem nos CSVs de indicadores), na ordem:
  1. unidade_sigla -> dicionário (match == "1") -> icmbio_id -> casa com a
     coluna icmbio_id de ICMBIO_estrutura.csv -> mesogrupo.
  2. unidade_sigla -> casa direto com a coluna sigla de ICMBIO_estrutura.csv.
  3. unidade_nome -> casa com uorg_nome/uorg_nome-completo de
     ICMBIO_estrutura.csv (normalizado, sem acento) — rede de segurança para
     unidades que não estejam em nenhuma das duas planilhas-ponte.
  4. NAO_MAPEADO.

Cobertura validada (amostra real de 375 unidades de um CSV de indicador):
371/375 (98,9%) via níveis 1-2; as 4 unidades restantes estão marcadas como
extintas no dicionário (match=0, sem icmbio_id) — gap real de dados, ficam
em NAO_MAPEADO.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .csv_utils import PROJECT_ROOT

DEFAULT_ESTRUTURA_CSV = PROJECT_ROOT / "artefatos_local" / "ocde" / "diagnosticos" / "ICMBIO_estrutura.csv"
DEFAULT_DICIONARIO_CSV = PROJECT_ROOT / "artefatos_local" / "ocde" / "diagnosticos" / "dicionario_petrvs_digiteca_v2.csv"

NAO_MAPEADO = "Não mapeado"


def _normalizar(texto: str | None) -> str:
    """ASCII sem acento, maiúsculas, espaços colapsados, trim."""
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.strip().upper())


def _normalizar_id(texto: str | None) -> str:
    """Normaliza icmbio_id para comparação (trim; preserva o formato N.NNNN)."""
    return (texto or "").strip()


@dataclass
class MesogrupoLookup:
    """Índices pré-computados para resolver mesogrupo por sigla/nome de unidade."""

    dicionario_sigla_para_id: dict[str, str] = field(default_factory=dict)  # sigla normalizada -> icmbio_id
    estrutura_id_para_meso: dict[str, str] = field(default_factory=dict)  # icmbio_id -> mesogrupo
    estrutura_sigla_para_meso: dict[str, str] = field(default_factory=dict)  # sigla normalizada -> mesogrupo
    estrutura_nome_para_meso: dict[str, str] = field(default_factory=dict)  # nome normalizado -> mesogrupo

    def resolve(self, sigla: str | None, nome: str | None) -> str:
        sigla_norm = _normalizar(sigla)

        # Nível 1 — ponte via dicionário CGOV (sigla PETRVS -> icmbio_id -> mesogrupo).
        icmbio_id = self.dicionario_sigla_para_id.get(sigla_norm)
        if icmbio_id and icmbio_id in self.estrutura_id_para_meso:
            return self.estrutura_id_para_meso[icmbio_id]

        # Nível 2 — sigla direta contra ICMBIO_estrutura.csv.
        if sigla_norm and sigla_norm in self.estrutura_sigla_para_meso:
            return self.estrutura_sigla_para_meso[sigla_norm]

        # Nível 3 — nome do próprio indicador (rede de segurança).
        nome_norm = _normalizar(nome)
        if nome_norm and nome_norm in self.estrutura_nome_para_meso:
            return self.estrutura_nome_para_meso[nome_norm]

        return NAO_MAPEADO


def _ler_estrutura(caminho: Path) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Retorna (por_id, por_sigla, por_nome) a partir de ICMBIO_estrutura.csv.

    A linha 1 do arquivo é metadado de schema do export SharePoint (JSON) —
    é descartada. A linha 2 é o cabeçalho real.
    """
    if not caminho.exists():
        return {}, {}, {}

    with caminho.open(encoding="utf-8-sig", errors="replace") as arquivo:
        linhas = arquivo.readlines()
    if len(linhas) < 2:
        return {}, {}, {}

    leitor = csv.reader(linhas[1:])
    cabecalho = next(leitor, None)
    if not cabecalho:
        return {}, {}, {}
    try:
        idx_sigla = cabecalho.index("sigla")
        idx_id = cabecalho.index("icmbio_id")
        idx_nome = cabecalho.index("uorg_nome")
        idx_nome_completo = cabecalho.index("uorg_nome-completo")
        idx_meso = cabecalho.index("mesogrupo")
    except ValueError:
        return {}, {}, {}

    por_id: dict[str, str] = {}
    por_sigla: dict[str, str] = {}
    por_nome: dict[str, str] = {}
    largura_minima = max(idx_sigla, idx_id, idx_nome, idx_nome_completo, idx_meso) + 1
    for linha in leitor:
        if len(linha) < largura_minima:
            continue
        mesogrupo = linha[idx_meso].strip()
        if not mesogrupo:
            continue
        id_norm = _normalizar_id(linha[idx_id])
        if id_norm and id_norm not in por_id:
            por_id[id_norm] = mesogrupo
        sigla_norm = _normalizar(linha[idx_sigla])
        if sigla_norm and sigla_norm not in por_sigla:
            por_sigla[sigla_norm] = mesogrupo
        for texto_nome in (linha[idx_nome], linha[idx_nome_completo]):
            chave = _normalizar(texto_nome)
            if chave and chave not in por_nome:
                por_nome[chave] = mesogrupo
    return por_id, por_sigla, por_nome


def _ler_dicionario(caminho: Path) -> dict[str, str]:
    """Retorna {sigla PETRVS normalizada -> icmbio_id} a partir de
    dicionario_petrvs_digiteca_v2.csv (apenas linhas com match == '1').

    Encoding cp1252 (Windows-1252) — confirmado pelos bytes do arquivo
    (ex. 0xC1 = 'Á'); abrir como utf-8 lança UnicodeDecodeError.
    """
    if not caminho.exists():
        return {}

    with caminho.open(encoding="cp1252", errors="replace", newline="") as arquivo:
        leitor = csv.reader(arquivo, delimiter=";")
        cabecalho = next(leitor, None)
        if not cabecalho:
            return {}
        try:
            idx_sigla = cabecalho.index("unidade_sigla")
            idx_match = cabecalho.index("match")
            idx_id = cabecalho.index("icmbio_id")
        except ValueError:
            return {}

        por_sigla: dict[str, str] = {}
        largura_minima = max(idx_sigla, idx_match, idx_id) + 1
        for linha in leitor:
            if len(linha) < largura_minima:
                continue
            if linha[idx_match].strip() != "1":
                continue
            sigla_norm = _normalizar(linha[idx_sigla])
            icmbio_id = _normalizar_id(linha[idx_id])
            if sigla_norm and icmbio_id:
                por_sigla[sigla_norm] = icmbio_id
    return por_sigla


def load_mesogrupo_lookup(
    estrutura_csv: Path | None = None,
    dicionario_csv: Path | None = None,
) -> MesogrupoLookup:
    """Carrega e cruza as duas planilhas de estrutura organizacional.

    Se algum arquivo não existir (ambiente sem acesso à pasta local privada),
    o lookup correspondente fica vazio — os scripts A1 continuam rodando
    normalmente, apenas com mesogrupo='Não mapeado' em todas as linhas.
    """
    estrutura_por_id, estrutura_por_sigla, estrutura_por_nome = _ler_estrutura(
        estrutura_csv or DEFAULT_ESTRUTURA_CSV
    )
    dicionario_sigla_para_id = _ler_dicionario(dicionario_csv or DEFAULT_DICIONARIO_CSV)
    return MesogrupoLookup(
        dicionario_sigla_para_id=dicionario_sigla_para_id,
        estrutura_id_para_meso=estrutura_por_id,
        estrutura_sigla_para_meso=estrutura_por_sigla,
        estrutura_nome_para_meso=estrutura_por_nome,
    )


def insert_mesogrupo_column(
    columns: list[str],
    rows: list[list],
    lookup: MesogrupoLookup,
    sigla_col: str = "unidade_sigla",
    nome_col: str = "unidade_nome",
) -> tuple[list[str], list[list]]:
    """Insere a coluna 'mesogrupo' logo após nome_col.

    No-op defensivo: se sigla_col ou nome_col não existirem em columns (caso
    do CSV v1 do I01, que não tem colunas de unidade), retorna columns/rows
    inalterados.
    """
    if sigla_col not in columns or nome_col not in columns:
        return columns, rows

    idx_sigla = columns.index(sigla_col)
    idx_nome = columns.index(nome_col)
    posicao = idx_nome + 1

    novas_columns = columns[:posicao] + ["mesogrupo"] + columns[posicao:]
    novas_rows = []
    for linha in rows:
        sigla = linha[idx_sigla] if idx_sigla < len(linha) else ""
        nome = linha[idx_nome] if idx_nome < len(linha) else ""
        mesogrupo = lookup.resolve(sigla, nome)
        novas_rows.append(linha[:posicao] + [mesogrupo] + linha[posicao:])
    return novas_columns, novas_rows
