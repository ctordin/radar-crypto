import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Radar Crypto - Fundamentalista", layout="wide")

# Lista de ativos
CRIPTOS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ENJ-USD", "DOT-USD", 
    "DOGE-USD", "LINK-USD", "RESOLV-USD", "SAFE-USD", "XRP-USD"
]

def analisar_crypto(ticker_symbol):
    try:
        crypto = yf.Ticker(ticker_symbol)
        hist = crypto.history(period="60d")
        if hist.empty:
            return None

        info = crypto.info
        mkt_cap = info.get('marketCap', 1)
        vol_24h = info.get('volume24Hr', 0)
        circulating = info.get('circulatingSupply', 0)
        max_supply = info.get('maxSupply', 0)
        
        preco_atual = hist['Close'].iloc[-1]
        media_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        
        giro_diario = (vol_24h / mkt_cap) * 100
        liquidez_ok = giro_diario > 2.0
        
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
                motivo = "Alta Liquidez + Tokenomics Saudável + Tendência"
            else:
                status = "AGUARDAR"
                motivo = "Ativo sólido, mas tendência de curto prazo baixa"
        else:
            status = "FORA DE FILTRO"
            detalhe = "Baixa Liquidez" if not liquidez_ok else "Alta Diluição"
            motivo = f"Risco: {detalhe} (Circ: {percentual_circulante:.1f}%)"
            
        return {
            "Ativo": ticker_symbol.replace("-USD", ""),
            "Preço (USD)": round(preco_atual, 4),
            "Giro Diário (%)": round(giro_diario, 2),
            "Circulante (%)": round(percentual_circulante, 1),
            "Status": status,
            "Análise": motivo
        }
    except:
        return None

# INTERFACE VISUAL
st.title("₿ Radar Crypto Quantamental")
st.write(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if st.button('Escanear Mercado Cripto'):
    resultados = []
    with st.spinner('Consultando dados...'):
        for ticker in CRIPTOS:
            res = analisar_crypto(ticker)
            if res:
                resultados.append(res)
    
    if resultados:
        df = pd.DataFrame(resultados)
        
        # FUNÇÃO DE ESTILO CORRIGIDA (Texto visível e cores claras)
        def highlight_status(val):
            if val == 'COMPRA':
                return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold'
            elif val == 'AGUARDAR':
                return 'background-color: #fff9c4; color: #f57f17; font-weight: bold'
            elif val == 'FORA DE FILTRO':
                return 'background-color: #ffcdd2; color: #b71c1c; font-weight: bold'
            return ''

        # Exibição usando .map para Pandas atual
        st.dataframe(df.style.map(highlight_status, subset=['Status']), use_container_width=True)
    else:
        st.error("Erro ao carregar dados.")

st.sidebar.info("Critérios: Giro > 2% | Circulante > 50% | Preço > MM20")
