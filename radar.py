import pandas as pd
import streamlit as st
import requests
from datetime import datetime
import time

st.set_page_config(page_title="Radar Crypto OKX", layout="wide")

# Lista de pares na OKX (formato Instrument ID)
CRIPTOS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "ADA-USDT", "DOT-USDT", "LINK-USDT", "AVAX-USDT", "NEAR-USDT"]

def get_okx_data(instId):
    try:
        # Puxando Ticker (Preço e Volume 24h)
        url_ticker = f"https://www.okx.com/api/v5/market/ticker?instId={instId}"
        res = requests.get(url_ticker).json()
        
        if res['code'] != '0': return None
        data = res['data'][0]
        
        last_price = float(data['last'])
        vol_24h = float(data['vol24h']) * last_price # Volume em USDT
        
        # Puxando Histórico (Candles de 1 dia para Média Móvel)
        url_history = f"https://www.okx.com/api/v5/market/candles?instId={instId}&bar=1D&limit=20"
        res_h = requests.get(url_history).json()
        
        if res_h['code'] == '0':
            candles = res_h['data']
            precos_fechamento = [float(c[4]) for c in candles]
            media_20 = sum(precos_fechamento) / len(precos_fechamento)
        else:
            media_20 = last_price

        # Filtro de Liquidez (Mínimo 5M USDT de volume diário para Altcoins)
        liquidez_ok = vol_24h > 5000000 
        
        if last_price > media_20 and liquidez_ok:
            status = "COMPRA"
            motivo = "Tendência Alta + Alta Liquidez"
        elif liquidez_ok:
            status = "AGUARDAR"
            motivo = "Abaixo da Média (Aguardar Reversão)"
        else:
            status = "FORA DE FILTRO"
            motivo = "Baixa Liquidez na Exchange"

        return {
            "Ativo": instId.replace("-USDT", ""),
            "Preço (USDT)": last_price,
            "Volume 24h": f"{vol_24h/1e6:.1f}M",
            "Status": status,
            "Análise": motivo
        }
    except Exception as e:
        return {"Ativo": instId, "Status": "ERRO", "Análise": str(e)}

# INTERFACE
st.title("₿ Radar Crypto via OKX API")
st.caption("Conexão direta com a Exchange - Sem limites de requisição do Yahoo")

if st.button('Escanear OKX'):
    resultados = []
    progresso = st.progress(0)
    
    for i, inst in enumerate(CRIPTOS):
        res = get_okx_data(inst)
        if res: resultados.append(res)
        time.sleep(0.2) # Delay mínimo apenas por segurança
        progresso.progress((i + 1) / len(CRIPTOS))
    
    df = pd.DataFrame(resultados)
    
    def highlight(val):
        if val == 'COMPRA': return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold'
        if val == 'AGUARDAR': return 'background-color: #fff9c4; color: #f57f17; font-weight: bold'
        return ''

    st.dataframe(df.style.map(highlight, subset=['Status']), use_container_width=True)
