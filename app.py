"""
Główny kontroler aplikacji LottoHistoryAI.
Zarządza stanem, interfejsem użytkownika i dystrybucją potoków danych.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st

from parser_mht import ParserMHTLotto
from analiza_skokow import AnalizatorSkokow
from statystyki import AnalizatorStatystyczny
from historyczny_blizniak import SilnikBlizniaka
from predykcja import GeneratorPredykcji
from generatory import GeneratorKuponow
from wykresy import KreatorWykresow
from utils import formatuj_zestaw

# Wyznaczenie bezwzględnej ścieżki do lokalnego pliku bazy danych
SCIEZKA_BAZY = Path(__file__).resolve().parent / "Wyniki.mht"

@st.cache_data(show_spinner=False)
def zaladuj_oraz_parsuj_baze(sciezka: Path) -> pd.DataFrame:
    """Bezpieczny kontener pamięci podręcznej dla parsowania pliku źródłowego."""
    if not sciezka.exists():
        return pd.DataFrame()
    parser = ParserMHTLotto(sciezka)
    return parser.parsuj()

def main():
    st.title("📊 LottoHistoryAI")
    st.caption("Zaawansowany system wielomodułowy analizy trendów i gradientów przesunięć")

    df_baza = zaladuj_oraz_parsuj_baze(SCIEZKA_BAZY)

    # Weryfikacja integralności pliku wejściowego
    if df_baza.empty:
        st.error("❌ Nie znaleziono pliku Wyniki.mht w katalogu głównym lub plik nie zawiera poprawnych wierszy danych.")
        st.info("Przenieś plik Wyniki.mht obok kodu źródłowego i odśwież aplikację.")
        st.stop()

    # --- PANEL BOCZNY (SIDEBAR) ---
    with st.sidebar:
        st.header("⚙️ Ustawienia Systemowe")
        st.success("Baza danych załadowana")
        st.metric("Wszystkich losowań w bazie", len(df_baza))
        st.write(f"**Najnowsze losowanie:** {int(df_baza['Numer Losowania'].max())}")
        st.write(f"**Najstarsze losowanie:** {int(df_baza['Numer Losowania'].min())}")

        opcje_zakresu = [o for o in ["100", "250", "500"] if len(df_baza) >= int(o)]
        opcje_zakresu.append("Wszystkie")
        
        wybor_zakresu = st.select_slider("Zakres analizy historycznej", options=opcje_zakresu, value=opcje_zakresu[-1])

    # Konfiguracja okna danych na osi czasu
    df_analiza = df_baza.copy() if wybor_zakresu == "Wszystkie" else df_baza.head(int(wybor_zakresu)).copy()

    # Inicjalizacja instancji obiektów biznesowych
    df_skoki = AnalizatorSkokow.oblicz_skoki(df_analiza)
    df_przejscia = AnalizatorSkokow.przygotuj_przejscia(df_analiza)
    stany_maszyny = AnalizatorStatystyczny.analizuj_stany_maszyny(df_przejscia)
    
    silnik_blizniaka = SilnikBlizniaka(df_analiza)
    silnik_predykcji = GeneratorPredykcji(df_analiza)

    # --- RENDEROWANIE KART INTERFEJSU ---
    tabs = st.tabs([
        "1. Surowe Dane", "2. Mapa Skoków", "3. Statystyki", "4. Gorące/Zimne", 
        "5. Pary i Trójki", "6. Stany Maszyny", "7. Historyczny Bliźniak", 
        "8. Analiza Następstw", "9. Predykcja", "10. Generatory"
    ])

    # Karta 1: Surowe Dane
    with tabs[0]:
        st.subheader("Baza danych wejściowych")
        sortowanie = st.radio("Kierunek prezentacji danych:", ["Od najnowszych", "Od najstarszych"], horizontal=True, key="r_raw")
        df_widok = df_analiza.sort_values("Numer Losowania", ascending=(sortowanie == "Od najstarszych"))
        st.dataframe(df_widok, width="stretch", hide_index=True)

    # Karta 2: Mapa Skoków
    with tabs[1]:
        st.subheader("Surowa mapa gradientów (przyrosty pozycji)")
        st.dataframe(df_skoki.sort_values("Numer Losowania", ascending=False), width="stretch", hide_index=True)

    # Karta 3: Statystyki
    with tabs[2]:
        st.subheader("Parametry statystyczne i rozkłady empiryczne")
        st.table(AnalizatorStatystyczny.generuj_podstawowe(df_analiza))
        col_s = st.selectbox("Wybierz kolumnę przesunięcia do analizy gęstości:", [f"Skok_P{i}" for i in range(1, 7)])
        st.plotly_chart(KreatorWykresow.histogram_skoku(df_skoki, col_s), width="stretch")

    # Karta 4: Gorące i Zimne Liczby
    with tabs[3]:
        st.subheader("Częstotliwość występowania poszczególnych liczb")
        horyzont = st.selectbox("Okno obserwacji:", [20, 50, 100, len(df_baza)], format_func=lambda x: f"Ostatnie {x} losowań" if x != len(df_baza) else "Pełny zbiór")
        czestosc = AnalizatorStatystyczny.oblicz_czestosc_liczb(df_baza, horyzont)
        st.plotly_chart(KreatorWykresow.wykres_czestosci(czestosc, f"Rozkład trafień (Horyzont: {horyzont})"), width="stretch")

    # Karta 5: Pary i Trójki
    with tabs[4]:
        st.subheader("Identyfikacja najczęstszych asocjacji wielokrotnych")
        pary, trojki = AnalizatorStatystyczny.znajdz_pary_i_trojki(df_analiza)
        c1, c2 = st.columns(2)
        c1.write("**Najczęstsze Pary:**")
        c1.dataframe(pary, width="stretch", hide_index=True)
        c2.write("**Najczęstsze Trójki:**")
        c2.dataframe(trojki, width="stretch", hide_index=True)

    # Karta 6: Analiza Stanów Maszyny
    with tabs[5]:
        st.subheader("Efektywność przejść i entropii rozstępów")
        st.info(f"Kwantylowy próg kompresji rozstępu wynosi: **≥ {stany_maszyny['prog_duzego']:.1f}**")
        st.write(f"- Skuteczność historyczna kompresji dośrodkowa: **{stany_maszyny['komp_proc']:.1f}%** ({stany_maszyny['komp_trafienia']}/{stany_maszyny['komp_przypadki']})")
        st.write(f"- Skuteczność historyczna ekspansji odśrodkowa: **{stany_maszyny['eksp_proc']:.1f}%** ({stany_maszyny['eksp_trafienia']}/{stany_maszyny['eksp_przypadki']})")

    # Karta 7: Historyczny Bliźniak
    with tabs[6]:
        st.subheader("Wyszukiwanie profili izomorficznych (Bliźniak)")
        inp_cols = st.columns(6)
        zestaw_uzytkownika = [inp_cols[i].number_input(f"Liczba {i+1}", 1, 49, i+1, key=f"inp_{i}") for i in range(6)]
        if len(set(zestaw_uzytkownika)) == 6:
            wyniki_b = silnik_blizniaka.znajdz_najbardziej_podobne(zestaw_uzytkownika, top_n=10)
            st.dataframe(pd.DataFrame(wyniki_b), width="stretch", hide_index=True)
        else:
            st.warning("Podane liczby muszą być unikalne!")

    # Karta 8: Analiza Następstw
    with tabs[7]:
        st.subheader("Analiza sekwencyjna następstw")
        najnowsze_wiersz = df_baza.iloc[0]
        ostatnie_realne = [int(najnowsze_wiersz[f"P{i}"]) for i in range(1, 7)]
        st.write(f"Profil następstw generowany automatycznie dla ostatniego losowania: **{ostatnie_realne}**")
        blizniacy_nastepstw = silnik_blizniaka.znajdz_najbardziej_podobne(ostatnie_realne, top_n=5)
        nastepstwa_rekordy = []
        for b in blizniacy_nastepstw:
            wiersz_n = df_baza[df_baza["Numer Losowania"] == b["Numer Bliźniaka"] + 1]
            if not wiersz_n.empty:
                nastepstwa_rekordy.append({
                    "Po bliźniaku nr": b["Numer Bliźniaka"],
                    "Wylosowano w t+1": str([int(wiersz_n.iloc[0][f"P{i}"]) for i in range(1, 7)])
                })
        st.dataframe(pd.DataFrame(nastepstwa_rekordy), width="stretch", hide_index=True)

    # Karta 9: Predykcja
    with tabs[8]:
        st.subheader("Generowanie rekomendacji metodami hybrydowymi")
        zestaw_skoki, skoki_raw = silnik_predykcji.generuj_zestaw_skokow(df_przejscia, stany_maszyny)
        zestaw_blizniaki = silnik_predykcji.generuj_zestaw_blizniakow(silnik_blizniaka)

        st.success(f"🔮 **Prediction #1 (Historical Twins):** {formatuj_zestaw(zestaw_blizniaki)}")
        st.success(f"🔮 **Prediction #2 (Jump Analysis):** {formatuj_zestaw(zestaw_skoki)} *(Sugerowane przyrosty: {skoki_raw})*")
        
        hybryda = sorted(list(set(zestaw_blizniaki[:3] + zestaw_skoki[:3])))
        while len(hybryda) < 6:
            for x in range(1, 50):
                if x not in hybryda:
                    hybryda.append(x)
                    break
        st.success(f"🔮 **Prediction #3 (Hybrid System):** {formatuj_zestaw(sorted(hybryda))}")

    # Karta 10: Generatory
    with tabs[9]:
        st.subheader("Zautomatyzowane generatory kuponów")
        c_g1, c_g2, c_g3 = st.columns(3)
        if c_g1.button("🔥 Wygeneruj: Złoty Strzał"):
            c_g1.code(formatuj_zestaw(GeneratorKuponow.zloty_strzal(df_analiza)))
        if c_g2.button("📐 Wygeneruj: Chybił Trafił Statystyczny"):
            c_g2.code(formatuj_zestaw(GeneratorKuponow.chybil_trafil_statystyczny()))
        if c_g3.button("🎲 Wygeneruj: Totalny Chybił Trafił"):
            c_g3.code(formatuj_zestaw(GeneratorKuponow.totalny_chybil_trafil()))

if __name__ == "__main__":
    main()
