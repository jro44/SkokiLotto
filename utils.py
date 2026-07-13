"""
Moduł pomocniczy aplikacji LottoHistoryAI.
Definiuje centralne logowanie, walidację struktur oraz szybkie wyliczenia cech.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any

# Konfiguracja głównego rejestratora zdarzeń
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def pobierz_logger(nazwa: str) -> logging.Logger:
    """Zwraca instancję loggera dla zadanego modułu."""
    return logging.getLogger(nazwa)

def bezpieczny_procent(licznik: int, mianownik: int) -> float:
    """Wylicza odsetek, zapobiegając błędowi dzielenia przez zero."""
    if not mianownik:
        return 0.0
    return (float(licznik) / float(mianownik)) * 100.0

def oblicz_statystyki_podstawowe(liczby: List[int]) -> Dict[str, Any]:
    """
    Wyznacza wektor cech strukturalnych dla zestawu liczb.
    Zwraca sumę, rozstęp, parytet oraz gęstość w dekadach i lukach międzyliczbowych.
    """
    posortowane = sorted(liczby)
    parzyste = sum(1 for x in posortowane if x % 2 == 0)
    nieparzyste = 6 - parzyste
    
    dekady = [0] * 5
    for x in posortowane:
        idx = min((x - 1) // 10, 4)
        dekady[idx] += 1
        
    luki = [posortowane[i + 1] - posortowane[i] - 1 for i in range(5)]
    
    return {
        "suma": sum(posortowane),
        "rozstep": posortowane[-1] - posortowane[0],
        "parzyste": parzyste,
        "nieparzyste": nieparzyste,
        "dekady": dekady,
        "luki": luki
    }

def formatuj_zestaw(liczby: List[int]) -> str:
    """Formatuje listę liczb do czytelnego ciągu znaków z dwucyfrowym wyrównaniem."""
    return "  ".join(f"{liczba:02d}" for float_val in [liczby] for liczba in float_val)
