# ============================================================

# DASHBOARD - VISUALIZAÇÃO DO SISTEMA FINANCEIRO

# ============================================================

# Responsável por:

# - Exibir dados do sistema

# - Monitorar performance

# - Visualizar decisões do modelo

# - Acompanhar portfólio

#

# TECNOLOGIA:

# - Streamlit

# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from core.connection import fetch_dataframe

# ============================================================

# CONFIGURAÇÃO INICIAL

# ============================================================

st.set_page_config(
page_title="Agente Financeiro",
layout="wide"
)

st.title("📊 Agente Financeiro - Dashboard Inteligente")

# ============================================================

# FUNÇÕES DE DADOS

# ============================================================

@st.cache_data(ttl=30)
def carregar_patrimonio():
    query = """
    SELECT registrado_em, valor_total
    FROM patrimonio
    ORDER BY registrado_em
    """
    return fetch_dataframe(query)

@st.cache_data(ttl=30)
def carregar_portfolio():
    query = """
    SELECT p.ativo_id, a.ticker, p.quantidade, p.preco_medio
    FROM posicoes p
    JOIN ativos a ON a.id = p.ativo_id
    """
    return fetch_dataframe(query)

@st.cache_data(ttl=30)
def carregar_trades():
    query = """
    SELECT t.*, a.ticker
    FROM trades t
    JOIN ativos a ON a.id = t.ativo_id
    ORDER BY t.data_saida DESC
    LIMIT 100
    """
    return fetch_dataframe(query)

@st.cache_data(ttl=30)
def carregar_scores():
    query = """
    SELECT s.*, a.ticker
    FROM scores s
    JOIN ativos a ON a.id = s.ativo_id
    ORDER BY s.criado_em DESC
    LIMIT 100
    """
    return fetch_dataframe(query)

# ============================================================

# PATRIMÔNIO

# ============================================================

st.subheader("📈 Evolução do Patrimônio")

df_patrimonio = carregar_patrimonio()

if not df_patrimonio.empty:
    fig = px.line(
        df_patrimonio,
        x="registrado_em",
        y="valor_total",
        title="Curva de Capital"
    )
    st.plotly_chart(fig, use_container_width=True)

    valor_atual = df_patrimonio["valor_total"].iloc[-1]
    valor_inicial = df_patrimonio["valor_total"].iloc[0]

    retorno = ((valor_atual / valor_inicial) - 1) * 100

    col1, col2 = st.columns(2)
    col1.metric("💰 Patrimônio Atual", f"R$ {valor_atual:,.2f}")
    col2.metric("📊 Retorno Total", f"{retorno:.2f}%")

else:
    st.warning("Sem dados de patrimônio")

# ============================================================

# PORTFÓLIO

# ============================================================

st.subheader("💼 Carteira Atual")

df_portfolio = carregar_portfolio()

if not df_portfolio.empty:
    st.dataframe(df_portfolio, use_container_width=True)

    fig = px.pie(
        df_portfolio,
        names="ticker",
        values="quantidade",
        title="Distribuição da Carteira"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Nenhuma posição aberta")

# ============================================================

# TRADES

# ============================================================

st.subheader("🔄 Histórico de Trades")

df_trades = carregar_trades()

if not df_trades.empty:
    st.dataframe(df_trades, use_container_width=True)

    lucro_total = df_trades["lucro"].sum()
    win_rate = (df_trades["lucro"] > 0).mean() * 100

    col1, col2 = st.columns(2)
    col1.metric("💰 Lucro Total", f"R$ {lucro_total:,.2f}")
    col2.metric("🎯 Win Rate", f"{win_rate:.2f}%")

else:
    st.info("Nenhum trade realizado ainda")

# ============================================================

# SCORES

# ============================================================

st.subheader("🧠 Decisões do Modelo")

df_scores = carregar_scores()

if not df_scores.empty:
    st.dataframe(df_scores, use_container_width=True)

    fig = px.histogram(
        df_scores,
        x="score_total",
        nbins=20,
        title="Distribuição dos Scores"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Nenhum score registrado")

# ============================================================

# AUTO REFRESH

# ============================================================

st.markdown("---")
st.caption("Atualização automática a cada 30 segundos")
st.experimental_rerun()
