"""
Moduł zaawansowanych obliczeń statystycznych dla całego zbioru oraz poszczególnych liczb.
Zabezpieczony przed błędami braku indeksów kolumn w strukturach danych.
"""

from __future__ import annotations
import pandas as pd
from typing import Dict, Any

class AnalizatorStatystyczny:
    """Klasa generująca rozbudowane statystyki matematyczne bazy losowań."""

    @staticmethod
    def generuj_podstawowe(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Oblicza średnie, mediany, odchylenia standardowe oraz mody dla pozycji P1-P6."""
        metryki = {}
        for col in [f"P{i}" for i in range(1, 7)]:
            metryki[col] = {
                "Srednia": round(float(df[col].mean()), 2),
                "Mediana": round(float(df[col].median()), 2),
                "Odchylenie": round(float(df[col].std()), 2),
                "Moda": int(df[col].mode()[0])
            }
        return metryki

    @staticmethod
    def oblicz_czestosc_liczb(df: pd.DataFrame, zakres_ostatnich: int = None) -> pd.Series:
        """Zwraca częstość występowania wszystkich liczb 1-49 w zadanym zakresie."""
        df_zakres = df.head(zakres_ostatnich) if zakres_ostatnich else df
        wszystkie_liczby = df_zakres[[f"P{i}" for i in range(1, 7)]].values.flatten()
        czestosc = pd.Series(wszystkie_liczby).value_counts()
        
        for i in range(1, 50):
            if i not in czestosc:
                czestosc[i] = 0
                
        return czestosc.sort_index()

    @staticmethod
    def znajdz_pary_i_trojki(df: pd.DataFrame, top_n: int = 10) -> tuple:
        """Identyfikuje najczęściej występujące pary i trójki liczb."""
        pary = {}
        trojki = {}

        for _, row in df[[f"P{i}" for i in range(1, 7)]].iterrows():
            liczby = sorted(list(row))
            for i in range(6):
                for j in range(i + 1, 6):
                    p = (liczby[i], liczby[j])
                    pary[p] = pary.get(p, 0) + 1
                    for k in range(j + 1, 6):
                        t = (liczby[i], liczby[j], liczby[k])
                        trojki[t] = trojki.get(t, 0) + 1

        df_pary = pd.DataFrame([{"Układ": f"{k[0]}, {k[1]}", "Czestosc": v} for k, v in pary.items()])
        df_trojki = pd.DataFrame([{"Układ": f"{k[0]}, {k[1]}, {k[2]}", "Czestosc": v} for k, v in trojki.items()])

        df_pary = df_pary.sort_values(by="Czestosc", ascending=False).head(top_n).reset_index(drop=True)
        df_trojki = df_trojki.sort_values(by="Czestosc", ascending=False).head(top_n).reset_index(drop=True)

        return df_pary, df_trojki

    @staticmethod
    def analizuj_stany_maszyny(df: pd.DataFrame) -> pd.DataFrame:
        """
        Klasyfikuje zachowania dynamiczne układu w oparciu o rozstępy liczb.
        Bezpiecznie przyjmuje surowy DataFrame i wylicza cechy lokalnie.
        """
        stany = []
        for _, row in df.iterrows():
            liczby = [int(row[f"P{i}"]) for i in range(1, 7)]
            rozstep = max(liczby) - min(liczby)
            
            if rozstep <= 25:
                stan = "Kompresja"
            elif rozstep >= 40:
                stan = "Ekspansja"
            else:
                stan = "Wahadło"
            stany.append({
                "Numer": int(row["Numer Losowania"]), 
                "Rozstęp (Max-Min)": rozstep, 
                "Zidentyfikowany Stan": stan
            })
            
        return pd.DataFrame(stany)
