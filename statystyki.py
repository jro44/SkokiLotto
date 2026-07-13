"""
Moduł zaawansowanych obliczeń statystycznych dla całego zbioru oraz poszczególnych liczb.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List
from utils import pobierz_logger

logger = pobierz_logger("Statystyki")

class AnalizatorStatystyczny:
    """Klasa generująca rozbudowane statystyki matematyczne bazy losowań."""

    @staticmethod
    def generuj_podstawowe(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Oblicza średnie, mediany, odchylenia standardowe oraz mody dla pozycji P1-P6."""
        metryki = {}
        for col in [f"P{i}" for i in range(1, 7)]:
            try:
                moda_res = stats.mode(df[col], keepdims=True)
                moda_val = int(moda_res.mode[0]) if len(moda_res.mode) > 0 else int(df[col].mode()[0])
            except Exception:
                moda_val = int(df[col].mode()[0])

            metryki[col] = {
                "Srednia": float(df[col].mean()),
                "Mediana": float(df[col].median()),
                "Odchylenie": float(df[col].std()),
                "Moda": moda_val
            }
        return metryki

    @staticmethod
    def oblicz_czestosc_liczb(df: pd.DataFrame, zakres_ostatnich: int = None) -> pd.Series:
        """Zwraca częstość występowania wszystkich liczb 1-49 w zadanym zakresie."""
        df_zakres = df.tail(zakres_ostatnich) if zakres_ostatnich else df
        wszystkie_liczby = df_zakres[[f"P{i}" for i in range(1, 7)]].values.flatten()
        czestosc = pd.Series(wszystkie_liczby).value_counts()
        
        # Dołączenie liczb, które mogły nie paść ani razu w wybranym oknie
        for i in range(1, 50):
            if i not in czestosc:
                czestosc[i] = 0
                
        return czestosc.sort_index()

    @staticmethod
    def znajdz_pary_i_trojki(df: pd.DataFrame, top_n: int = 10) -> tuple:
        """Identyfikuje najczęściej występujące pary i trójki liczb."""
        logger.info("Szukanie najczęstszych par i trójek liczb.")
        pary: Dict[tuple, int] = {}
        trojki: Dict[tuple, int] = {}

        for _, row in df[[f"P{i}" for i in range(1, 7)]].iterrows():
            liczby = sorted(list(row))
            # Pary
            for i in range(6):
                for j in range(i + 1, 6):
                    p = (liczby[i], liczby[j])
                    pary[p] = pary.get(p, 0) + 1
            # Trójki
            for i in range(6):
                for j in range(i + 1, 6):
                    for k in range(j + 1, 6):
                        t = (liczby[i], liczby[j], liczby[k])
                        trojki[t] = trojki.get(t, 0) + 1

        df_pary = pd.DataFrame([{"Para": f"{k[0]}, {k[1]}", "Czestosc": v} for k, v in pary.items()])
        df_trojki = pd.DataFrame([{"Trojka": f"{k[0]}, {k[1]}, {k[2]}", "Czestosc": v} for k, v in trojki.items()])

        df_pary = df_pary.sort_values(by="Czestosc", ascending=False).财务_head = df_pary.head(top_n).reset_index(drop=True)
        df_trojki = df_trojki.sort_values(by="Czestosc", ascending=False).head(top_n).reset_index(drop=True)

        return df_pary, df_trojki

    @staticmethod
    def analizuj_stany_maszyny(df: pd.DataFrame) -> pd.DataFrame:
        """
        Klasyfikuje stan maszyny losującej na bazie rozstępu liczb:
        - Kompresja: Rozstęp <= 25 (Liczby skupione)
        - Ekspansja: Rozstęp >= 40 (Liczby mocno rozproszone)
        - Wahadło: 25 < Rozstęp < 40 (Układ zrównoważony)
        """
        stany = []
        for _, row in df.iterrows():
            liczby = [row[f"P{i}"] for i in range(1, 7)]
            rozstep = max(liczby) - min(liczby)
            
            if rozstep <= 25:
                stan = "Kompresja"
            elif rozstep >= 40:
                stan = "Ekspansja"
            else:
                stan = "Wahadło"
            stany.append({"Numer": row["Numer"], "Rozstep": rozstep, "Stan": stan})
            
        return pd.DataFrame(stany)
