"""
Moduł pomocniczy dla aplikacji LottoHistoryAI.
Zapewnia konfigurację logowania oraz współdzielone funkcje narzędziowe.
"""

import logging
from typing import List
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def pobierz_logger(nazwa: str) -> logging.Logger:
    """Zwraca skonfigurowany obiekt loggera."""
    return logging.getLogger(nazwa)

logger = pobierz_logger("Utils")

def waliduj_numery(wiersz: List[int]) -> bool:
    """Sprawdza, czy lista zawiera dokładnie 6 unikalnych liczb w zakresie 1-49."""
    if len(wiersz) != 6:
        return False
    if not all(1 <= x <= 49 for x in wiersz):
        return False
    if len(set(wiersz)) != 6:
        return False
    return True

def oblicz_statystyki_podstawowe(liczby: List[int]) -> dict:
    """Oblicza podstawowe metryki liczbowe dla pojedynczego losowania."""
    posortowane = sorted(liczby)
    parzyste = sum(1 for x in posortowane if x % 2 == 0)
    nieparzyste = 6 - parzyste
    
    dekady = [0] * 5
    for x in posortowane:
        idx = min((x - 1) // 10, 4)
        dekady[idx] += 1
        
    luki = [posortowane[i+1] - posortowane[i] - 1 for i in range(5)]
    
    return {
        "suma": sum(posortowane),
        "rozstep": posortowane[-1] - posortowane[0],
        "parzyste_nieparzyste": f"{parzyste}:{nieparzyste}",
        "dekady": dekady,
        "luki": luki
    }
