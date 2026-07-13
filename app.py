from __future__ import annotations

import html
import re
from collections import Counter
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st

# =============================================================================
# KONFIGURACJA
# =============================================================================

NAZWA_PLIKU = "Wyniki.mht"
LICZBA_POZYCJI = 6
MIN_LICZBA = 1
MAX_LICZBA = 49
PROG_DUZEGO_SKOKU_WAHADLA = 10

KOLUMNY_LICZB = [f"P{i}" for i in range(1, LICZBA_POZYCJI + 1)]
KOLUMNY_SKOKOW = [f"Skok_P{i}" for i in range(1, LICZBA_POZYCJI + 1)]

st.set_page_config(
    page_title="Analizator gradientów Lotto 6/49",
    page_icon="📈",
    layout="wide",
)

# =============================================================================
# WCZYTYWANIE I PARSOWANIE MHT/HTML
# =============================================================================

def znajdz_sciezke_pliku() -> Path:
    """Zwraca ścieżkę pliku znajdującego się obok uruchamianego app.py."""
    return Path(__file__).resolve().parent / NAZWA_PLIKU


@st.cache_data(show_spinner=False)
def wczytaj_zawartosc_mht(sciezka_tekstowa: str) -> str:
    """
    Wczytuje dokument MHT.
    Ekstrahuje text/html z kontenera MIME lub stosuje bezpieczny odczyt awaryjny.
    """
    sciezka = Path(sciezka_tekstowa)
    dane = sciezka.read_bytes()

    try:
        wiadomosc = BytesParser(policy=policy.default).parsebytes(dane)

        if wiadomosc.is_multipart():
            fragmenty_html: list[str] = []

            for czesc in wiadomosc.walk():
                if czesc.get_content_type().lower() != "text/html":
                    continue

                try:
                    fragmenty_html.append(czesc.get_content())
                except Exception:
                    payload = czesc.get_payload(decode=True) or b""
                    kodowanie = czesc.get_content_charset() or "utf-8"
                    fragmenty_html.append(
                        payload.decode(kodowanie, errors="replace")
                    )

            if fragmenty_html:
                return "\n".join(fragmenty_html)

        if wiadomosc.get_content_type().lower() == "text/html":
            return wiadomosc.get_content()

    except Exception:
        pass

    for kodowanie in ("utf-8", "cp1250", "iso-8859-2", "latin-1"):
        try:
            return dane.decode(kodowanie)
        except UnicodeDecodeError:
            continue

    return dane.decode("utf-8", errors="replace")


def pobierz_klasy_znacznika(td_otwierajacy: str) -> set[str]:
    """Zwraca zestaw klas CSS z otwierającego znacznika td."""
    dopasowanie = re.search(
        r"\bclass\s*=\s*([\"'])(.*?)\1",
        td_otwierajacy,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not dopasowanie:
        return set()

    return {
        klasa.strip().lower()
        for klasa in re.split(r"\s+", dopasowanie.group(2).strip())
        if klasa.strip()
    }


@st.cache_data(show_spinner=False)
def parsuj_wyniki_lotto(zawartosc: str) -> pd.DataFrame:
    """Parsuje wiersze tabeli HTML przy użyciu biblioteki re."""
    wzorzec_tr = re.compile(
        r"<tr\b[^>]*>(.*?)</tr\s*>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    wzorzec_td = re.compile(
        r"(<td\b[^>]*>)(.*?)</td\s*>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    wzorzec_strong = re.compile(
        r"<strong\b[^>]*>\s*(\d+)\s*</strong\s*>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    rekordy: list[dict[str, int]] = []

    for zawartosc_wiersza in wzorzec_tr.findall(zawartosc):
        komorki = wzorzec_td.findall(zawartosc_wiersza)
        if not komorki:
            continue

        indeks_numeru: int | None = None
        numer_losowania: int | None = None

        for indeks, (td_start, td_srodek) in enumerate(komorki):
            klasy = pobierz_klasy_znacznika(td_start)

            if "mapynumer" not in klasy:
                continue

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

        wylosowane: list[int] = []

        for pozycja_liczby, (td_start, _td_srodek) in enumerate(
            komorki_liczb,
            start=1,
        ):
            klasy = pobierz_klasy_znacznika(td_start)
            if "mapwylosowano" in klasy:
                wylosowane.append(pozycja_liczby)

        if len(wylosowane) != LICZBA_POZYCJI:
            continue

        rekord = {"Numer Losowania": numer_losowania}
        posortowane_wylosowane = sorted(wylosowane)
        for i in range(LICZBA_POZYCJI):
            rekord[f"P{i + 1}"] = posortowane_wylosowane[i]
            
        rekordy.append(rekord)

    if not rekordy:
        return pd.DataFrame(columns=["Numer Losowania", *KOLUMNY_LICZB])

    df = pd.DataFrame(rekordy)
    df = df.drop_duplicates(subset=["Numer Losowania"], keep="first")
    df = df.sort_values("Numer Losowania", ascending=False).reset_index(drop=True)

    for kolumna in ["Numer Losowania", *KOLUMNY_LICZB]:
        df[kolumna] = pd.to_numeric(df[kolumna], errors="coerce")

    df = df.dropna().astype(int)
    return df


# =============================================================================
# MAPA SKOKÓW I DANE PRZEJŚĆ
# =============================================================================

def przygotuj_dane_chronologiczne(df: pd.DataFrame) -> pd.DataFrame:
    """Sortuje wyniki od najstarszego do najnowszego."""
    return df.sort_values("Numer Losowania", ascending=True).reset_index(drop=True)


def oblicz_mape_skokow(df: pd.DataFrame) -> pd.DataFrame:
    """Wylicza gradient (różnicę) osobno dla każdej z sześciu pozycji."""
    chronologiczny = przygotuj_dane_chronologiczne(df)

    skoki = chronologiczny[KOLUMNY_LICZB].diff()
    skoki.columns = KOLUMNY_SKOKOW

    wynik = pd.concat(
        [chronologiczny[["Numer Losowania"]], skoki],
        axis=1,
    ).iloc[1:].copy()

    wynik[KOLUMNY_SKOKOW] = wynik[KOLUMNY_SKOKOW].astype(int)
    return wynik.reset_index(drop=True)


def przygotuj_przejscia(df: pd.DataFrame) -> pd.DataFrame:
    """Buduje tabelę przejść stanów dla analizy warunkowej."""
    chronologiczny = przygotuj_dane_chronologiczne(df)
    przejscia = chronologiczny.copy()

    for i, (kol_liczby, kol_skoku) in enumerate(
        zip(KOLUMNY_LICZB, KOLUMNY_SKOKOW),
        start=1,
    ):
        przejscia[kol_skoku] = chronologiczny[kol_liczby].diff()
        przejscia[f"Poprzednie_P{i}"] = chronologiczny[kol_liczby].shift(1)

    przejscia["Poprzedni rozstęp"] = (
        przejscia["Poprzednie_P6"] - przejscia["Poprzednie_P1"]
    )
    przejscia["Bieżący rozstęp"] = przejscia["P6"] - przejscia["P1"]
    przejscia["Poprzedni numer losowania"] = (
        chronologiczny["Numer Losowania"].shift(1)
    )

    przejscia = przejscia.iloc[1:].copy()

    kolumny_int = [
        "Numer Losowania",
        "Poprzedni numer losowania",
        "Poprzedni rozstęp",
        "Bieżący rozstęp",
        *KOLUMNY_LICZB,
        *KOLUMNY_SKOKOW,
        *[f"Poprzednie_P{idx}" for idx in range(1, 7)],
    ]
    przejscia[kolumny_int] = przejscia[kolumny_int].astype(int)

    return przejscia.reset_index(drop=True)


def ogranicz_historie(df: pd.DataFrame, wybor: str) -> pd.DataFrame:
    """Ogranicza bazę danych do wybranych N ostatnich losowań."""
    if wybor == "Wszystkie":
        return df.copy()

    liczba = int(wybor)
    return (
        df.sort_values("Numer Losowania", ascending=False)
        .head(liczba)
        .sort_values("Numer Losowania", ascending=True)
        .reset_index(drop=True)
    )


# =============================================================================
# STATYSTYKI
# =============================================================================

def top_3_wartosci(seria: pd.Series) -> list[tuple[int, int, float]]:
    licznik = Counter(int(x) for x in seria.dropna().tolist())
    razem = sum(licznik.values())

    return [
        (wartosc, liczba, 100.0 * liczba / razem if razem else 0.0)
        for wartosc, liczba in licznik.most_common(3)
    ]


def tabela_statystyk(skoki: pd.DataFrame) -> pd.DataFrame:
    rekordy: list[dict[str, object]] = []

    for i, kolumna in enumerate(KOLUMNY_SKOKOW, start=1):
        seria = skoki[kolumna]
        top = top_3_wartosci(seria)

        rekord: dict[str, object] = {
            "Pozycja": f"P{i}",
            "Średni skok kierunkowy": round(float(seria.mean()), 3),
            "Średni skok bezwzględny": round(float(seria.abs().mean()), 3),
        }

        for miejsce in range(3):
            if miejsce < len(top):
                wartosc, liczba, procent = top[miejsce]
                rekord[f"Top {miejsce + 1}"] = (
                    f"{wartosc:+d} | {liczba} razy | {procent:.1f}%"
                )
            else:
                rekord[f"Top {miejsce + 1}"] = "—"

        rekordy.append(rekord)

    return pd.DataFrame(rekordy)


def rozklad_skokow(seria: pd.Series) -> pd.DataFrame:
    rozklad = (
        seria.value_counts(normalize=True)
        .sort_index()
        .mul(100)
        .rename("Prawdopodobieństwo [%]")
        .to_frame()
    )
    rozklad.index.name = "Skok"
    return rozklad


# =============================================================================
# STANY MATEMATYCZNE
# =============================================================================

def bezpieczny_procent(licznik: int, mianownik: int) -> float:
    return 100.0 * licznik / mianownik if mianownik else 0.0


def wyznacz_progi_stanow(przejscia: pd.DataFrame) -> tuple[float, float, int]:
    rozstepy = przejscia["Poprzedni rozstęp"]
    prog_malego = float(rozstepy.quantile(0.25))
    prog_duzego = float(rozstepy.quantile(0.75))

    skoki_skrajne = pd.concat(
        [
            przejscia["Skok_P1"].abs(),
            przejscia["Skok_P6"].abs(),
        ],
        ignore_index=True,
    )
    prog_ekspansji = max(5, int(round(skoki_skrajne.quantile(0.75))))

    return prog_malego, prog_duzego, prog_ekspansji


def analiza_stanow(przejscia: pd.DataFrame) -> dict[str, object]:
    prog_malego, prog_duzego, prog_ekspansji = wyznacz_progi_stanow(przejscia)

    maska_kompresji = przejscia["Poprzedni rozstęp"] >= prog_duzego
    kompresje = przejscia.loc[maska_kompresji]
    trafione_kompresje = kompresje[
        (kompresje["Skok_P1"] > 0) & (kompresje["Skok_P6"] < 0)
    ]

    maska_ekspansji = przejscia["Poprzedni rozstęp"] <= prog_malego
    ekspansje = przejscia.loc[maska_ekspansji]
    trafione_ekspansje = ekspansje[
        (ekspansje["Skok_P1"] <= -prog_ekspansji)
        & (ekspansje["Skok_P6"] >= prog_ekspansji)
    ]

    wyniki_wahadla: dict[str, dict[str, float | int]] = {}

    for pozycja, kolumna in enumerate(KOLUMNY_SKOKOW, start=1):
        seria = przejscia[kolumna].reset_index(drop=True)
        poprzedni_sk = seria.shift(1)

        duzy_poprzedni = poprzedni_sk.abs() > PROG_DUZEGO_SKOKU_WAHADLA
        przeciwny_znak = (
            ((poprzedni_sk > 0) & (seria < 0))
            | ((poprzedni_sk < 0) & (seria > 0))
        )

        liczba_przypadkow = int(duzy_poprzedni.sum())
        liczba_korekt = int((duzy_poprzedni & przeciwny_znak).sum())

        wyniki_wahadla[f"P{pozycja}"] = {
            "przypadki": integer_przypadkow := liczba_przypadkow,
            "korekty": integer_korekt := liczba_korekt,
            "prawdopodobieństwo": bezpieczny_procent(
                integer_korekt,
                integer_przypadkow,
            ),
        }

    return {
        "prog_malego_rozstepu": prog_malego,
        "prog_duzego_rozstepu": prog_duzego,
        "prog_duzego_skoku_ekspansji": prog_ekspansji,
        "kompresja_przypadki": len(kompresje),
        "kompresja_trafienia": len(trafione_kompresje),
        "kompresja_prawdopodobienstwo": bezpieczny_procent(
            len(trafione_kompresje),
            len(kompresje),
        ),
        "ekspansja_przypadki": len(ekspansje),
        "ekspansja_trafienia": len(trafione_ekspansje),
        "ekspansja_prawdopodobienstwo": bezpieczny_procent(
            len(trafione_ekspansje),
            len(ekspansje),
        ),
        "wahadlo": wyniki_wahadla,
    }


# =============================================================================
# PREDYKCJA HEURYSTYCZNA
# =============================================================================

def znormalizuj_liczniki(serie: Iterable[tuple[pd.Series, float]]) -> dict[int, float]:
    wynik: dict[int, float] = {}

    for seria, waga in serie:
        if seria.empty:
            continue

        czestosci = seria.value_counts(normalize=True)
        for skok, prawdopodobienstwo in czestosci.items():
            wynik[int(skok)] = (
                wynik.get(int(skok), 0.0)
                + float(waga) * float(prawdopodobienstwo)
            )

    return wynik


def wybierz_najlepszy_skok(
    przejscia: pd.DataFrame,
    kolumna: str,
    stan: str,
    prog_malego: float,
    prog_duzego: float,
    ostatni_skok: int | None,
) -> tuple[int, float, list[tuple[int, float]]]:
    wszystkie = przejscia[kolumna]
    ostatnie = przejscia.tail(min(100, len(przejscia)))[kolumna]

    serie_wazone: list[tuple[pd.Series, float]] = [
        (wszystkie, 0.35),
        (ostatnie, 0.35),
    ]

    if stan == "Kompresja":
        warunkowe = przejscia.loc[
            przejscia["Poprzedni rozstęp"] >= prog_duzego,
            kolumna,
        ]
        serie_wazone.append((warunkowe, 0.30))
    elif stan == "Ekspansja":
        warunkowe = przejscia.loc[
            przejscia["Poprzedni rozstęp"] <= prog_malego,
            kolumna,
        ]
        serie_wazone.append((warunkowe, 0.30))
    else:
        srodkowe = przejscia.loc[
            przejscia["Poprzedni rozstęp"].between(
                prog_malego,
                prog_duzego,
                inclusive="neither",
            ),
            kolumna,
        ]
        serie_wazone.append((srodkowe, 0.20))

    punkty = znormalizuj_liczniki(serie_wazone)

    if (
        ostatni_skok is not None
        and abs(ostatni_skok) > PROG_DUZEGO_SKOKU_WAHADLA
    ):
        poprzednie = przejscia[kolumna].shift(1)
        maska = (
            (poprzednie.abs() > PROG_DUZEGO_SKOKU_WAHADLA)
            & (np.sign(poprzednie) == np.sign(ostatni_skok))
            & (np.sign(przejscia[kolumna]) == -np.sign(ostatni_skok))
        )
        korekty = przejscia.loc[maska, kolumna]

        for skok, prawdopodobienstwo in (
            korekty.value_counts(normalize=True).items()
        ):
            punkty[int(skok)] = (
                punkty.get(int(skok), 0.0)
                + 0.45 * float(prawdopodobienstwo)
            )

    ranking = sorted(
        punkty.items(),
        key=lambda para: (-para[1], abs(para[0]), para[0]),
    )

    if not ranking:
        return 0, 0.0, [(0, 0.0)]

    najlepszy_skok, najlepszy_wynik = ranking[0]
    return int(najlepszy_skok), float(najlepszy_wynik), ranking[:5]


def dopasuj_do_zakresu_i_kolejnosci(kandydaci: list[int]) -> list[int]:
    wynik = np.array(kandydaci, dtype=int)

    for i in range(LICZBA_POZYCJI):
        minimum = MIN_LICZBA + i
        maksimum = MAX_LICZBA - (LICZBA_POZYCJI - 1 - i)
        wynik[i] = int(np.clip(wynik[i], minimum, maksimum))

    for _ in range(3):
        for i in range(1, LICZBA_POZYCJI):
            wynik[i] = max(wynik[i], wynik[i - 1] + 1)

        wynik[-1] = min(wynik[-1], MAX_LICZBA)

        for i in range(LICZBA_POZYCJI - 2, -1, -1):
            wynik[i] = min(wynik[i], wynik[i + 1] - 1)

        wynik[0] = max(wynik[0], MIN_LICZBA)

    return [int(x) for x in wynik]


def diagnozuj_i_generuj(
    df_zakres: pd.DataFrame,
    przejscia: pd.DataFrame,
) -> dict[str, object]:
    statystyki_stanow = analiza_stanow(przejscia)
    prog_malego = float(statystyki_stanow["prog_malego_rozstepu"])
    prog_duzego = float(statystyki_stanow["prog_duzego_rozstepu"])

    najnowszy = (
        df_zakres.sort_values("Numer Losowania", ascending=False)
        .iloc[0]
    )
    liczby_ostatnie = [int(najnowszy[k]) for k in KOLUMNY_LICZB]
    rozstep_ostatni = liczby_ostatnie[-1] - liczby_ostatnie[0]

    if rozstep_ostatni >= prog_duzego:
        stan = "Kompresja"
        opis_stanu = (
            "Ostatni rozstęp jest szeroki. Model sprawdza historyczne "
            "przejścia po podobnie rozciągniętych układach."
        )
    elif rozstep_ostatni <= prog_malego:
        stan = "Ekspansja"
        opis_stanu = (
            "Ostatni rozstęp jest ciasny. Model sprawdza historyczne "
            "przejścia po podobnie skupionych układach."
        )
    else:
        stan = "Neutralny"
        opis_stanu = (
            "Ostatni rozstęp znajduje się pomiędzy progami kwartylowymi. "
            "Największą wagę otrzymuje rozkład ogólny i trend najnowszy."
        )

    ostatnie_skoki = (
        przejscia.sort_values("Numer Losowania", ascending=True)
        .iloc[-1][KOLUMNY_SKOKOW]
    )

    przewidywane_skoki: list[int] = []
    pewnosci: list[float] = []
    rankingi: dict[str, list[tuple[int, float]]] = {}
    aktywne_wahadla: list[str] = []

    for i, kolumna in enumerate(KOLUMNY_SKOKOW, start=1):
        ostatni_skok = int(ostatnie_skoki[kolumna])

        if abs(ostatni_skok) > PROG_DUZEGO_SKOKU_WAHADLA:
            aktywne_wahadla.append(f"P{i}: ostatni skok {ostatni_skok:+d}")

        skok, wynik, top = wybierz_najlepszy_skok(
            przejscia=przejscia,
            kolumna=kolumna,
            stan=stan,
            prog_malego=prog_malego,
            prog_duzego=prog_duzego,
            ostatni_skok=ostatni_skok,
        )
        przewidywane_skoki.append(skok)
        pewnosci.append(wynik)
        rankingi[f"P{i}"] = top

    kandydaci = [
        liczby_ostatnie[idx] + przewidywane_skoki[idx]
        for idx in range(LICZBA_POZYCJI)
    ]
    zestaw = dopasuj_do_zakresu_i_kolejnosci(kandydaci)

    return {
        "numer_ostatniego": int(najnowszy["Numer Losowania"]),
        "liczby_ostatnie": liczby_ostatnie,
        "rozstep_ostatni": rozstep_ostatni,
        "stan": stan,
        "opis_stanu": opis_stanu,
        "aktywne_wahadla": aktywne_wahadla,
        "przewidywane_skoki": przewidywane_skoki,
        "pewnosci": pewnosci,
        "rankingi": rankingi,
        "zestaw": zestaw,
        "statystyki_stanow": statystyki_stanow,
    }


# =============================================================================
# INTERFEJS
# =============================================================================

def formatuj_zestaw(liczby: list[int]) -> str:
    return "  ".join(f"{liczba:02d}" for liczba in liczby)


def pokaz_aplikacje() -> None:
    st.title("📈 Analizator gradientów przesunięć Lotto 6/49")
    st.caption("Analiza zmian wartości na sześciu uporządkowanych pozycjach kuponu.")

    sciezka = znajdz_sciezke_pliku()

    try:
        if not sciezka.exists():
            raise FileNotFoundError(str(sciezka))

        zawartosc = wczytaj_zawartosc_mht(str(sciezka))
        df = parsuj_wyniki_lotto(zawartosc)

        if df.empty:
            st.error(
                "Plik został odnaleziony, ale parser nie wykrył poprawnych "
                "wierszy Lotto zawierających dokładnie 6 liczb."
            )
            st.stop()

        if len(df) < 3:
            st.error("Do analizy skoków i stanów potrzebne są co najmniej 3 losowania.")
            st.stop()

    except FileNotFoundError:
        st.error(f"Nie znaleziono pliku '{NAZWA_PLIKU}' w folderze aplikacji.")
        st.stop()
    except Exception as blad:
        st.error(f"Wystąpił błąd podczas wczytywania danych: {blad}")
        st.stop()

    with st.sidebar:
        st.header("Ustawienia analizy")
        st.success("Plik lokalny został wczytany poprawnie.")
        st.write(f"**Poprawne losowania:** {len(df)}")
        st.write(f"**Najnowszy numer:** {int(df['Numer Losowania'].max())}")
        st.write(f"**Najstarszy numer:** {int(df['Numer Losowania'].min())}")

        dostepne_opcje = [opcja for opcja in ["100", "250", "500"] if len(df) >= int(opcja)]
        dostepne_opcje.append("Wszystkie")

        wybor_zakresu = st.select_slider(
            "Zakres nauki trendów",
            options=dostepne_opcje,
            value=dostepne_opcje[-1],
            help="Wybierz liczbę najnowszych losowań używanych do statystyk i predykcji.",
        )

    df_zakres = ogranicz_historie(df, wybor_zakresu)
    mapa_skokow_zakres = oblicz_mape_skokow(df_zakres)
    przejscia_zakres = przygotuj_przejscia(df_zakres)

    zakladka_mapa, zakladka_stat, zakladka_pred = st.tabs(
        ["Surowa Mapa Skoków", "Analiza Statystyczna", "Sytuacje i Predykcja"]
    )

    with zakladka_mapa:
        st.subheader("Surowa mapa gradientów")
        
        kolejnosc_tabeli = st.radio(
            "Sortowanie tabeli:", 
            ["Od najnowszych", "Od najstarszych"], 
            horizontal=True, 
            key="sort_mapa"
        )
        
        mapa_do_wyswietlenia = mapa_skokow_zakres.copy()
        if kolejnosc_tabeli == "Od najnowszych":
            mapa_do_wyswietlenia = mapa_do_wyswietlenia.sort_values("Numer Losowania", ascending=False)
        else:
            mapa_do_wyswietlenia = mapa_do_wyswietlenia.sort_values("Numer Losowania", ascending=True)

        st.dataframe(
            mapa_do_wyswietlenia.reset_index(drop=True),
            width="stretch",
            hide_index=True,
            height=650,
        )

    with zakladka_stat:
        st.subheader("Średnie i najczęstsze gradienty")
        statystyki = tabela_statystyk(mapa_skokow_zakres)
        st.dataframe(statystyki, width="stretch", hide_index=True)

        st.divider()
        st.subheader("Rozkłady prawdopodobieństwa skoków")

        for poczatek in (0, 2, 4):
            kol1, kol2 = st.columns(2)
            for kontener, indeks in zip((kol1, kol2), (poczatek, poczatek + 1)):
                with kontener:
                    kolumna = KOLUMNY_SKOKOW[indeks]
                    st.markdown(f"#### Pozycja P{indeks + 1}")
                    st.bar_chart(
                        rozklad_skokow(mapa_skokow_zakres[kolumna]),
                        x_label="Wartość skoku",
                        y_label="Prawdopodobieństwo [%]",
                        width="stretch",
                    )

    with zakladka_pred:
        wynik = diagnozuj_i_generuj(df_zakres, przejscia_zakres)
        stany = wynik["statystyki_stanow"]

        st.subheader("Diagnoza najnowszego układu")

        met1, met2, met3, met4 = st.columns(4)
        met1.metric("Najnowsze losowanie", str(wynik["numer_ostatniego"]))
        met2.metric("Ostatni zestaw", formatuj_zestaw(wynik["liczby_ostatnie"]))
        met3.metric("Rozstęp P6 − P1", str(wynik["rozstep_ostatni"]))
        met4.metric("Rozpoznany stan", str(wynik["stan"]))

        st.info(str(wynik["opis_stanu"]))

        if wynik["aktywne_wahadla"]:
            st.warning(
                "Aktywna przesłanka wahadłowa: "
                + "; ".join(wynik["aktywne_wahadla"])
                + ". Model zwiększył wagę historycznych korekt o przeciwnym znaku."
            )

        st.divider()
        st.subheader("Historyczna powtarzalność stanów")

        kol_a, kol_b, kol_c = st.columns(3)
        with kol_a:
            st.metric("Kompresja dośrodkowa", f"{stany['kompresja_prawdopodobienstwo']:.1f}%")
            st.caption(f"{stany['kompresja_trafienia']} / {stany['kompresja_przypadki']} (próg: ≥ {stany['prog_duzego_rozstepu']:.1f})")
        with kol_b:
            st.metric("Ekspansja odśrodkowa", f"{stany['ekspansja_prawdopodobienstwo']:.1f}%")
            st.caption(f"{stany['ekspansja_trafienia']} / {stany['ekspansja_przypadki']} (próg: ≤ {stany['prog_malego_rozstepu']:.1f})")
        with kol_c:
            wahadlo = stany["wahadlo"]
            wszystkie_przypadki = sum(int(w["przypadki"]) for w in wahadlo.values())
            wszystkie_korekty = sum(int(w["korekty"]) for w in wahadlo.values())
            st.metric("Korekta wahadłowa", f"{bezpieczny_procent(wszystkie_korekty, wszystkie_przypadki):.1f}%")
            st.caption(f"{wszystkie_korekty} korekt na {wszystkie_przypadki} dużych skoków.")

        tabela_wahadla = pd.DataFrame(
            [
                {
                    "Pozycja": pozycja,
                    "Duże skoki": dane["przypadki"],
                    "Korekty przeciwnego znaku": dane["korekty"],
                    "Prawdopodobieństwo [%]": round(float(dane["prawdopodobieństwo"]), 1),
                }
                for pozycja, dane in stany["wahadlo"].items()
            ]
        )
        st.dataframe(tabela_wahadla, width="stretch", hide_index=True)

        st.divider()
        st.subheader("Najbardziej prawdopodobne gradienty")

        tabela_predykcji = pd.DataFrame(
            {
                "Pozycja": [f"P{i}" for i in range(1, 7)],
                "Ostatnia liczba": wynik["liczby_ostatnie"],
                "Sugerowany skok": [f"{skok:+d}" for skok in wynik["przewidywane_skoki"]],
                "Liczba finalna": wynik["zestaw"],
            }
        )
        st.dataframe(tabela_predykcji, width="stretch", hide_index=True)

        st.success(f"Sugerowany zestaw heurystyczny: **{formatuj_zestaw(wynik['zestaw'])}**")


if __name__ == "__main__":
    pokaz_aplikacje()
