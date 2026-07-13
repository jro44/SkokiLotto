"""
Kompaktowy silnik klastrowania profilowego i wyszukiwania podobieństw 
strukturalnych w oparciu o wektory odległości cech złożonych.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Dict, Any
from utils import oblicz_statystyki_podstawowe

class SilnikBlizniaka:
    """Implementuje algorytm wyszukiwania najbliższych sąsiadów w przestrzeni cech losowań."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.sort_values(by="Numer Losowania", ascending=True).reset_index(drop=True)
        self.baza_cech: List[Dict[str, Any]] = []
        self._przygotuj_baze()

    def _przygotuj_baze(self) -> None:
        """Mapuje całą historię losowań na zbiór ustrukturyzowanych cech statystycznych."""
        for idx, row in self.df.iterrows():
            liczby = [int(row[f"P{i}"]) for i in range(1, 7)]
            staty = oblicz_statystyki_podstawowe(liczby)
            
            hotness = 0
            if idx > 50:
                okno = self.df.iloc[idx - 50 : idx][[f"P{i}" for i in range(1, 7)]].values.flatten()
                counts = Counter(okno)
                hotness = sum(counts.get(l, 0) for l in liczby)

            self.baza_cech.append({
                "Numer Losowania": int(row["Numer Losowania"]),
                "Liczby": liczby,
                "suma": staty["suma"],
                "rozstep": staty["rozstep"],
                "parzyste": staty["parzyste"],
                "dekady": staty["dekady"],
                "luki": staty["luki"],
                "hotness": hotness
            })

    def znajdz_najbardziej_podobne(self, docelowe_liczby: List[int], top_n: int = 10) -> List[Dict[str, Any]]:
        """Wylicza odległość metryczną próby od wzorców historycznych."""
        t_staty = oblicz_statystyki_podstawowe(docelowe_liczby)
        t_dekady = np.array(t_staty["dekady"])
        t_luki = np.array(t_staty["luki"])

        wyniki = []
        for obiekt in self.baza_cech:
            d_suma = abs(obiekt["suma"] - t_staty["suma"]) * 0.1
            d_rozstep = abs(obiekt["rozstep"] - t_staty["rozstep"]) * 0.3
            d_parzyste = abs(obiekt["parzyste"] - t_staty["parzyste"]) * 2.0
            d_dekady = float(np.sum(np.abs(np.array(obiekt["dekady"]) - t_dekady))) * 1.5
            d_luki = float(np.sum(np.abs(np.array(obiekt["luki"]) - t_luki))) * 0.8
            
            odleglosc = d_suma + d_rozstep + d_parzyste + d_dekady + d_luki
            score = round(100.0 / (1.0 + odleglosc), 2)

            wyniki.append({
                "Numer Bliźniaka": obiekt["Numer Losowania"],
                "Liczby Historyczne": str(obiekt["Liczby"]),
                "Zgodność Profilu [%]": score,
                "Suma": obiekt["suma"],
                "Rozstęp": obiekt["rozstep"]
            })

        return sorted(wyniki, key=lambda x: x["Zgodność Profilu [%]"], reverse=True)[:top_n]
