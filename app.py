import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import tempfile


st.set_page_config(page_title="Análisis de Activos Financieros", layout="wide")

st.title("📈 Análisis de Activos Financieros")
st.markdown("Desarrollado por **Jose Villa** — Curso: *Complementaria 2*")

# --- Entradas ---
ticker = st.text_input("Símbolo principal (Ejemplo: AAPL, BTC-USD, TSLA):", "AAPL")
compare_ticker = st.text_input("Comparar con otro activo (opcional):", "")
start_date = st.date_input("Fecha de inicio:", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Fecha final:", pd.to_datetime("2024-01-01"))
interval = st.selectbox("Frecuencia de datos:", ["1d", "1wk", "1mo"])

# --- Botón principal ---
if st.button("🔍 Analizar"):
    try:
        # --- Descargar datos principales ---
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        if data.empty:
            st.error("No se encontraron datos. Verifique el símbolo o el rango de fechas.")
            st.stop()

        precios = data["Adj Close"] if "Adj Close" in data.columns else data["Close"]
        precios = precios.dropna()

        # --- Cálculos principales ---
        data["Rendimiento"] = precios.pct_change().fillna(0)
        data["Volatilidad"] = data["Rendimiento"].rolling(20).std().fillna(0) * np.sqrt(20)
        data["MA_Corta"] = precios.rolling(10).mean().fillna(method="bfill")
        data["MA_Larga"] = precios.rolling(30).mean().fillna(method="bfill")

        # --- Señal ---
        if data["MA_Corta"].iloc[-1] > data["MA_Larga"].iloc[-1]:
            tendencia = "ALCISTA"
            color = "green"
            decision = "Comprar o mantener posiciones."
            conclusion = f"El activo **{ticker}** muestra una tendencia alcista. Se sugiere mantener o ampliar posiciones controlando el riesgo."
        elif data["MA_Corta"].iloc[-1] < data["MA_Larga"].iloc[-1]:
            tendencia = "BAJISTA"
            color = "red"
            decision = "Evitar nuevas compras y mantener liquidez."
            conclusion = f"El activo **{ticker}** presenta una tendencia bajista. Se recomienda precaución y esperar señales de recuperación."
        else:
            tendencia = "ESTABLE"
            color = "gray"
            decision = "Esperar confirmación antes de operar."
            conclusion = f"El activo **{ticker}** se mantiene estable. Conviene esperar mayor claridad en el mercado."

        st.markdown(f"### <span style='color:{color}'>📊 Tendencia {tendencia}</span>", unsafe_allow_html=True)
        st.markdown(f"**Decisión sugerida:** {decision}")

        # --- Gráfico principal ---
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(data.index, precios, label="Precio", color="blue", linewidth=2)
        ax1.plot(data.index, data["MA_Corta"], label="Media móvil 10 días", color="orange", linestyle="--")
        ax1.plot(data.index, data["MA_Larga"], label="Media móvil 30 días", color="green", linestyle="--")
        ax1.set_title(f"Evolución del activo {ticker}", fontsize=14)
        ax1.set_xlabel("Fecha")
        ax1.set_ylabel("Precio")
        ax1.legend()
        ax1.grid(True, linestyle="--", alpha=0.5)
        st.pyplot(fig1)

        # Guardar imagen del gráfico principal
        grafico_path_1 = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        fig1.savefig(grafico_path_1, dpi=150, bbox_inches="tight")

        # --- Comparación con otro activo ---
        comparacion_texto = ""
        grafico_path_2 = None
        if compare_ticker:
            comp = yf.download(compare_ticker, start=start_date, end=end_date, interval=interval)
            if not comp.empty:
                comp_precio = comp["Adj Close"] if "Adj Close" in comp.columns else comp["Close"]
                comp_precio = comp_precio.dropna()

                # 🔹 Alinear índices (para evitar error de comparación)
                combined = pd.concat([precios, comp_precio], axis=1, join="inner")
                combined.columns = [ticker, compare_ticker]

                # Normalizar base 100
                norm_principal = combined[ticker] / combined[ticker].iloc[0] * 100
                norm_comp = combined[compare_ticker] / combined[compare_ticker].iloc[0] * 100

                # Gráfico comparativo
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                ax2.plot(norm_principal.index, norm_principal, label=f"{ticker}", color="blue", linewidth=2)
                ax2.plot(norm_comp.index, norm_comp, label=f"{compare_ticker}", color="purple", linewidth=2)
                ax2.set_title(f"Comparación de rendimiento entre {ticker} y {compare_ticker}", fontsize=14)
                ax2.set_xlabel("Fecha")
                ax2.set_ylabel("Índice de rendimiento (Base 100)")
                ax2.legend()
                ax2.grid(True, linestyle="--", alpha=0.5)
                st.pyplot(fig2)

                grafico_path_2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                fig2.savefig(grafico_path_2, dpi=150, bbox_inches="tight")

                # Recomendación comparativa
                if norm_principal.iloc[-1] > norm_comp.iloc[-1]:
                    comparacion_texto = (
                        f"Durante el periodo, **{ticker}** ha tenido mejor rendimiento que **{compare_ticker}**, "
                        "lo que indica una fortaleza relativa superior. Podría mantenerse como la opción preferente."
                    )
                else:
                    comparacion_texto = (
                        f"Durante el periodo, **{compare_ticker}** ha superado a **{ticker}**, "
                        "mostrando mayor rentabilidad. Podría considerarse un activo alternativo más fuerte."
                    )

                st.info(comparacion_texto)

        # --- Métricas ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Último precio", f"${float(precios.iloc[-1]):.2f}")
        col2.metric("Volatilidad (20d)", f"{float(data['Volatilidad'].iloc[-1])*100:.2f}%")
        col3.metric("Rendimiento medio", f"{float(data['Rendimiento'].mean())*100:.2f}%")

        # --- Descargar CSV ---
        csv = data.to_csv().encode("utf-8")
        st.download_button("💾 Descargar datos históricos (CSV)", csv, file_name=f"{ticker}_analisis.csv", mime="text/csv")

        # --- PDF ---
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 750, f"Informe de Análisis Financiero - {ticker}")
        c.setFont("Helvetica", 11)
        c.drawString(50, 730, f"Periodo: {start_date} a {end_date}")
        c.drawString(50, 710, f"Tendencia: {tendencia}")
        c.drawString(50, 690, f"Decisión sugerida: {decision}")
        c.drawString(50, 670, f"Último precio: ${float(precios.iloc[-1]):.2f}")
        c.drawString(50, 650, f"Volatilidad (20 días): {float(data['Volatilidad'].iloc[-1])*100:.2f}%")
        c.drawString(50, 630, f"Rendimiento medio: {float(data['Rendimiento'].mean())*100:.2f}%")

        if grafico_path_1:
            img1 = ImageReader(grafico_path_1)
            c.drawImage(img1, 50, 360, width=500, height=250)

        if grafico_path_2:
            img2 = ImageReader(grafico_path_2)
            c.drawImage(img2, 50, 100, width=500, height=200)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 80, "Conclusión y recomendaciones:")
        c.setFont("Helvetica", 11)
        text = c.beginText(50, 60)
        text.textLines(conclusion)
        if compare_ticker and comparacion_texto:
            text.textLines("\nComparación adicional:\n" + comparacion_texto)
        c.drawText(text)

        c.showPage()
        c.save()
        pdf_buffer.seek(0)

        st.download_button("📄 Descargar informe PDF", pdf_buffer, file_name=f"Informe_{ticker}.pdf", mime="application/pdf")

        st.markdown("---")
        st.info("Este análisis tiene fines educativos y no constituye una recomendación de inversión profesional.")

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
