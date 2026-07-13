"""
Silnik podobieństwa profilowego losowań (Historyczny Bliźniak).
Oblicza wektory cech losowań i wyszukuje najbardziej zbliżone stany z przeszłości.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from utils import pobierz_logger, oblicz_statystyki_podstawowe

logger = pobierz_logger("HistorycznyBlizniak")

class SilnikBlizniaka:
    """Klasa wyszukująca najbardziej zbliżone losowania historyczne za pomocą autorskiego scoringu."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.sort_values(by="Numer").reset_index(drop=True)
        self._przygotuj_baze_cech()

    def _przygotuj_baze_cech(self) -> None:
        """Generuje profile cech dla całego zbioru danych."""
        logger.info("Przygotowywanie wektorów cech dla bazy historycznej.")
        cechy = []
        
        # Wyznaczenie mapy opóźnień (delay) i gorącości (hotness) dla każdego punktu w czasie
        # Na potrzeby pełnego offline wyznaczamy kroczące częstości
        for idx, row in self.df.iterrows():
            liczby = [int(row[f"P{i}"]) for i in range(1, 7)]
            staty = oblicz_statystyki_podstawowe(liczby)
            
            # Prosty kalkulator hotness/delay na bazie okna historycznego z 50 losowań wstecz
            hotness_score = 0
            delay_score = 0
            if idx > 50:
                okno = self.df.iloc[idx-50:idx]
                płaska_lista = okno[[f"P{i}" for i in range(1, 7)]].values.flatten()
                unikalne, counts = np.unique(płaska_lista, return_counts=True)
                czestosc_map = dict(zip(unikalne, counts))
                
                for l in liczby:
                    hotness_score += czestosc_map.get(l, 0)
                    # Opóźnienie (ile losowań temu padła)
                    ostatnie_wystapienie = okno[(okno[f"P1"]==l) | (okno[f"P2"]==l) | (okno[f"P3"]==l) | (okno[f"P4"]==l) | (okno[f"P5"]==l) | (okno[f"P6"]==l)]
                    if not ostatnie_wystapienie.empty:
                        delay_score += (idx - ostatnie_wystapienie.index[-1])
                    else:
                        delay_score += 50
            
            cechy.append({
                "Numer": row["Numer"],
                "suma": staty["suma"],
                "rozstep": staty["rozstep"],
                "parzyste": int(staty["parzyste_nieparzyste"].split(":")[0]),
                "dekady": staty["dekady"],
                "luki": staty["luki"],
                "hotness_score": hotness_score,
                "delay_score": delay_score,
                "liczby": liczby
            })
        self.baza_cech = cechy

    def znajdz_blizniakow(self, docelowe_liczby: List[int], top_n: int = 10) -> List[Dict[str, Any]]:
        """Wyszukuje top N losowań najbardziej podobnych do zestawu wejściowego."""
        target_staty = oblicz_statystyki_podstawowe(docelowe_liczby)
        t_suma = target_staty["suma"]
        t_rozstep = target_staty["rozstep"]
        t_parzyste = int(target_staty["parzyste_nieparzyste"].split(":")[0])
        t_dekady = np.array(target_staty["dekady"])
        t_luki = np.array(target_staty["luki"])

        wyniki = []
        for obiekt in self.baza_cech:
            # Miara odległości (im mniejsza, tym bardziej podobne losowanie)
            d_suma = abs(obiekt["suma"] - t_suma) * 0.1
            d_rozstep = abs(obiekt["rozstep"] - t_rozstep) * 0.2
            d_parzyste = abs(obiekt["parzyste"] - t_parzyste) * 1.5
            d_dekady = np.sum(np.abs(np.array(obiekt["dekady"]) - t_dekady)) * 1.0
            d_luki = np.sum(np.abs(np.array(obiekt["luki"]) - t_luki)) * 0.5
            
            odleglosc_calkowita = d_suma + d_rozstep + d_parzyste + d_dekady + d_luki
            
            wyniki.append({
                "Numer": obiekt["Numer"],
                "Liczby": obiekt["liczby"],
                "Podobienstwo_Score": round(100 / (1 + odleglosc_calkowita), 2),
                "Suma": obiekt["suma"],
                "Rozstep": obiekt["rozstep"]
            })

        # Sortowanie od najbardziej podobnych (najwyższy score)
        wyniki_posortowane = sorted(wyniki, key=lambda x: x["Podobienstwo_Score"], reverse=True)
        return wyniki_posortowane[:top_n]
