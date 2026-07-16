"""
Modył zaawansowanych generatorów zakładów Lotto 6/49.
Zapewnia potrójną strategię typowania oraz pełną wsteczną zgodność nazw atrybutów.
"""

from __future__ import annotations
import random
import pandas as pd
from typing import List, Tuple
from utils import oblicz_statystyki_podstawowe

class GeneratorKuponow:
    """Klasa udostępniająca trzy niezależne strategie generowania typów kuponów Lotto."""

    @staticmethod
    def zloty_strzal(df: pd.DataFrame) -> List[int]:
        """
        Strategia 1: Złoty Strzał.
        Losuje ze specjalnie wyselekcjonowanej puli najczęściej padających liczb,
        kontrolując optymalną sumę matematyczną kuponu.
        """
        płaska_lista = df[[f"P{i}" for i in range(1, 7)]].values.flatten()
        pula_top = list(pd.Series(płaska_lista).value_counts().head(20).index)
        
        for _ in range(1000):
            propozycja = sorted(random.sample(pula_top, 6))
            if 110 <= sum(propozycja) <= 190:
                return propozycja
        return sorted(random.sample(pula_top, 6))

    @staticmethod
    def chybil_trafil_statystyczny(df: pd.DataFrame) -> List[int]:
        """
        Strategia 2: Statystyczny Chybił Trafił.
        Losuje zestaw z pełnego zakresu, automatycznie odrzucając układy skrajnie mało prawdopodobne.
        """
        for _ in range(2000):
            liczby = sorted(random.sample(range(1, 50), 6))
            
            # Filtry eliminacyjne
            ciag_liniowy = sum(1 for i in range(5) if liczby[i+1] - liczby[i] == 1)
            if ciag_liniowy >= 4: 
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
        """
        Strategia 3: Totalny Chybił Trafił.
        Czysta losowość stochastyczna bez stosowania jakichkolwiek filtrów matematycznych.
        """
        return sorted(random.sample(range(1, 49 + 1), 6))

    # --- JAWNE ALIASY INTERFEJSU (BACKWARD COMPATIBILITY) ---
    @classmethod
    def generuj_zloty_strzal(cls, df: pd.DataFrame) -> List[int]:
        """Alias dla metody zloty_strzal obsługujący specyficzne wywołanie kontrolera."""
        return cls.zloty_strzal(df)

    @classmethod
    def generuj_chybil_trafil_statystyczny(cls, df: pd.DataFrame) -> List[int]:
        """Alias dla metody chybil_trafil_statystyczny obsługujący specyficzne wywołanie kontrolera."""
        return cls.chybil_trafil_statystyczny(df)

    @classmethod
    def generuj_totalny_chybil_trafil(cls) -> List[int]:
        """Alias dla metody totalny_chybil_trafil obsługujący specyficzne wywołanie kontrolera."""
        return cls.totalny_chybil_trafil()
