"""
Moduł statystyczny agregujący i klasyfikujący rozkłady prawdopodobieństwa,
wielokrotne powtórzenia struktur oraz anomalie rozstępów maszyny losującej.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any
from utils import bezpieczny_procent

class AnalizatorStatystyczny:
    """Klasa implementująca operacje z zakresu opisowej i warunkowej analizy danych."""

    @staticmethod
    def generuj_podstawowe(df: pd.DataFrame) -> pd.DataFrame:
        """Wyznacza podstawowe charakterystyki rozkładu empirycznego dla osi pozycyjnych."""
        rekordy = []
        for i in range(1, 7):
            seria = df[f"P{i}"]
            rekordy.append({
                "Pozycja": f"P{i}",
                "Średnia": round(float(seria.mean()), 2),
                "Mediana": round(float(seria.median()), 2),
                "Odchylenie Std.": round(float(seria.std()), 2),
                "Moda": int(seria.mode()[0])
            })
        return pd.DataFrame(rekordy)

    @staticmethod
    def oblicz_czestosc_liczb(df: pd.DataFrame, zakres: int | None = None) -> pd.Series:
        """Zwraca histogram częstości występowania poszczególnych kul z puli 1-49."""
        df_target = df.head(zakres) if zakres else df
        płaska_lista = df_target[[f"P{i}" for i in range(1, 7)]].values.flatten()
        czestosc = pd.Series(płaska_lista).value_counts()
        for i in range(1, 50):
            if i not in czestosc:
                czestosc[i] = 0
        return czestosc.sort_index()

    @staticmethod
    def znajdz_pary_i_trojki(df: pd.DataFrame, top_n: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Wyszukuje i zlicza najbardziej powtarzalne kombinacje par i trójek liczbowych."""
        pary: Dict[Tuple[int, int], int] = {}
        trojki: Dict[Tuple[int, int, int], int] = {}
        
        for _, row in df[[f"P{i}" for i in range(1, 7)]].iterrows():
            liczby = sorted(list(row))
            for i in range(6):
                for j in range(i + 1, 6):
                    p = (liczby[i], liczby[j])
                    pary[p] = pary.get(p, 0) + 1
                    for k in range(j + 1, 6):
                        t = (liczby[i], liczby[j], liczby[k])
                        trojki[t] = trojki.get(t, 0) + 1

        df_pary = pd.DataFrame([{"Układ": f"{k[0]}, {k[1]}", "Częstość": v} for k, v in pary.items()])
        df_trojki = pd.DataFrame([{"Układ": f"{k[0]}, {k[1]}, {k[2]}", "Częstość": v} for k, v in trojki.items()])
        
        df_pary = df_pary.sort_values(by="Częstość", ascending=False).head(top_n).reset_index(drop=True)
        df_trojki = df_trojki.sort_values(by="Częstość", ascending=False).head(top_n).reset_index(drop=True)
        return df_pary, df_trojki

    @staticmethod
    def analizuj_stany_maszyny(przejscia: pd.DataFrame) -> Dict[str, Any]:
        """Klasyfikuje zachowania dynamiczne układu w oparciu o stany skupienia (Rozstępy)."""
        rozstepy = przejscia["Poprzedni rozstęp"]
        prog_malego = float(rozstepy.quantile(0.25))
        prog_duzego = float(rozstepy.quantile(0.75))

        kompresje = przejscia[przejscia["Poprzedni rozstęp"] >= prog_duzego]
        trafione_komp = kompresje[(kompresje["Skok_P1"] > 0) & (kompresje["Skok_P6"] < 0)]

        ekspansje = przejscia[przejscia["Poprzedni rozstęp"] <= prog_malego]
        trafione_eksp = ekspansje[(ekspansje["Skok_P1"] < 0) & (ekspansje["Skok_P6"] > 0)]

        return {
            "prog_malego": prog_malego,
            "prog_duzego": prog_duzego,
            "komp_przypadki": len(kompresje),
            "komp_trafienia": len(trafione_komp),
            "komp_proc": bezpieczny_procent(len(trafione_komp), len(kompresje)),
            "eksp_przypadki": len(ekspansje),
            "eksp_trafienia": len(trafione_eksp),
            "eksp_proc": bezpieczny_procent(len(trafione_eksp), len(ekspansje))
        }
