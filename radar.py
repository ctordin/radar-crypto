import ccxt
import pandas as pd
import streamlit as st
import time
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES DA INTERFACE E CORRETORA
# ==========================================
st.set_page_config(page_title="Radar Crypto - 10 Ativos", layout="wide")
CORRETORA = ccxt.okx()

# Atualizado: MATIC trocado por POL/USDT
LISTA_ATIVOS = [
    'SOL/USDT', 'BTC/USDT', 'ETH/USDT', 'AVAX/USDT', 'LINK/USDT',
    'ADA/USDT', 'DOGE/USDT', 'DOT/USDT', 'XRP/USDT', 'POL/USDT'
]

# ==========================================
# 2. MOTOR DE ANÁLISE (O Cérebro)
# ==========================================
def analisar_ativo(simbolo):
    try:
        velas_macro = CORRETORA.fetch_ohlcv(simbolo, '1w', limit=100)
        df_macro = pd.DataFrame(velas_macro, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_macro['sma_50'] = df_macro['close'].rolling(window=50).mean()
        tendencia_alta = df_macro.iloc[-1]['close'] > df_macro.iloc[-1]['sma_50']

        velas_micro = CORRETORA.fetch_ohlcv(simbolo, '1d', limit=100)
        df = pd.DataFrame(velas_micro, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df['sma_rapida'] = df['close'].rolling(window=9).mean()
        df['sma_lenta'] = df['close'].rolling(window=21).mean()
        
        delta = df['close'].diff()
        df['rsi'] = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean())))
        df['volume_medio'] = df['volume'].rolling(20).mean()
        df['atr'] = (df[['high', 'low']].max(axis=1) - df[['high', 'low']].min(axis=1)).rolling(14).mean()

        atual = df.iloc[-1]
        anterior = df.iloc[-2]

        cruz_alta = anterior['sma_rapida'] <= anterior['sma_lenta'] and atual['sma_rapida'] > atual['sma_lenta']
        cruz_baixa = anterior['sma_rapida'] >= anterior['sma_lenta'] and atual['sma_rapida'] < atual['sma_lenta']
        vol_ok = atual['volume'] > atual['volume_medio']
        
        recomendacao = "⚪ AGUARDAR"
        alvo = 0.0

        if tendencia_alta:
            if cruz_alta and atual['rsi'] < 60 and vol_ok:
                recomendacao = "🟢 ABRIR COMPRA (LONG)"
                alvo = atual['close'] + (atual['atr'] * 3)
            elif cruz_baixa or (anterior['rsi'] >= 70 and atual['rsi'] < 70):
                recomendacao = "🔴 FECHAR COMPRA (Lucro/Stop)"
        else:
            if (cruz_baixa or (anterior['rsi'] >= 70 and atual['rsi'] < 70)) and vol_ok:
                recomendacao = "🔴 ABRIR VENDA (SHORT)"
                alvo = atual['close'] - (atual['atr'] * 3)
            elif cruz_alta or atual['rsi'] < 30:
                recomendacao = "🟢 FECHAR SHORT (Recomprar)"

        return {
            "Ativo": simbolo,
            "Preço Atual ($)": f"{atual['close']:.4f}",
            "Macro": "ALTA" if tendencia_alta else "BAIXA",
            # CORREÇÃO: Transformando o RSI em texto (String) para não dar conflito com o "-"
            "RSI (14)": f"{atual['rsi']:.1f}", 
            "Recomendação": recomendacao,
            "Alvo TP ($)": f"{alvo:.4f}" if alvo > 0 else "-"
        }
    except Exception as e:
        return {"Ativo": simbolo, "Recomendação": "⚠️ Erro/Falta de Dados", "Preço Atual ($)": "-", "Macro": "-", "RSI (14)": "-", "Alvo TP ($)": "-"}

# ==========================================
# 3. INTERFACE VISUAL (STREAMLIT)
# ==========================================
st.title("🛰️ Radar de Oportunidades - Top 10")
st.write(f"Última varredura: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if st.button("🔄 Executar Varredura de Mercado"):
    barra_progresso = st.progress(0)
    texto_status = st.empty()
    
    resultados = []
    total_ativos = len(LISTA_ATIVOS)
    
    for i, moeda in enumerate(LISTA_ATIVOS):
        texto_status.text(f"Analisando {moeda} ({i+1}/{total_ativos})...")
        analise = analisar_ativo(moeda)
        resultados.append(analise)
        barra_progresso.progress((i + 1) / total_ativos)
        time.sleep(1)
    
    texto_status.text("✅ Varredura concluída!")
    df_resultados = pd.DataFrame(resultados)
    
    # CORREÇÃO: Usando o comando atualizado do Streamlit (width='stretch')
    st.dataframe(df_resultados, width='stretch', hide_index=True)