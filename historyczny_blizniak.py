"""
Silnik profilowego podobieństwa losowań (Historyczny Bliźniak) dla Lotto 6/49.
Oblicza odległości cech skumulowanych i wyszukuje identyczne lub najbardziej zbliżone stany z przeszłości.
"""

from __future__ import annotations
from collections import Counter
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from utils import oblicz_statystyki_podstawowe, pobierz_logger

logger = pobierz_logger("HistorycznyBlizniak")

class SilnikBlizniaka:
    """Klasa wyszukująca najbardziej zbliżone losowania historyczne za pomocą odległości cech matematycznych."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.sort_values(by="Numer Losowania", ascending=True).reset_index(drop=True)
        self.baza_cech: List[Dict[str, Any]] = []
        self._przygotuj_baze_cech()

    def _przygotuj_baze_cech(self) -> None:
        """Generuje profile cech wektorowych dla całego zbioru danych losowań."""
        logger.info("Przygotowywanie wektorów cech dla bazy historycznej Lotto.")
        for idx, row in self.df.iterrows():
            liczby = [int(row[f"P{i}"]) for i in range(1, 7)]
            staty = oblicz_statystyki_podstawowe(liczby)
            
            # Dynamiczny kalkulator hotness score na bazie okna kroczącego 50 losowań wstecz
            hotness_score = 0
            if idx > 50:
                okno = self.df.iloc[idx-50:idx]
                plaska_lista = okno[[f"P{i}" for i in range(1, 7)]].values.flatten()
                czestosc_map = Counter(plaska_lista)
                hotness_score = sum(czestosc_map.get(l, 0) for l in liczby)
            
            self.baza_cech.append({
                "Numer": int(row["Numer Losowania"]),
                "Liczby": liczby,
                "suma": staty["suma"],
                "rozstep": staty["rozstep"],
                "parzyste": int(staty["parzyste_nieparzyste"].split(":")[0]) if "parzyste_nieparzyste" in staty else staty["parzyste"],
                "dekady": staty["dekady"],
                "luki": staty["luki"],
                "hotness_score": hotness_score
            })

    def znajdz_blizniakow(self, docelowe_liczby: List[int], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Główna metoda wywoływana przez kontroler app.py.
        Oblicza wielowymiarową odległość i zwraca listę najbardziej podobnych losowań.
        """
        target_staty = oblicz_statystyki_podstawowe(docelowe_liczby)
        t_suma = target_staty["suma"]
        t_rozstep = target_staty["rozstep"]
        t_parzyste = int(target_staty["parzyste_nieparzyste"].split(":")[0]) if "parzyste_nieparzyste" in target_staty else target_staty["parzyste"]
        t_dekady = np.array(target_staty["dekady"])
        t_luki = np.array(target_staty["luki"])

        wyniki = []
        for obiekt in self.baza_cech:
            # Obliczanie ważonej odległości Manhattan dla poszczególnych cech rozkładu
            d_suma = abs(obiekt["suma"] - t_suma) * 0.1
            d_rozstep = abs(obiekt["rozstep"] - t_rozstep) * 0.2
            d_parzyste = abs(obiekt["parzyste"] - t_parzyste) * 1.5
            d_dekady = float(np.sum(np.abs(np.array(obiekt["dekady"]) - t_dekady))) * 1.0
            d_luki = float(np.sum(np.abs(np.array(obiekt["luki"]) - t_luki))) * 0.5
            
            odleglosc_calkowita = d_suma + d_rozstep + d_parzyste + d_dekady + d_luki
            score_podobieństwa = round(100.0 / (1.0 + odleglosc_calkowita), 2)
            
            wyniki.append({
                "Numer": obiekt["Numer"],
                "Liczby Historyczne": str(obiekt["Liczby"]),
                "Podobienstwo_Score": score_podobieństwa,
                "Suma": obiekt["suma"],
                "Rozstęp": obiekt["rozstep"]
            })

        # Sortowanie malejąco według procentowego wskaźnika zgodności profilu
        return sorted(wyniki, key=lambda x: x["Podobienstwo_Score"], reverse=True)[:top_n]
