"""
Graficzny silnik wizualizacji dystrybucji prawdopodobieństwa oparty o Plotly.
Zaimplementowany za pomocą niskopoziomowego graph_objects dla maksymalnej 
stabilności i kompatybilności z Plotly 6.x.
"""

from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

class KreatorWykresow:
    """Fabryka generująca interaktywne elementy wizualizacji rozkładów."""

    @staticmethod
    def wykres_czestosci(seria: pd.Series, tytul: str) -> go.Figure:
        """Tworzy słupkowy wykres rozkładu gęstości wystąpień."""
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=seria.index,
            y=seria.values,
            marker=dict(
                color=seria.values,
                colorscale="Viridis"
            ),
            name="Trafienia"
        ))
        
        fig.update_layout(
            title=tytul,
            xaxis=dict(tickmode='linear', dtick=2, title="Liczba"),
            yaxis=dict(title="Trafienia"),
            template="plotly_white",
            bargap=0.1
        )
        return fig

    @staticmethod
    def histogram_skoku(df: pd.DataFrame, kolumna: str) -> go.Figure:
        """
        Tworzy histogram rozkładu skoków różnicowych.
        Używa jawnego go.Histogram, eliminując błędy walidacji layoutu.
        """
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df[kolumna],
            marker_color="#2b5c8f",
            name=kolumna
        ))
        
        fig.update_layout(
            title=f"Gęstość rozkładu dla: {kolumna}",
            xaxis=dict(title="Wartość skoku"),
            yaxis=dict(title="Częstość"),
            template="plotly_white",
            bargap=0.1
        )
        return fig
