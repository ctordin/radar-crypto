import yfinance as yf
import pandas as pd
import streamlit as st
import time
from datetime import datetime

# Configuração da página Streamlit
st.set_page_config(page_title="Radar B3 - Quantamental", layout="wide")

# Lista dos 11 ativos para monitoramento
ATIVOS = [
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'MGLU3.SA', 'MULT3.SA',
    'WEGE3.SA', 'ABEV3.SA', 'RENT3.SA', 'SUZB3.SA', 'MDNE3.SA',
    'ALOS3.SA'
]

def analisar_ativo(ticker_symbol):
    try:
        ativo = yf.Ticker(ticker_symbol)
        hist = ativo.history(period="60d")
        if hist.empty:
            return None

        # 1. COLETA DE DADOS (Pilares 1, 2 e 4)
        info = ativo.info
        p_vp = info.get('priceToBook', 99)
        roe = info.get('returnOnEquity', 0)
        divida_patrimonio = info.get('debtToEquity', 999) 
        
        # 2. TÉCNICA
        preco_atual = hist['Close'].iloc[-1]
        media_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        
        # 3. FILTROS FUNDAMENTALISTAS (SEUS CRITÉRIOS)
        aprovado_fundamento = (p_vp < 3.0) and (roe > 0.05) and (divida_patrimonio < 150)
        
        # 4. DEFINIÇÃO DE STATUS
        if aprovado_fundamento:
            if preco_atual > media_20:
                status = "🟢 COMPRA"
                motivo = "Fundamentos OK + Tendência Alta"
            else:
                status = "🟡 AGUARDAR"
                motivo = "Ativo bom, mas preço abaixo da média"
        else:
            status = "🔴 FORA DE FILTRO"
            motivo = f"Risco: P/VP {p_vp:.1f} | ROE {roe*100:.1f}% | Dív {divida_patrimonio}%"
            
        return {
            "Ticker": ticker_symbol,
            "Preço": round(preco_atual, 2),
            "Status": status,
            "Motivo": motivo,
            "P/VP": round(p_vp, 2),
            "ROE (%)": round(roe * 100, 2)
        }
    except:
        return None

# INTERFACE STREAMLIT
st.title("🚀 Radar B3: Inteligência Quantamental")
st.subheader(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")

if st.button('Atualizar Dados Agora'):
    dados_finais = []
    
    with st.spinner('Analisando fundamentos e gráficos...'):
        for ticker in ATIVOS:
            resultado = analisar_ativo(ticker)
            if resultado:
                dados_finais.append(resultado)
    
    # Criar DataFrame para exibição
    df = pd.DataFrame(dados_finais)
    
    # Exibir métricas em destaque
    cols = st.columns(3)
    cols[0].metric("Ativos Monitorados", len(ATIVOS))
    cols[1].metric("Oportunidades de Compra", len(df[df['Status'] == "🟢 COMPRA"]))
    cols[2].metric("Setores Analisados", "Diversos")

    # Tabela principal
    st.table(df)

st.info("Configuração: P/VP < 3.0 | ROE > 5% | Dívida/Patr < 150% | Preço > Média 20")
