"""insights_engine.py — Geração de insights interpretativos e recomendações em português."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .classificador import semaforo, VERDE, AMARELO, VERMELHO
from .loader import periodo_sort_key
from .metricas import MetricasPeriodo, pct_unidades_em_faixa

# ── helpers internos ─────────────────────────────────────────────────────────

def _sorted_periodos(df: pd.DataFrame) -> list[str]:
    """Retorna os rótulos de período únicos em ordem cronológica."""
    return sorted(df["periodo"].unique(), key=periodo_sort_key)


def _escopo(unidade: Optional[str]) -> str:
    """Rótulo textual do escopo dos dados: 'nacional' ou a sigla da unidade.

    Vários textos de insight/recomendação diziam "nacional" mesmo quando o
    relatório já vinha filtrado por --unidade (os números estavam corretos,
    só a palavra estava errada). Bug corrigido em 06.08.2026.
    """
    return f"em {unidade}" if unidade else "nacional"


def _enc(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    if "periodo_status" in df.columns:
        return df[df["periodo_status"] == "encerrado"]
    return df


def _ult(df: Optional[pd.DataFrame]) -> str:
    e = _enc(df)
    if e.empty or "periodo" not in e.columns:
        return ""
    return sorted(e["periodo"].unique(), key=periodo_sort_key)[-1]


def _delta_str(delta: Optional[float]) -> str:
    if delta is None:
        return ""
    if delta > 5:
        return f"▲ melhora de {delta:+.1f}% vs. período anterior"
    if delta < -5:
        return f"▼ queda de {delta:+.1f}% vs. período anterior"
    return "→ estável em relação ao período anterior"


# ── Eixo 1 — Trabalho Remoto (I01) ──────────────────────────────────────────

def insights_eixo1(
    df_v1: Optional[pd.DataFrame],
    df_v2: Optional[pd.DataFrame],
    unidade: Optional[str] = None,
) -> tuple[list[str], list[str]]:
    """Retorna (insights, recomendacoes) para o Eixo 1."""
    ins: list[str] = []
    rec: list[str] = []

    if df_v1 is None and df_v2 is None:
        return ["Dados de I01 não encontrados na pasta de entregas."], []

    enc1 = _enc(df_v1)
    enc2 = _enc(df_v2)

    # I01-v1 (proporcao_perc) é sempre um agregado nacional — sem unidade_sigla,
    # não pode ser restringido a uma unidade. Quando `unidade` está definido,
    # usar I01-v2 (já filtrado pela unidade) como fonte da distribuição por
    # modalidade, para não misturar texto "nacional" com um relatório de
    # unidade específica. Bug corrigido em 06.08.2026.
    if unidade and not enc2.empty and "modalidade" in enc2.columns \
            and "proporcao_na_unidade_perc" in enc2.columns:
        pct_col2 = "proporcao_na_unidade_perc"
        ult2 = _ult(enc2)
        if ult2:
            ult_df = enc2[enc2["periodo"] == ult2]
            pivot = ult_df.groupby("modalidade")[pct_col2].mean().sort_values(ascending=False)
            if not pivot.empty:
                dom, dom_val = pivot.index[0], pivot.iloc[0]
                ins.append(
                    f"Em **{ult2}**, a modalidade dominante em **{unidade}** é **{dom}** "
                    f"({dom_val:.1f}% dos servidores da unidade)."
                )
                if len(pivot) > 1:
                    seg, seg_val = pivot.index[1], pivot.iloc[1]
                    ins.append(f"Segunda modalidade mais frequente: **{seg}** ({seg_val:.1f}%).")

            pers = _sorted_periodos(enc2)
            if len(pers) >= 2:
                p_ini, p_fim = pers[0], pers[-1]
                for mod in enc2["modalidade"].unique():
                    v_ini = enc2[(enc2["periodo"] == p_ini) & (enc2["modalidade"] == mod)][pct_col2].mean()
                    v_fim = enc2[(enc2["periodo"] == p_fim) & (enc2["modalidade"] == mod)][pct_col2].mean()
                    if pd.notna(v_ini) and pd.notna(v_fim):
                        delta = v_fim - v_ini
                        if abs(delta) > 5:
                            sinal = "▲" if delta > 0 else "▼"
                            ins.append(
                                f"Tendência: {sinal} **{mod}** variou {delta:+.1f} pp "
                                f"entre {p_ini} e {p_fim}."
                            )
        if "total_servidores" in enc2.columns and ult2:
            tot = enc2[enc2["periodo"] == ult2]["total_servidores"].sum()
            ins.append(f"Efetivo total de **{unidade}** em **{ult2}**: **{int(tot)}** servidores.")
    else:
        ult1 = _ult(df_v1) if df_v1 is not None else ""
        pct_col = "proporcao_perc" if "proporcao_perc" in (enc1.columns if not enc1.empty else []) else "percentual"
        if not enc1.empty and ult1 and "modalidade" in enc1.columns and pct_col in enc1.columns:
            ult_df = enc1[enc1["periodo"] == ult1]
            pivot = ult_df.groupby("modalidade")[pct_col].mean().sort_values(ascending=False)
            if not pivot.empty:
                dom, dom_val = pivot.index[0], pivot.iloc[0]
                ins.append(
                    f"Em **{ult1}**, a modalidade dominante é **{dom}** "
                    f"({dom_val:.1f}% dos servidores em média nacional)."
                )
                if len(pivot) > 1:
                    seg, seg_val = pivot.index[1], pivot.iloc[1]
                    ins.append(f"Segunda modalidade mais frequente: **{seg}** ({seg_val:.1f}%).")

            # Tendência entre primeiro e último período (ordenação cronológica)
            pers = _sorted_periodos(enc1)
            if len(pers) >= 2:
                p_ini, p_fim = pers[0], pers[-1]
                for mod in enc1["modalidade"].unique():
                    v_ini = enc1[(enc1["periodo"] == p_ini) & (enc1["modalidade"] == mod)][pct_col].mean()
                    v_fim = enc1[(enc1["periodo"] == p_fim) & (enc1["modalidade"] == mod)][pct_col].mean()
                    if pd.notna(v_ini) and pd.notna(v_fim):
                        delta = v_fim - v_ini
                        if abs(delta) > 5:
                            sinal = "▲" if delta > 0 else "▼"
                            ins.append(
                                f"Tendência: {sinal} **{mod}** variou {delta:+.1f} pp "
                                f"entre {p_ini} e {p_fim}."
                            )

        if not enc2.empty and ult1 and "unidade_sigla" in enc2.columns:
            ult2_df = enc2[enc2["periodo"] == ult1] if "periodo" in enc2.columns else enc2
            total_units = ult2_df["unidade_sigla"].nunique()
            ins.append(f"Total de unidades com servidores registrados em **{ult1}**: **{total_units}**.")

    rec.append(
        "Monitorar a evolução por modalidade a cada ciclo, especialmente a proporção de trabalho "
        "presencial obrigatório nas unidades de conservação (UCs), onde o teletrabalho pleno pode "
        "ser inadequado operacionalmente."
    )
    rec.append(
        "Identificar unidades com alta rotatividade de modalidade (mudanças frequentes) para "
        "entender se refletem adequação ao cargo ou instabilidade de gestão."
    )

    return ins, rec


# ── Eixo 2 — Execução (I02, I03, I04) ───────────────────────────────────────

def insights_eixo2(
    df02: Optional[pd.DataFrame], serie02: list[MetricasPeriodo],
    df03: Optional[pd.DataFrame], serie03: list[MetricasPeriodo],
    df04: Optional[pd.DataFrame], serie04: list[MetricasPeriodo],
    unidade: Optional[str] = None,
) -> tuple[list[str], list[str]]:
    ins: list[str] = []
    rec: list[str] = []

    # I02
    if serie02:
        ult2 = serie02[-1]
        sem2 = semaforo(ult2.media, "i02")
        ins.append(
            f"**I02** — Taxa média de cumprimento em **{ult2.periodo}**: "
            f"**{ult2.media:.1f}%** (mediana {ult2.mediana:.1f}%) — {sem2}."
        )
        d = _delta_str(ult2.delta_pct)
        if d:
            ins.append(f"I02 {d}.")

        enc2 = _enc(df02)
        if not enc2.empty and "taxa_cumprimento_perc" in enc2.columns:
            n_crit = len(enc2[
                (enc2["periodo"] == ult2.periodo) &
                (enc2["taxa_cumprimento_perc"] < 60)
            ]["unidade_sigla"].unique()) if "unidade_sigla" in enc2.columns else 0
            if n_crit > 0:
                ins.append(f"⚠️ **{n_crit} unidade(s)** com taxa de cumprimento abaixo de 60% — atenção prioritária.")
            amp = ult2.maximo - ult2.minimo
            if amp > 50:
                ins.append(
                    f"Alta dispersão entre unidades: amplitude de {amp:.0f} pp "
                    f"(mín. {ult2.minimo:.1f}% — máx. {ult2.maximo:.1f}%)."
                )

    # I03
    if serie03:
        ult3 = serie03[-1]
        ins.append(
            f"**I03** — Taxa mediana de atingimento por entrega em **{ult3.periodo}**: "
            f"**{ult3.mediana:.1f}%**."
        )
        enc3 = _enc(df03)
        if not enc3.empty and "taxa_atingimento_perc" in enc3.columns:
            ult3_df = enc3[enc3["periodo"] == ult3.periodo]
            pct_acima = (ult3_df["taxa_atingimento_perc"] >= 100).mean() * 100
            ins.append(f"{pct_acima:.1f}% das entregas atingiram 100% ou mais da meta.")
            pct_baixo = (ult3_df["taxa_atingimento_perc"] < 80).mean() * 100
            if pct_baixo > 20:
                ins.append(
                    f"⚠️ {pct_baixo:.1f}% das entregas abaixo de 80% — revisar planejamento "
                    f"e/ou diagnóstico de obstáculos operacionais."
                )

    # I04
    if serie04:
        ult4 = serie04[-1]
        sem4 = semaforo(ult4.media, "i04")
        ins.append(
            f"**I04** — Score médio de atingimento em **{ult4.periodo}**: "
            f"**{ult4.media:.1f}%** — {sem4}."
        )
        d4 = _delta_str(ult4.delta_pct)
        if d4:
            ins.append(f"I04 {d4}.")
        enc4 = _enc(df04)
        if not enc4.empty and "grupo_performance" in enc4.columns:
            ult4_df = enc4[enc4["periodo"] == ult4.periodo]
            dist = ult4_df["grupo_performance"].value_counts(normalize=True) * 100
            for grp, pct in dist.items():
                if pct > 10:
                    ins.append(f"Grupo **{grp}**: {pct:.1f}% das unidades.")

    # Recomendações baseadas no semáforo principal (I02)
    sem_principal = semaforo(serie02[-1].media if serie02 else None, "i02")
    if sem_principal == VERMELHO:
        rec.append(
            f"🔴 **Execução — Ação urgente:** Taxa de cumprimento {_escopo(unidade)} abaixo de 60%. "
            "Acionar imediatamente gestores das unidades críticas para diagnóstico e revisão de metas "
            "excessivamente ambiciosas ou identificação de bloqueios operacionais."
        )
    elif sem_principal == AMARELO:
        rec.append(
            "🟡 **Execução — Monitorar:** Taxa de cumprimento entre 60–80%. Revisar metas que "
            "sistematicamente não são atingidas, verificar se há gargalos de pessoal ou orçamento, "
            "e identificar boas práticas das unidades em zona verde para replicação."
        )
    else:
        rec.append(
            "🟢 **Execução — Manter:** Execução em patamar saudável. "
            "Focar em uniformizar o desempenho das unidades com dispersão elevada e elevar o "
            "patamar das que consistentemente ficam próximas do limiar de 80%."
        )

    return ins, rec


# ── Eixo 3 — Carga de Trabalho (I05, I06, I07, I08) ─────────────────────────

def insights_eixo3(
    df05: Optional[pd.DataFrame], serie05: list[MetricasPeriodo],
    df06: Optional[pd.DataFrame],
    df07: Optional[pd.DataFrame], serie07: list[MetricasPeriodo],
    df08: Optional[pd.DataFrame], serie08: list[MetricasPeriodo],
    unidade: Optional[str] = None,
) -> tuple[list[str], list[str]]:
    ins: list[str] = []
    rec: list[str] = []

    # I05
    if serie05:
        ult5 = serie05[-1]
        ins.append(
            f"**I05** — Em **{ult5.periodo}**, cada servidor está vinculado em média a "
            f"**{ult5.media:.1f}** entregas (mediana {ult5.mediana:.1f})."
        )
        if ult5.p25 > 0 and ult5.p75 > 2 * ult5.p25:
            ins.append(
                f"Distribuição desigual de entregas: P75={ult5.p75:.1f} vs P25={ult5.p25:.1f} — "
                f"parte dos servidores assume carga muito acima da mediana da unidade."
            )

    # I06 — indicador de risco principal do Eixo 3
    media_solo: Optional[float] = None
    ult6_label = _ult(df06)
    enc6 = _enc(df06)
    if (not enc6.empty and ult6_label and
            "tamanho_grupo_responsavel" in enc6.columns and
            "pct_categoria" in enc6.columns and
            "unidade_sigla" in enc6.columns):
        ult6_df = enc6[enc6["periodo"] == ult6_label]
        solo = ult6_df[ult6_df["tamanho_grupo_responsavel"] == "1 servidor"]
        if not solo.empty:
            media_solo = solo.groupby("unidade_sigla")["pct_categoria"].mean().mean()
            sem6 = semaforo(media_solo, "i06")
            ins.append(
                f"**I06** — Em **{ult6_label}**, em média **{media_solo:.1f}%** das entregas "
                f"por unidade são de responsabilidade de 1 único servidor — {sem6}."
            )
            alta_conc = solo[solo["pct_categoria"] > 50]
            n_alta = alta_conc["unidade_sigla"].nunique()
            if n_alta > 0:
                ins.append(
                    f"⚠️ **{n_alta} unidade(s)** com mais de 50% das entregas concentradas em "
                    f"1 servidor — risco operacional significativo."
                )

    # I07
    if serie07:
        ult7 = serie07[-1]
        ins.append(
            f"**I07** — Mediana de horas planejadas por entrega em **{ult7.periodo}**: "
            f"**{ult7.mediana:.1f}h** (máx. {ult7.maximo:.1f}h, mín. {ult7.minimo:.1f}h)."
        )
        if ult7.mediana > 0 and ult7.maximo > 5 * ult7.mediana:
            ins.append(
                f"Outliers expressivos em I07: entregas com até {ult7.maximo:.0f}h "
                f"({ult7.maximo/ult7.mediana:.1f}× a mediana) — revisar escopo de entregas atípicas."
            )

    # I08
    if serie08:
        ult8 = serie08[-1]
        ins.append(
            f"**I08** — Proporção mediana de horas por entrega em **{ult8.periodo}**: "
            f"**{ult8.mediana:.1f}%** da capacidade horária disponível da unidade."
        )
        if ult8.media > 20:
            ins.append(
                "Proporção de horas elevada sugere que entregas específicas consomem parcela "
                "significativa da capacidade instalada — avaliar viabilidade do planejamento."
            )

    # Recomendações baseadas em I06 (risco principal)
    sem6_val = semaforo(media_solo, "i06")
    if sem6_val == VERMELHO:
        rec.append(
            "🔴 **Carga — Concentração crítica:** Mais de 50% das entregas dependem de "
            "1 servidor. Redistribuir responsabilidades imediatamente nas unidades críticas "
            "e criar backups operacionais para reduzir risco de paralisia."
        )
    elif sem6_val == AMARELO:
        rec.append(
            "🟡 **Carga — Atenção à concentração:** Nível intermediário de dependência "
            "individual. Fomentar colaboração e compartilhamento de responsabilidades, "
            "especialmente em unidades com histórico de alta rotatividade."
        )
    else:
        rec.append(
            "🟢 **Carga — Distribuição equilibrada:** Responsabilidades bem distribuídas. "
            "Monitorar tendência para prevenir concentração em servidores-chave."
        )
    rec.append(
        "Cruzar I05 com I07: unidades com muitas entregas por servidor E horas elevadas por "
        "entrega indicam sobrecarga real — prioridade para reforço de equipe ou revisão de escopo."
    )

    return ins, rec


# ── Eixo 4 — Desempenho e Avaliação (I09, I10, I11, I12) ────────────────────

def insights_eixo4(
    df09: Optional[pd.DataFrame], serie09: list[MetricasPeriodo],
    df10: Optional[pd.DataFrame], serie10: list[MetricasPeriodo],
    df11: Optional[pd.DataFrame], serie11: list[MetricasPeriodo],
    df12: Optional[pd.DataFrame],
    unidade: Optional[str] = None,
) -> tuple[list[str], list[str]]:
    ins: list[str] = []
    rec: list[str] = []

    escala = {1: "Não executado", 2: "Inadequado", 3: "Adequado",
              4: "Alto desempenho", 5: "Excepcional"}

    # I09
    media_i09: Optional[float] = None
    if serie09:
        ult9 = serie09[-1]
        media_i09 = ult9.media
        sem9 = semaforo(ult9.media, "i09")
        nota_ref = min(5, max(1, round(ult9.media)))
        desc = escala.get(nota_ref, "")
        ins.append(
            f"**I09** — Média {_escopo(unidade)} de avaliações de PT em **{ult9.periodo}**: "
            f"**{ult9.media:.2f}** ({desc}) — {sem9}."
        )
        d9 = _delta_str(ult9.delta_pct)
        if d9:
            ins.append(f"I09 {d9}.")

    # I10
    perc_i10: Optional[float] = None
    if serie10:
        ult10 = serie10[-1]
        perc_i10 = ult10.media
        sem10 = semaforo(ult10.media, "i10")
        ins.append(
            f"**I10** — Percentual médio de avaliações inadequadas em **{ult10.periodo}**: "
            f"**{ult10.media:.2f}%** — {sem10}."
        )
        enc10 = _enc(df10)
        if not enc10.empty and "nivel_alerta" in enc10.columns and "unidade_sigla" in enc10.columns:
            ult10_df = enc10[enc10["periodo"] == ult10.periodo]
            crit = ult10_df[ult10_df["nivel_alerta"] == "Alerta crítico"]
            n_crit = crit["unidade_sigla"].nunique()
            if n_crit > 0:
                ins.append(f"⚠️ **{n_crit} unidade(s)** em nível de alerta crítico de inadequados.")

    # I11
    if serie11:
        ult11 = serie11[-1]
        sem11 = semaforo(ult11.media, "i11")
        ins.append(
            f"**I11** — Percentual médio de excepcionais em **{ult11.periodo}**: "
            f"**{ult11.media:.2f}%** — {sem11}."
        )
        # Composição estimada do perfil de avaliações
        if serie09 and serie10 and serie11:
            exc = ult11.media
            inad = serie10[-1].media if serie10 else 0
            adeq = max(0, 100 - exc - inad)
            ins.append(
                f"Perfil estimado ICMBio (último período encerrado): "
                f"~{exc:.1f}% Excepcional | ~{adeq:.1f}% Adequado/Alto desempenho | ~{inad:.1f}% Inadequado."
            )

    # I12
    coer_pct: Optional[float] = None
    ult12_label = _ult(df12)
    enc12 = _enc(df12)
    if not enc12.empty and ult12_label and "classificacao_coerencia" in enc12.columns:
        ult12_df = enc12[enc12["periodo"] == ult12_label]
        dist = ult12_df["classificacao_coerencia"].value_counts(normalize=True) * 100
        coer_pct = dist.get("Coerente", 0.0)
        sem12 = semaforo(coer_pct, "i12")
        ins.append(
            f"**I12** — Em **{ult12_label}**, **{coer_pct:.1f}%** das unidades com avaliação "
            f"coerente entre PT e PE — {sem12}."
        )
        if "direcao_divergencia" in ult12_df.columns:
            dir_dist = ult12_df["direcao_divergencia"].value_counts(normalize=True) * 100
            pe_maior = dir_dist.get("PE>PT", 0)
            if pe_maior > 30:
                ins.append(
                    f"Padrão: PE > PT em {pe_maior:.1f}% dos casos — avaliador coletivo (PE) "
                    f"tende a ser mais generoso que a autoavaliação individual (PT)."
                )

    # Recomendações
    sem_i09 = semaforo(media_i09, "i09")
    sem_i10 = semaforo(perc_i10, "i10")
    if sem_i09 == VERMELHO or sem_i10 == VERMELHO:
        rec.append(
            "🔴 **Avaliação — Ação urgente:** Perfil de avaliações preocupante. "
            "Realizar sessões de calibração com avaliadores para alinhar critérios e "
            "identificar se há pressão por notas elevadas ou subestimação sistemática."
        )
    elif sem_i09 == AMARELO or sem_i10 == AMARELO:
        rec.append(
            "🟡 **Avaliação — Monitorar:** Avaliações em patamar intermediário. "
            "Acompanhar tendência e investigar unidades com padrão de notas atípico "
            "(outliers em I10 ou I11) para intervenção preventiva."
        )
    else:
        rec.append(
            "🟢 **Avaliação — Perfil saudável:** Avaliações dentro do padrão esperado. "
            "Manter ciclos regulares de feedback e assegurar que excepcionais (I11) "
            "sejam formalmente reconhecidos pela organização."
        )

    if coer_pct is not None and coer_pct < 70:
        rec.append(
            "🔴 **I12 — Divergência PT×PE:** Menos de 70% de coerência entre avaliações "
            "individuais e de unidade. Promover sessões de alinhamento de critérios e "
            "garantir que gestores conheçam os planos individuais dos servidores antes de avaliar."
        )

    return ins, rec


# ── Insights cruzados (multi-eixo) ───────────────────────────────────────────

def insights_cruzados(
    serie02: list[MetricasPeriodo],
    serie05: list[MetricasPeriodo],
    df06: Optional[pd.DataFrame],
    serie09: list[MetricasPeriodo],
    serie10: list[MetricasPeriodo],
    unidade: Optional[str] = None,
) -> list[str]:
    """Gera insights que cruzam múltiplos indicadores."""
    ins: list[str] = []

    # I02 × I06: baixa execução + alta concentração = risco duplo
    media_i02 = serie02[-1].media if serie02 else None
    enc6 = _enc(df06)
    ult6 = _ult(df06)
    if (media_i02 is not None and media_i02 < 70 and
            not enc6.empty and ult6 and "tamanho_grupo_responsavel" in enc6.columns and
            "pct_categoria" in enc6.columns and "unidade_sigla" in enc6.columns):
        solo = enc6[(enc6["periodo"] == ult6) & (enc6["tamanho_grupo_responsavel"] == "1 servidor")]
        if not solo.empty:
            alta_conc = solo[solo["pct_categoria"] > 50]["unidade_sigla"].unique()
            if len(alta_conc) > 0:
                ins.append(
                    f"🔴 **Risco combinado (I02 × I06):** Execução {_escopo(unidade)} abaixo de 70% "
                    f"E alta concentração de responsabilidades — {len(alta_conc)} unidade(s) "
                    f"acumulam baixo desempenho e dependência de servidor único. Prioridade máxima."
                )

    # I09 × I11: média baixa + poucos excepcionais = perfil conservador ou problema real
    media_i09 = serie09[-1].media if serie09 else None
    perc_exc = serie10[-1].media if len(serie10) > 0 else None
    if media_i09 is not None and media_i09 < 3.0:
        ins.append(
            "Combinação I09 × I10: média geral de avaliações PT abaixo de 3.0 (Adequado) "
            "sugere revisão dos critérios de avaliação ou necessidade de suporte às equipes."
        )

    # I05: alta carga → pode explicar baixa execução I02
    if serie05 and serie02:
        med_entregas = serie05[-1].mediana
        media_exec = serie02[-1].media
        if med_entregas > 8 and media_exec < 75:
            ins.append(
                f"Correlação possível I05 × I02: alta carga de entregas por servidor "
                f"(mediana {med_entregas:.1f}) pode estar contribuindo para a execução "
                f"{_escopo(unidade)} abaixo de 75% — avaliar se os planos de trabalho são realistas."
            )

    return ins
