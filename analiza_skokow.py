"""
Komponent analityczny odpowiedzialny za kalkulację zmian przyrostowych (skoków)
pozycji w ujęciu ciągów chronologicznych.
"""

from __future__ import annotations
import pandas as pd

class AnalizatorSkokow:
    """Klasa transformująca serie losowań do postaci wektorów różnicowych."""

    @staticmethod
    def oblicz_skoki(df: pd.DataFrame) -> pd.DataFrame:
        """Oblicza różnicę wartości dla każdej pozycji względem poprzedniego punktu w czasie."""
        chronologiczny = df.sort_values("Numer Losowania", ascending=True).reset_index(drop=True)
        skoki = chronologiczny[[f"P{i}" for i in range(1, 7)]].diff()
        skoki.columns = [f"Skok_P{i}" for i in range(1, 7)]
        
        wynik = pd.concat([chronologiczny[["Numer Losowania"]], skoki], axis=1).iloc[1:].copy()
        for col in wynik.columns:
            wynik[col] = wynik[col].astype(int)
        return wynik.reset_index(drop=True)

    @staticmethod
    def przygotuj_przejscia(df: pd.DataFrame) -> pd.DataFrame:
        """Buduje zaawansowaną macierz przejść stanów opóźnionych dla silników wnioskowania."""
        chronologiczny = df.sort_values("Numer Losowania", ascending=True).reset_index(drop=True)
        przejscia = chronologiczny.copy()

        for i in range(1, 7):
            przejscia[f"Skok_P{i}"] = chronologiczny[f"P{i}"].diff()
            przejscia[f"Poprzednie_P{i}"] = chronologiczny[f"P{i}"].shift(1)

        przejscia["Poprzedni rozstęp"] = przejscia["Poprzednie_P6"] - przejscia["Poprzednie_P1"]
        przejscia["Bieżący rozstęp"] = przejscia["P6"] - przejscia["P1"]
        przejscia["Poprzedni numer losowania"] = chronologiczny["Numer Losowania"].shift(1)

        return przejscia.iloc[1:].reset_index(drop=True)
