"""
Generator predykcji probabilistycznych i ekstrapolacji trendów
przy użyciu korekt wahadłowych oraz rozkładów warunkowych.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

class GeneratorPredykcji:
    """Klasa implementująca algorytmy predykcyjne oparte o analizę przesunięć."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.PROG = 10

    def generuj_zestaw_skokow(self, przejscia: pd.DataFrame, stany: Dict[str, Any]) -> Tuple[List[int], List[int]]:
        """Generuje predykcję na podstawie ważonego prawdopodobieństwa wystąpienia skoku."""
        najnowszy = self.df.sort_values("Numer Losowania", ascending=False).iloc[0]
        liczby_ostatnie = [int(najnowszy[f"P{i}"]) for i in range(1, 7)]
        rozstep_ostatni = liczby_ostatnie[-1] - liczby_ostatnie[0]

        stan = "Neutralny"
        if rozstep_ostatni >= stany["prog_duzego"]: 
            stan = "Kompresja"
        elif rozstep_ostatni <= stany["prog_malego"]: 
            stan = "Ekspansja"

        ostatnie_skoki = przejscia.sort_values("Numer Losowania", ascending=True).iloc[-1]
        przewidywane_skoki = []

        for i in range(1, 7):
            wszystkie = przejscia[f"Skok_P{i}"]
            ostatni_skok = int(ostatnie_skoki[f"Skok_P{i}"])
            
            p_wszystkie = wszystkie.value_counts(normalize=True)
            punkty = {int(k): float(v) * 0.5 for k, v in p_wszystkie.items()}

            if abs(ostatni_skok) > self.PROG:
                maska = (przejscia[f"Skok_P{i}"].shift(1).abs() > self.PROG) & (np.sign(przejscia[f"Skok_P{i}"]) == -np.sign(ostatni_skok))
                korekty = przejscia.loc[maska, f"Skok_P{i}"].value_counts(normalize=True)
                for k, v in korekty.items():
                    punkty[int(k)] = punkty.get(int(k), 0.0) + (float(v) * 0.5)

            best_skok = sorted(punkty.items(), key=lambda x: -x[1])[0][0]
            przewidywane_skoki.append(best_skok)

        kandydaci = [liczby_ostatnie[idx] + przewidywane_skoki[idx] for idx in range(6)]
        return self.dopasuj_zakres(kandydaci), przewidywane_skoki

    def generuj_zestaw_blizniakow(self, silnik: Any) -> List[int]:
        """Wyznacza rekomendację na bazie rozkładu następstw najbliższych profilowo bliźniaków."""
        najnowszy = self.df.sort_values("Numer Losowania", ascending=False).iloc[0]
        liczby_ost = [int(najnowszy[f"P{i}"]) for i in range(1, 7)]
        
        blizniacy = silnik.znajdz_najbardziej_podobne(liczby_ost, top_n=5)
        pula = []
        for b in blizniacy:
            wiersz_nast = self.df[self.df["Numer Losowania"] == b["Numer Bliźniaka"] + 1]
            if not wiersz_nast.empty:
                pula.extend([int(wiersz_nast.iloc[0][f"P{i}"]) for i in range(1, 7)])

        if len(set(pula)) >= 6:
            return sorted(list(pd.Series(pula).value_counts().head(6).index))
        return sorted(list(range(1, 7)))

    def dopasuj_zakres(self, kandydaci: List[int]) -> List[int]:
        """Porządkuje i wymusza unikalność oraz poprawność matematyczną zakresu 1-49 dla pozycji."""
        wynik = np.array(kandydaci, dtype=int)
        for i in range(6):
            wynik[i] = int(np.clip(wynik[i], 1 + i, 49 - (5 - i)))
        for _ in range(3):
            for i in range(1, 6): 
                wynik[i] = max(wynik[i], wynik[i - 1] + 1)
            for i in range(4, -1, -1): 
                wynik[i] = min(wynik[i], wynik[i + 1] - 1)
        return [int(x) for x in wynik]
