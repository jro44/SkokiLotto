"""
Moduł zaawansowanych generatorów kuponów na bazie kryteriów statystycznych i filtrów.
"""

import random
from typing import List, Set, Dict, Any
import pandas as pd
from utils import oblicz_statystyki_podstawowe

class GeneratorKuponow:
    """Klasa udostępniająca trzy niezależne strategie generowania typów."""

    @staticmethod
    def generuj_zloty_strzal(df: pd.DataFrame) -> List[int]:
        """
        Strategia 1: Złoty Strzał.
        Losuje ze specjalnie wyselekcjonowanej puli liczb najczęściej padających.
        """
        # Pobieranie top 20 najczęstszych liczb z historii
        wszystkie = df[[f"P{i}" for i in range(1, 7)]].values.flatten()
        pula_top = list(pd.Series(wszystkie).value_counts().head(20).index)
        
        # Losowanie zestawu spełniającego kryterium sumy
        for _ in range(1000):
            propozycja = sorted(random.sample(pula_top, 6))
            suma = sum(propozycja)
            if 100 <= suma <= 200:
                return propozycja
        return sorted(random.sample(pula_top, 6))

    @staticmethod
    def generuj_chybil_trafil_statystyczny(df: pd.DataFrame) -> List[int]:
        """
        Strategia 2: Statystyczny Chybił Trafił.
        Odrzuca układy skrajnie mało prawdopodobne (np. sekwencje, monodekady).
        """
        for _ in range(2000):
            liczby = sorted(random.sample(range(1, 50), 6))
            
            # Filtry eliminacyjne
            # 1. Brak 6 liczb pod rząd
            pod rzad = 0
            for i in range(5):
                if liczby[i+1] - liczby[i] == 1:
                    pod rzad += 1
            if pod rzad >= 5: continue
                
            # 2. Nie wszystkie parzyste / nie wszystkie nieparzyste
            parzyste = sum(1 for x in liczby if x % 2 == 0)
            if parzyste == 0 or parzyste == 6: continue
                
            # 3. Analiza sumy (eliminacja skrajności)
            if not (90 <= sum(liczby) <= 210): continue
                
            # 4. Sprawdzenie rozkładu dekad (czy nie wpadły w jedną)
            staty = oblicz_statystyki_podstawowe(liczby)
            if max(staty["dekady"]) >= 5: continue
                
            return liczby
            
        return sorted(random.sample(range(1, 50), 6))

    @staticmethod
    def generuj_totalny_chybil_trafil() -> List[int]:
        """Strategia 3: Pełna losowość bez stosowania jakichkolwiek filtrów."""
        return sorted(random.sample(range(1, 50), 6))
