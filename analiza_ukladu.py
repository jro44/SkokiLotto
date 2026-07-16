"""
Moduł zaawansowanej analizy izomorfizmu strukturalnego dla Lotto 6/49.
Identyfikuje historyczne losowania o identycznym układzie cech jak najnowszy wynik
i prognozuje stan t+1, mapując go według aktualnych częstości bębna.
"""

from __future__ import annotations
import pandas as pd
from typing import List, Dict, Any
from utils import oblicz_statystyki_podstawowe, pobierz_logger

logger = pobierz_logger("AnalizaUkladu")

class AnalizatorUkladuHistorii:
    def __init__(self, df: pd.DataFrame):
        # Dane posortowane chronologicznie od najstarszego do najnowszego
        self.df = df.sort_values("Numer Losowania", ascending=True).reset_index(drop=True)

    def analizuj_i_mapuj_nastepstwa(self, docelowe_liczby: List[int], aktualne_gorace: List[int]) -> Dict[str, Any]:
        """
        1. Pobiera profil (układ) wejściowy.
        2. Szuka w historii losowań o IDENTYCZNYM układzie (parytet, dekady, rozstęp).
        3. Ekstrahuje wyniki bezpośrednio po nich (t+1).
        4. Mapuje je (aktualizuje) według wag bieżących gorących liczb.
        """
        target_profile = oblicz_statystyki_podstawowe(docelowe_liczby)
        t_parzyste = target_profile["parzyste"]
        t_nieparzyste = target_profile["nieparzyste"]
        t_dekady = target_profile["dekady"]
        t_rozstep = target_profile["rozstep"]

        zidentyfikowane_blizniaki = []
        nastepne_losowania_liczb = []

        # Przeszukujemy historię (pomijamy ostatni wiersz, bo nie ma dla niego t+1)
        for idx in range(len(self.df) - 1):
            wiersz = self.df.iloc[idx]
            liczby_hist = [int(wiersz[f"P{i}"]) for i in range(1, 7)]
            prof_hist = oblicz_statystyki_podstawowe(liczby_hist)

            # Poprawione kryterium identyczności układu geometryczno-statystycznego dla Lotto
            if (prof_hist["parzyste"] == t_parzyste and 
                prof_hist["nieparzyste"] == t_nieparzyste and
                prof_hist["dekady"] == t_dekady and 
                abs(prof_hist["rozstep"] - t_rozstep) <= 3): # tolerancja rozstępu dla stabilności próby
                
                wiersz_nastepny = self.df.iloc[idx + 1]
                liczby_nastepne = [int(wiersz_nastepny[f"P{i}"]) for i in range(1, 7)]
                
                zidentyfikowane_blizniaki.append({
                    "Numer Losowania": int(wiersz["Numer Losowania"]),
                    "Liczby w tym układzie": str(liczby_hist),
                    "Następne Losowanie (t+1)": int(wiersz_nastepny["Numer Losowania"]),
                    "Wynik t+1": str(liczby_nastepne)
                })
                nastepne_losowania_liczb.extend(liczby_nastepne)

        # Jeśli nie znaleziono identycznego układu, zwracamy bezpieczny zestaw awaryjny
        if not zidentyfikowane_blizniaki:
            return {
                "sukces": False,
                "komunikat": "W załadowanej historii nie znaleziono losowania o identycznym układzie geometrycznym przedziałów i parzystości.",
                "zestaw_aktualizowany": sorted(aktualne_gorace[:6])
            }

        # DYNAMICZNA AKTUALIZACJA (MAPOWANIE WEDŁUG AKTUALIZACJI CYKLU)
        czestosc_nastepstw = pd.Series(nastepne_losowania_liczb).value_counts()
        
        ranking_wagowy = {}
        for liczba, ile_razy_w_nastepstwach in czestosc_nastepstw.items():
            waga_aktualizacji = 1.5 if liczba in aktualne_gorace else 1.0
            ranking_wagowy[int(liczba)] = ile_razy_w_nastepstwach * waga_aktualizacji

        # Wybieramy top 6 zaktualizowanych liczb
        wygrywajace_liczby = sorted(ranking_wagowy.keys(), key=lambda x: -ranking_wagowy[x])[:6]
        
        # Korekta techniczna wielkości zestawu
        while len(wygrywajace_liczby) < 6:
            for l in range(1, 50):
                if l not in wygrywajace_liczby:
                    wygrywajace_liczby.append(l)
                    break

        return {
            "sukces": True,
            "blizniaki": pd.DataFrame(zidentyfikowane_blizniaki),
            "zestaw_aktualizowany": sorted(wygrywajace_liczby)
        }
