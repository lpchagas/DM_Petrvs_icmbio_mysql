"""metricas.py — Cálculo de métricas estatísticas por indicador e período."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from ocde.relatorios.loader import periodo_sort_key


@dataclass
class MetricasPeriodo:
    periodo: str
    n: int
    media: float
    mediana: float
    p25: float
    p75: float
    minimo: float
    maximo: float
    delta_pct: Optional[float] = None  # variação percentual da média vs. período anterior


def calcular_serie(df: pd.DataFrame, col: str) -> list[MetricasPeriodo]:
    """Série temporal de métricas por período (ordem cronológica).

    Usa `loader.periodo_sort_key` (ano, mês) — não `sorted()` puro. Rótulos
    de período (T3-2025, M01-2026, Q2-2026) não ordenam cronologicamente
    como strings: "M01-2026" < "T3-2025" alfabeticamente, mas T3-2025
    (jul/2025) é muito anterior a M01-2026 (jan/2026). O bug antigo
    invertia a linha do tempo real e distorcia os `delta_pct` calculados
    abaixo. Bug corrigido em 06.08.2026.
    """
    if df is None or df.empty or col not in df.columns or "periodo" not in df.columns:
        return []
    resultados: list[MetricasPeriodo] = []
    media_ant: Optional[float] = None
    for per in sorted(df["periodo"].unique(), key=periodo_sort_key):
        sub = df[df["periodo"] == per][col].dropna()
        if sub.empty:
            continue
        media = float(sub.mean())
        delta = (
            (media - media_ant) / abs(media_ant) * 100
            if media_ant is not None and media_ant != 0
            else None
        )
        resultados.append(MetricasPeriodo(
            periodo=per,
            n=int(sub.count()),
            media=round(media, 2),
            mediana=round(float(sub.median()), 2),
            p25=round(float(sub.quantile(0.25)), 2),
            p75=round(float(sub.quantile(0.75)), 2),
            minimo=round(float(sub.min()), 2),
            maximo=round(float(sub.max()), 2),
            delta_pct=round(delta, 1) if delta is not None else None,
        ))
        media_ant = media
    return resultados


def ranking_unidades(df: pd.DataFrame, col: str, periodo: str,
                     asc: bool = True, n: int = 10) -> pd.DataFrame:
    """Ranking das N unidades no período, ordenadas por `col`."""
    if df is None or df.empty or col not in df.columns or "unidade_sigla" not in df.columns:
        return pd.DataFrame()
    sub = df[df["periodo"] == periodo][["unidade_sigla", col]].dropna()
    # Para indicadores com múltiplas linhas por unidade (ex: I05 tem uma linha por servidor),
    # agrupa pela média para garantir uma linha por unidade no ranking.
    if sub.duplicated(subset=["unidade_sigla"]).any():
        sub = sub.groupby("unidade_sigla", as_index=False)[col].mean()
    return sub.sort_values(col, ascending=asc).head(n).reset_index(drop=True)


def variacao_por_unidade(df: pd.DataFrame, col: str,
                         per_ant: str, per_nov: str) -> pd.DataFrame:
    """Variação de `col` entre dois períodos, por unidade."""
    if df is None or df.empty or "unidade_sigla" not in df.columns:
        return pd.DataFrame()
    ant = df[df["periodo"] == per_ant][["unidade_sigla", col]].rename(columns={col: "anterior"})
    nov = df[df["periodo"] == per_nov][["unidade_sigla", col]].rename(columns={col: "atual"})
    merged = ant.merge(nov, on="unidade_sigla", how="inner")
    merged["delta"] = merged["atual"] - merged["anterior"]
    merged["delta_pct"] = merged.apply(
        lambda r: (r["delta"] / abs(r["anterior"]) * 100)
        if pd.notna(r["anterior"]) and r["anterior"] != 0 else None,
        axis=1,
    )
    return merged.sort_values("delta")


def pct_unidades_em_faixa(df: pd.DataFrame, col: str, periodo: str,
                           minimo: float, maximo: float = float("inf")) -> float:
    """% de unidades cujo valor de `col` está entre minimo (inclusive) e maximo (exclusive)."""
    if df is None or df.empty or col not in df.columns:
        return 0.0
    sub = df[df["periodo"] == periodo][col].dropna()
    if sub.empty:
        return 0.0
    return round(((sub >= minimo) & (sub < maximo)).mean() * 100, 1)
