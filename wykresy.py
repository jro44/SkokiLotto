"""
Moduł wizualizacji danych. Odpowiada za generowanie interaktywnych wykresów w Plotly.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

class KreatorWykresow:
    """Klasa generująca wykresy dla interfejsu Streamlit."""

    @staticmethod
    def stworz_histogram_pozycji(df: pd.DataFrame, kolumna: str) -> go.Figure:
        """Tworzy histogram rozkładu empirycznego dla danej pozycji P1-P6."""
        fig = px.histogram(
            df, 
            x=kolumna, 
            nbins=49, 
            title=f"Rozkład prawdopodobieństwa dla pozycji: {kolumna}",
            labels={kolumna: "Wylosowana Liczba", "count": "Częstość wystąpień"},
            color_discrete_sequence=["#1f77b4"]
        )
        fig.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=2), template="plotly_white")
        return fig

    @staticmethod
    def stworz_wykres_czestosci(seria_czestosc: pd.Series, tytul: str) -> go.Figure:
        """Tworzy wykres słupkowy częstości występowania poszczególnych liczb."""
        df_plot = pd.DataFrame({"Liczba": seria_czestosc.index, "Częstość": seria_czestosc.values})
        fig = px.bar(
            df_plot, 
            x="Liczba", 
            y="Częstość", 
            title=tytul,
            labels={"Liczba": "Numer liczby (1-49)", "Częstość": "Ilość trafień"},
            color="Częstość",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=2), template="plotly_white")
        return fig

    @staticmethod
    def stworz_wykres_skokow(df_skoki: pd.DataFrame, kolumna_skoku: str) -> go.Figure:
        """Tworzy liniowy wykres serii skoków w czasie (ostatnie 150 losowań)."""
        df_tail = df_skoki.tail(150)
        fig = px.line(
            df_tail, 
            x="Numer", 
            y=kolumna_skoku, 
            title=f"Przebieg przesunięć (skoków) w czasie dla: {kolumna_skoku} (Ostatnie 150 losowań)",
            labels={"Numer": "Numer Losowania", kolumna_skoku: "Wartość Skoku"},
            markers=True
        )
        fig.update_layout(template="plotly_white")
        return fig
