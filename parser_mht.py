"""
Niezależny, offline parser plików MHT/HTML realizujący ekstrakcję 
danych z tabel za pomocą czystych wyrażeń regularnych (re).
"""

from __future__ import annotations
import re
from pathlib import Path
from email import policy
from email.parser import BytesParser
import pandas as pd
from utils import pobierz_logger

logger = pobierz_logger("ParserMHT")

class ParserMHTLotto:
    """Klasa odpowiedzialna za przetwarzanie i walidację plików formatu Wyniki.mht."""
    
    def __init__(self, sciezka_pliku: Path):
        self.sciezka_pliku = sciezka_pliku

    def _pobierz_klasy_znacznika(self, td_otwierajacy: str) -> set[str]:
        """Wyciąga klasy CSS zawarte wewnątrz otwierającego tagu TD."""
        dopasowanie = re.search(
            r"\bclass\s*=\s*([\"'])(.*?)\1",
            td_otwierajacy,
            flags=re.IGNORECASE | re.DOTALL
        )
        if not dopasowanie:
            return set()
        return {
            klasa.strip().lower()
            for klasa in re.split(r"\s+", dopasowanie.group(2).strip())
            if klasa.strip()
        }

    def parsuj(self) -> pd.DataFrame:
        """
        Parsuje zawartość pliku MHT, dekodując struktury wieloczęściowe MIME.
        Zwraca uporządkowany DataFrame z kolumnami indeksu i pozycji losowania.
        """
        logger.info(f"Inicjalizacja odczytu pliku: {self.sciezka_pliku.name}")
        if not self.sciezka_pliku.exists():
            raise FileNotFoundError(f"Nie odnaleziono pliku: {self.sciezka_pliku.name}")

        dane = self.sciezka_pliku.read_bytes()
        tresc_html = ""

        try:
            wiadomosc = BytesParser(policy=policy.default).parsebytes(dane)
            if wiadomosc.is_multipart():
                fragmenty = []
                for czesc in wiadomosc.walk():
                    if czesc.get_content_type().lower() == "text/html":
                        try:
                            fragmenty.append(czesc.get_content())
                        except Exception:
                            kodowanie = czesc.get_content_charset() or "utf-8"
                            fragmenty.append(czesc.get_payload(decode=True).decode(kodowanie, errors="replace"))
                tresc_html = "\n".join(fragmenty)
            else:
                if wiadomosc.get_content_type().lower() == "text/html":
                    tresc_html = wiadomosc.get_content()
        except Exception as e:
            logger.warning(f"Błąd analizy struktury MIME, uruchamianie dekodowania awaryjnego: {e}")

        if not tresc_html:
            for kodowanie in ("utf-8", "cp1250", "iso-8859-2", "latin-1"):
                try:
                    tresc_html = dane.decode(kodowanie)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                tresc_html = dane.decode("utf-8", errors="replace")

        wzorzec_tr = re.compile(r"<tr\b[^>]*>(.*?)</tr\s*>", flags=re.IGNORECASE | re.DOTALL)
        wzorzec_td = re.compile(r"(<td\b[^>]*>)(.*?)</td\s*>", flags=re.IGNORECASE | re.DOTALL)
        wzorzec_strong = re.compile(r"<strong\b[^>]*>\s*(\d+)\s*</strong\s*>", flags=re.IGNORECASE | re.DOTALL)

        rekordy = []
        wiersze_tr = wzorzec_tr.findall(tresc_html)

        for wiersz in wiersze_tr:
            komorki = wzorzec_td.findall(wiersz)
            if not komorki:
                continue

            indeks_numeru = None
            numer_losowania = None

            for indeks, (td_start, td_srodek) in enumerate(komorki):
                if "mapynumer" in self._pobierz_klasy_znacznika(td_start):
                    dopasowanie_numeru = wzorzec_strong.search(td_srodek)
                    if dopasowanie_numeru:
                        indeks_numeru = indeks
                        numer_losowania = int(dopasowanie_numeru.group(1))
                        break

            if indeks_numeru is None or numer_losowania is None:
                continue

            komorki_liczb = komorki[indeks_numeru + 1 : indeks_numeru + 50]
            if len(komorki_liczb) < 49:
                continue

            wylosowane = []
            for pozycja_liczby, (td_start, _) in enumerate(komorki_liczb, start=1):
                if "mapwylosowano" in self._pobierz_klasy_znacznika(td_start):
                    wylosowane.append(pozycja_liczby)

            if len(wylosowane) != 6:
                continue

            rekord = {"Numer Losowania": numer_losowania}
            posortowane = sorted(wylosowane)
            for i in range(6):
                rekord[f"P{i + 1}"] = posortowane[i]
            rekordy.append(rekord)

        if not rekordy:
            logger.error("Parser zakończył pracę z pustym zbiorem danych.")
            return pd.DataFrame(columns=["Numer Losowania", "P1", "P2", "P3", "P4", "P5", "P6"])

        df = pd.DataFrame(rekordy).drop_duplicates(subset=["Numer Losowania"], keep="first")
        df = df.sort_values("Numer Losowania", ascending=False).reset_index(drop=True)
        
        logger.info(f"Pomyślnie zaimportowano i zweryfikowano {len(df)} rekordów losowań.")
        return df.dropna().astype(int)
