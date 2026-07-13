"""
Filtry losujące i systemy redukcji skrajnie nieprawdopodobnych kombinacji 
kombinatorycznych (Generatory typów).
"""

from __future__ import annotations
import random
import pandas as pd
from typing import List
from utils import oblicz_statystyki_podstawowe

class GeneratorKuponow:
    """Klasa realizująca alternatywne strategie generowania kuponów losowych."""

    @staticmethod
    def zloty_strzal(df: pd.DataFrame) -> List[int]:
        """Losowanie ze zredukowanej puli najgorętszych liczb z ograniczeniem przedziału sumy."""
        płaska = df[[f"P{i}" for i in range(1, 7)]].values.flatten()
        gorace = list(pd.Series(płaska).value_counts().head(18).index)
        for _ in range(1000):
            propozycja = sorted(random.sample(gorace, 6))
            if 110 <= sum(propozycja) <= 190: 
                return propozycja
        return sorted(random.sample(gorace, 6))

    @staticmethod
    def chybil_trafil_statystyczny() -> List[int]:
        """Losowanie z odrzuceniem układów monodekad, sekwencji liniowych oraz skrajnego parytetu."""
        for _ in range(5000):
            liczby = sorted(random.sample(range(1, 50), 6))
            
            ciag = sum(1 for i in range(5) if liczby[i+1] - liczby[i] == 1)
            if ciag >= 4: 
                continue
            
            parzyste = sum(1 for x in liczby if x % 2 == 0)
            if parzyste in (0, 6): 
                continue
            
            if not (95 <= sum(liczby) <= 205): 
                continue
            
            staty = oblicz_statystyki_podstawowe(liczby)
            if max(staty["dekady"]) >= 4: 
                continue
            
            return liczby
        return sorted(random.sample(range(1, 50), 6))

    @staticmethod
    def totalny_chybil_trafil() -> List[int]:
        """Generator czysto stochastyczny o zerowej filtracji."""
        return sorted(random.sample(range(1, 50), 6))
