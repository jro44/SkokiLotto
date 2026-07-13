"""
Moduł analizy skoków (różnic pozycji między kolejnymi losowaniami).
"""

import pandas as pd
from utils import pobierz_logger

logger = pobierz_logger("AnalizaSkokow")

class AnalizatorSkokow:
    """Klasa obliczająca przesunięcia (skoki) wartości na poszczególnych pozycjach."""
    
    @staticmethod
    def oblicz_skoki(df: pd.DataFrame) -> pd.DataFrame:
        """
        Oblicza Skok_P1 do Skok_P6 jako Różnica = Wartość_Bieżąca - Wartość_Poprzednia.
        Dla pierwszego losowania wartości skoku wynoszą 0 (lub NaN, tu zastąpione 0).
        """
        logger.info("Obliczanie mapy skoków pozycji losowań.")
        df_skoki = df.copy()
        
        for i in range(1, 7):
            df_skoki[f"Skok_P{i}"] = df_skoki[f"P{i}"].diff().fillna(0).astype(int)
            
        return df_skoki
