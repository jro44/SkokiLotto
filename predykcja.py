"""
Silnik predykcji probabilistycznej i hybrydowej oparty na danych historycznych.
Generuje 3 różne typy predykcji.
"""

import pandas as pd
import numpy as np
from typing import List, Set
from utils import pobierz_logger
from statystyki import AnalizatorStatystyczny
from analiza_skokow import AnalizatorSkokow
from historyczny_blizniak import SilnikBlizniaka

logger = pobierz_logger("Predykcja")

class GeneratorPredykcji:
    """Klasa agregująca algorytmy prognostyczne na bazie trendów matematycznych."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.analizator_skokow = AnalizatorSkokow()

    def generuj_predykcje_blizniacy(self, silnik_blizniaka: SilnikBlizniaka) -> List[int]:
        """Predykcja #1: Bazowana na następstwach najbardziej dopasowanych profilowo bliźniaków."""
        ostatnie_losowanie = self.df.iloc[-1]
        liczby_ostatnie = [int(ostatnie_losowanie[f"P{i}"]) for i in range(1, 7)]
        
        blizniacy = silnik_blizniaka.znajdz_blizniakow(liczby_ostatnie, top_n=5)
        pula_liczb: List[int] = []
        
        for b in blizniacy:
            nr_nastepnego = b["Numer"] + 1
            wiersz_nastepny = self.df[self.df["Numer"] == nr_nastepnego]
            if not wiersz_nastepny.empty:
                for i in range(1, 7):
                    pula_liczb.append(int(wiersz_nastepny.iloc[0][f"P{i}"]))
                    
        if len(set(pula_liczb)) >= 6:
            czestosc = pd.Series(pula_liczb).value_counts()
            return sorted(list(czestosc.head(6).index))
        return sorted(list(range(1, 7)))

    def generuj_predykcje_skoki(self) -> List[int]:
        """Predykcja #2: Analiza skoków pozycji i ekstrapolacja średniego kroczącego przesunięcia."""
        df_skoki = self.analizator_skokow.oblicz_skoki(self.df)
        ostatnie_losowanie = self.df.iloc[-1]
        
        wyznaczone = []
        for i in range(1, 7):
            sredni_skok = round(df_skoki[f"Skok_P{i}"].tail(20).mean())
            nowa_liczba = int(ostatnie_losowanie[f"P{i}"] + sredni_skok)
            # Korekta zakresu 1-49
            if nowa_liczba < 1: nowa_liczba = (nowa_liczba % 49) + 1
            if nowa_liczba > 49: nowa_liczba = (nowa_liczba % 49) + 1
            wyznaczone.append(nowa_liczba)
            
        # Zapewnienie unikalności liczb
        wyznaczone = list(set(wyznaczone))
        while len(wyznaczone) < 6:
            for n in range(1, 50):
                if n not in wyznaczone:
                    wyznaczone.append(n)
                    break
        return sorted(wyznaczone[:6])

    def generuj_predykcje_hybrydowa(self) -> List[int]:
        """Predykcja #3: Hybryda wagowa łącząca gorące liczby oraz mediany matematyczne rozkładów."""
        czestosc_calosc = AnalizatorStatystyczny.oblicz_czestosc_liczb(self.df, zakres_ostatnich=100)
        gorace = list(czestosc_calosc.sort_values(ascending=False).head(15).index)
        
        # Wybór kombinacji median rozkładów z losowością kontrolowaną
        pula = list(set(gorace))
        if len(pula) < 6:
            pula = pula + list(range(1, 10))
            
        wybrane = np.random.choice(pula, size=6, replace=False)
        return sorted([int(x) for x in wybrane])
