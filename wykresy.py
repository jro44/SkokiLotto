"""
Moduł prezentacji graficznej danych oparty o bibliotekę Plotly.
"""

from __future__ import annotations
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

class KreatorWykresow:
    """Fabryka generująca interaktywne elementy wizualizacji rozkładów."""

    @staticmethod
    def wykres_czestosci(seria: pd.Series, tytul: str) -> go.Figure:
        """Tworzy słupkowy wykres rozkładu gęstości wystąpień."""
        df_plot = pd.DataFrame({"Liczba": seria.index, "Trafienia": seria.values})
        fig = px.bar(df_plot, x="Liczba", y="Trafienia", title=tytul, color="Trafienia", color_continuous_scale="Viridis")
        fig.update_layout(xaxis=dict(tickmode='linear', dtick=2), template="plotly_white")
        return fig

    @staticmethod
    def histogram_skoku(df: pd.DataFrame, kolumna: str) -> go.Figure:
        """Tworzy histogram rozkładu skoków różnicowych."""
        fig = px.histogram(df, x=kolumna, title=f"Gęstość rozkładu dla: {kolumna}", color_discrete_sequence=["#2b5c8f"])
        fig.update_layout(template="plotly_white", bar_gap=0.1)
        return fig
