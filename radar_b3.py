import yfinance as yf
import pandas as pd
import streamlit as st
import time
from datetime import datetime

# Lista dos 11 ativos para monitoramento
ATIVOS = [
    "MGLU3.SA", "PETR4.SA", "VALE3.SA", "ITUB4.SA", 
    "ABEV3.SA", "WEGE3.SA", "BBAS3.SA", "RENT3.SA", 
    "B3SA3.SA", "HAPV3.SA", "VBBR3.SA"
]

def analisar_ativo(ticker_symbol):
    try:
        ativo = yf.Ticker(ticker_symbol)
        # Busca dados históricos para a parte técnica (últimos 60 dias)
        hist = ativo.history(period="60d")
        if hist.empty:
            return "Erro: Dados históricos não encontrados"

        # 1. COLETA DE DADOS FUNDAMENTALISTAS (Pilares 1, 2 e 4)
        info = ativo.info
        p_vp = info.get('priceToBook', 99)
        roe = info.get('returnOnEquity', 0)
        divida_patrimonio = info.get('debtToEquity', 999) # em %
        
        # 2. COLETA DE DADOS TÉCNICOS
        preco_atual = hist['Close'].iloc[-1]
        media_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        
        # 3. FILTROS DE QUALIDADE (FUNDAMENTALISTA)
        # Critérios: P/VP < 3.0 | ROE > 5% | Dívida/Patrimônio < 150%
        aprovado_fundamento = (p_vp < 3.0) and (roe > 0.05) and (divida_patrimonio < 150)
        
        # 4. LÓGICA DO RADAR
        if aprovado_fundamento:
            # Se o fundamento é bom, a técnica decide o timing
            if preco_atual > media_20:
                status = "COMPRA"
                motivo = "Fundamentos sólidos + Tendência de Alta"
            else:
                status = "AGUARDAR"
                motivo = "Bom ativo, mas aguardando reversão técnica (Preço < MM20)"
        else:
            status = "FORA DE FILTRO"
            motivo = f"Risco Fundamentalista (P/VP:{p_vp:.2f}, ROE:{roe*100:.1f}%, Dív:{divida_patrimonio}%)"
            
        return {
            "Ticker": ticker_symbol,
            "Preço": round(preco_atual, 2),
            "Status": status,
            "Motivo": motivo
        }

    except Exception as e:
        return {"Ticker": ticker_symbol, "Status": "ERRO", "Motivo": str(e)}

def executar_radar():
    print(f"{'ATIVO':<10} | {'PREÇO':<8} | {'STATUS':<15} | {'MOTIVO'}")
    print("-" * 80)
    
    resultados = []
    for ticker in ATIVOS:
        res = analisar_ativo(ticker)
        resultados.append(res)
        print(f"{res['Ticker']:<10} | {res['Preço']:<8} | {res['Status']:<15} | {res['Motivo']}")

if __name__ == "__main__":
    executar_radar()
