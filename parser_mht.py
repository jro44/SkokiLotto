"""
Parser plików MHT dedykowany dla bazy danych losowań Lotto.
Wykorzystuje wyłącznie wyrażenia regularne (re), działając w 100% offline.
"""

import re
from pathlib import Path
import pandas as pd
from utils import pobierz_logger, waliduj_numery

logger = pobierz_logger("ParserMHT")

class ParserMHTLotto:
    """Klasa odpowiedzialna za parsowanie danych z pliku Wyniki.mht."""
    
    def __init__(self, sciezka_pliku: Path):
        self.sciezka_pliku = sciezka_pliku

    def parsuj(self) -> pd.DataFrame:
        """
        Parsuje plik MHT wyciągając numer losowania oraz 6 wylosowanych liczb.
        Zwraca posortowany DataFrame (od najstarszego do najnowszego).
        """
        logger.info(f"Rozpoczęcie parsowania pliku: {self.sciezka_pliku}")
        if not self.sciezka_pliku.exists():
            logger.error(f"Plik {self.sciezka_pliku} nie istnieje.")
            raise FileNotFoundError(f"Brak pliku: {self.sciezka_pliku.name}")

        with open(self.sciezka_pliku, "r", encoding="utf-8", errors="ignore") as f:
            tresc = f.read()

        # Usunięcie znaków podziału linii specyficznych dla kodowania Quoted-Printable (=3D, =\n)
        tresc = re.sub(r'=\s*\n', '', tresc)
        tresc = tresc.replace('=3D', '=')

        # Znajdowanie wszystkich znaczników <tr>...</tr>
        wiersze_tr = re.findall(r'<tr[^>]*>.*?</tr>', tresc, re.DOTALL | re.IGNORECASE)
        logger.info(f"Znaleziono {len(wiersze_tr)} potencjalnych wierszy HTML TR.")

        rekordy = []
        
        # Wyrażenia regularne do ekstrakcji numeru losowania i liczb
        regex_numer = re.compile(r'<td\s+class=["\']mapyNumer["\'][^>]*>\s*<strong[^>]*>\s*(\d+)\s*</strong>', re.DOTALL | re.IGNORECASE)
        regex_liczby = re.compile(r'<td\s+class=["\']mapWylosowano["\'][^>]*>\s*(\d+)\s*</td>', re.DOTALL | re.IGNORECASE)

        for wiersz in wiersze_tr:
            m_num = regex_numer.search(wiersz)
            if not m_num:
                continue
                
            nr_losowania = int(m_num.group(1))
            znalezione_liczby = [int(x) for x in regex_liczby.findall(wiersz)]
            
            # Filtrowanie i akceptacja wyłącznie wierszy z dokładnie 6 liczbami
            if len(znalezione_liczby) == 6 and waliduj_numery(znalezione_liczby):
                znalezione_liczby.sort()
                rekordy.append([nr_losowania] + znalezione_liczby)

        if not rekordy:
            logger.warning("Nie sparsowano żadnych poprawnych rekordów z pliku MHT.")
            return pd.DataFrame(columns=["Numer", "P1", "P2", "P3", "P4", "P5", "P6"])

        df = pd.DataFrame(rekordy, columns=["Numer", "P1", "P2", "P3", "P4", "P5", "P6"])
        df = df.drop_duplicates(subset=["Numer"])
        df = df.sort_values(by="Numer", ascending=True).reset_index(drop=True)
        
        logger.info(f"Pomyślnie sparsowano {len(df)} unikalnych losowań Lotto.")
        return df
