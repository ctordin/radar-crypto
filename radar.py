import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Radar Crypto - Master", layout="wide")

# Lista ajustada para maior estabilidade no yfinance
CRIPTOS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOT-USD", 
    "LINK-USD", "AVAX-USD", "NEAR-USD"
]

def analisar_crypto(ticker_symbol):
    try:
        crypto = yf.Ticker(ticker_symbol)
        # Aumentamos o período para garantir que a média móvel seja calculada
        hist = crypto.history(period="90d")
        
        if hist.empty or len(hist) < 20:
            return {"Ativo": ticker_symbol, "Status": "ERRO", "Análise": "Sem histórico suficiente"}

        info = crypto.info
        # Usamos .get(key, default) para evitar que o código quebre se o dado sumir
        mkt_cap = info.get('marketCap', 1)
        vol_24h = info.get('volume24Hr', info.get('volume', 0))
        circulating = info.get('circulatingSupply', 0)
        max_supply = info.get('maxSupply', 0)
        
        preco_atual = hist['Close'].iloc[-1]
        media_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        
        # Cálculo de Liquidez
        giro_diario = (vol_24h / mkt_cap) * 100 if mkt_cap > 1 else 0
        liquidez_ok = giro_diario > 2.0
        
        # Cálculo de Diluição
        if max_supply and max_supply > 0:
            percentual_circulante = (circulating / max_supply) * 100
            diluicao_ok = percentual_circulante > 50.0
        else:
            percentual_circulante = 100.0
            diluicao_ok = True

        fundamentos_ok = liquidez_ok and diluicao_ok
        
        if fundamentos_ok:
            if preco_atual > media_20:
                status = "COMPRA"
                motivo = "Fundamentos OK + Tendência Alta"
            else:
                status = "AGUARDAR"
                motivo = "Abaixo da Média de 20 dias"
        else:
            status = "FORA DE FILTRO"
            detalhe = "Baixa Liquidez" if not liquidez_ok else "Alta Diluição"
            motivo = f"Risco: {detalhe} ({percentual_circulante:.1f}%)"
            
        return {
            "Ativo": ticker_symbol.replace("-USD", ""),
            "Preço (USD)": round(preco_atual, 4),
            "Giro (%)": round(giro_diario, 2),
            "Circ. (%)": round(percentual_circulante, 1),
            "Status": status,
            "Análise": motivo
        }
    except Exception as e:
        return {"Ativo": ticker_symbol, "Status": "ERRO", "Análise": f"Falha na API: {str(e)}"}

# INTERFACE
st.title("₿ Radar Crypto Quantamental")

if st.button('Executar Scanner de Mercado'):
    resultados = []
    progresso = st.progress(0)
    
    for i, ticker in enumerate(CRIPTOS):
        res = analisar_crypto(ticker)
        if res:
            resultados.append(res)
        progresso.progress((i + 1) / len(CRIPTOS))
    
    if resultados:
        df = pd.DataFrame(resultados)
        
        def highlight_status(val):
            if val == 'COMPRA': return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold'
            if val == 'AGUARDAR': return 'background-color: #fff9c4; color: #f57f17; font-weight: bold'
            if val == 'FORA DE FILTRO': return 'background-color: #ffcdd2; color: #b71c1c; font-weight: bold'
            return ''

        st.dataframe(df.style.map(highlight_status, subset=['Status']), use_container_width=True)
    else:
        st.warning("A API do Yahoo retornou vazio. Tente novamente em alguns segundos.")

st.sidebar.caption(f"Último Check: {datetime.now().strftime('%H:%M:%S')}")
