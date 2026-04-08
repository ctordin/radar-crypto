import yfinance as yf
import pandas as pd
import streamlit as st
import time
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES DA INTERFACE (B3)
# ==========================================
st.set_page_config(page_title="Radar de Ações B3", layout="wide")

# Você pode adicionar quantas ações quiser aqui, lembrando sempre do sufixo ".SA"
LISTA_ACOES = [
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'MGLU3.SA', 'MULT3.SA',
    'WEGE3.SA', 'ABEV3.SA', 'RENT3.SA', 'SUZB3.SA', 'MDNE3.SA',
    'ALOS3.SA' # <-- Sua nova ação foi adicionada aqui!
]

# ==========================================
# 2. MOTOR DE ANÁLISE (O Cérebro Adaptado para Ações)
# ==========================================
def analisar_acao(ticker):
    try:
        macro_data = yf.Ticker(ticker).history(period='2y', interval='1wk')
        if macro_data.empty: raise ValueError("Sem dados macro")
        df_macro = pd.DataFrame(macro_data)
        df_macro['sma_50'] = df_macro['Close'].rolling(window=50).mean()
        tendencia_alta = df_macro.iloc[-1]['Close'] > df_macro.iloc[-1]['sma_50']

        micro_data = yf.Ticker(ticker).history(period='1y', interval='1d')
        if micro_data.empty: raise ValueError("Sem dados micro")
        df = pd.DataFrame(micro_data)
        
        df['sma_rapida'] = df['Close'].rolling(window=9).mean()
        df['sma_lenta'] = df['Close'].rolling(window=21).mean()
        
        delta = df['Close'].diff()
        df['rsi'] = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean())))
        df['volume_medio'] = df['Volume'].rolling(20).mean()
        df['atr'] = (df[['High', 'Low']].max(axis=1) - df[['High', 'Low']].min(axis=1)).rolling(14).mean()

        atual = df.iloc[-1]
        anterior = df.iloc[-2]

        cruz_alta = anterior['sma_rapida'] <= anterior['sma_lenta'] and atual['sma_rapida'] > atual['sma_lenta']
        cruz_baixa = anterior['sma_rapida'] >= anterior['sma_lenta'] and atual['sma_rapida'] < atual['sma_lenta']
        vol_ok = atual['Volume'] > atual['volume_medio']
        
        recomendacao = "⚪ AGUARDAR"
        alvo = 0.0

        if tendencia_alta:
            if cruz_alta and atual['rsi'] < 60 and vol_ok:
                recomendacao = "🟢 ABRIR COMPRA"
                alvo = atual['Close'] + (atual['atr'] * 3)
            elif cruz_baixa or (anterior['rsi'] >= 70 and atual['rsi'] < 70):
                recomendacao = "🔴 FECHAR COMPRA (Lucro/Stop)"
        else:
            if (cruz_baixa or (anterior['rsi'] >= 70 and atual['rsi'] < 70)) and vol_ok:
                recomendacao = "🔴 ABRIR SHORT (Vendido)"
                alvo = atual['Close'] - (atual['atr'] * 3)
            elif cruz_alta or atual['rsi'] < 30:
                recomendacao = "🟢 FECHAR SHORT (Recomprar)"

        return {
            "Ativo": ticker.replace('.SA', ''), 
            "Preço (R$)": f"R$ {atual['Close']:.2f}",
            "Macro": "ALTA" if tendencia_alta else "BAIXA",
            "RSI (14)": f"{atual['rsi']:.1f}",
            "Recomendação": recomendacao,
            "Alvo TP (R$)": f"R$ {alvo:.2f}" if alvo > 0 else "-"
        }
    except Exception as e:
        return {"Ativo": ticker.replace('.SA', ''), "Recomendação": "⚠️ Erro de Leitura", "Preço (R$)": "-", "Macro": "-", "RSI (14)": "-", "Alvo TP (R$)": "-"}

# ==========================================
# 3. INTERFACE VISUAL (STREAMLIT)
# ==========================================
st.title("📈 Radar B3 - Swing Trade")
st.markdown("*(Atenção: Os sinais gerados devem ser executados manualmente no Home Broker do **C6 Invest**).*")
st.write(f"Última varredura: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if st.button("🔄 Analisar Bolsa de Valores"):
    barra_progresso = st.progress(0)
    texto_status = st.empty()
    
    resultados = []
    total_ativos = len(LISTA_ACOES)
    
    for i, acao in enumerate(LISTA_ACOES):
        texto_status.text(f"Baixando dados de {acao} ({i+1}/{total_ativos})...")
        analise = analisar_acao(acao)
        resultados.append(analise)
        barra_progresso.progress((i + 1) / total_ativos)
        time.sleep(0.5) 
    
    texto_status.text("✅ Varredura concluída!")
    df_resultados = pd.DataFrame(resultados)
    
    st.dataframe(df_resultados, width='stretch', hide_index=True)
