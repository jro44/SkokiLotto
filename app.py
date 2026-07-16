"""
Główny kontroler aplikacji LottoHistoryAI.
Zarządza stanem interfejsu, nawigacją zakładkami oraz koordynacją modułów.
Wersja zintegrowana z silnikiem dynamicznego izomorfizmu układu (Karta 4).
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st

# Importy natywnych komponentów strukturalnych projektu
from parser_mht import ParserMHTLotto
from analiza_skokow import AnalizatorSkokow
from statystyki import AnalizatorStatystyczny
from historyczny_blizniak import SilnikBlizniaka
from predykcja import GeneratorPredykcji
from generatory import GeneratorKuponow
from wykresy import KreatorWykresow
from analiza_ukladu import AnalizatorUkladuHistorii
from utils import formatuj_zestaw, pobierz_logger

logger = pobierz_logger("GłównyKontroler")

# Definicja bezwzględnej ścieżki do lokalnego pliku bazy danych MHT
SCIEZKA_BAZY = Path(__file__).resolve().parent / "Wyniki.mht"

@st.cache_data(show_spinner=False)
def zaladuj_i_parsuj_baze_lotto(sciezka: Path) -> pd.DataFrame:
    """Bezpieczny kontener pamięci podręcznej dla parsera plików tekstowych MHT."""
    if not sciezka.exists():
        return pd.DataFrame()
    parser_lotto = ParserMHTLotto(sciezka)
    return parser_lotto.parsuj()

def main():
    st.set_page_config(
        page_title="LottoHistoryAI - Gradienty i Izomorfizmy",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📊 LottoHistoryAI")
    st.caption("Zaawansowany system wielomodułowy analizy trendów, przyrostów pozycyjnych i izomorfizmów")

    # Wczytanie i weryfikacja integralności bazy danych offline
    df_baza = zaladuj_i_parsuj_baze_lotto(SCIEZKA_BAZY)

    if df_baza.empty:
        st.error("❌ Błąd krytyczny: Nie odnaleziono lub nie udało się sparsować pliku 'Wyniki.mht' w folderze aplikacji.")
        st.info("Upewnij się, że plik z bazą losowań znajduje się w tym samym katalogu co 'app.py' i odśwież stronę.")
        st.stop()

    # --- PANEL BOCZNY (SIDEBAR) ---
    with st.sidebar:
        st.header("⚙️ Ustawienia Systemowe")
        st.success("Baza danych Lotto załadowana poprawnie")
        st.metric("Wszystkich losowań w bazie", len(df_baza))
        
        # Wyznaczenie zakresów granicznych zbioru danych
        najnowsze_nr = int(df_baza["Numer Losowania"].max())
        najstarsze_nr = int(df_baza["Numer Losowania"].min())
        
        st.write(f"**Najnowsze losowanie:** {najnowsze_nr}")
        st.write(f"**Najstarsze losowanie:** {najstarsze_nr}")

        # Konfiguracja suwaka głębokości okna czasowego analizy trendów
        opcje_zakresu = [o for o in ["100", "250", "500"] if len(df_baza) >= int(o)]
        opcje_zakresu.append("Wszystkie")
        
        wybor_zakresu = st.select_slider(
            "Zakres analizy historycznej", 
            options=opcje_zakresu, 
            value=opcje_zakresu[-1]
        )

    # Filtrowanie okna danych wejściowych zgodnie z decyzją użytkownika
    if wybor_zakresu == "Wszystkie":
        df_analiza = df_baza.copy()
    else:
        df_analiza = df_baza.head(int(wybor_zakresu)).copy()

    # Inicjalizacja instancji obiektów biznesowych z warstwy modułowej
    df_skoki = AnalizatorSkokow.oblicz_skoki(df_analiza)
    df_przejscia = AnalizatorSkokow.przygotuj_przejscia(df_analiza)
    stany_maszyny = AnalizatorStatystyczny.analizuj_stany_maszyny(df_przejscia)
    
    silnik_blizniaka = SilnikBlizniaka(df_analiza)
    silnik_predykcji = GeneratorPredykcji(df_analiza)
    silnik_izomorfizmu = AnalizatorUkladuHistorii(df_analiza)

    # --- RENDEROWANIE INTERFEJSU UŻYTKOWNIKA ---
    # Definicja 11 dedykowanych kart (w tym nowa karta izomorfizmu strukturalnego)
    tabs = st.tabs([
        "1. Surowe Dane", 
        "2. Mapa Skoków", 
        "3. Statystyki Rozkładu", 
        "4. Izomorfizm Układu", 
        "5. Gorące/Zimne", 
        "6. Pary i Trójki", 
        "7. Stany Maszyny", 
        "8. Historyczny Bliźniak", 
        "9. Analiza Następstw", 
        "10. Predykcja", 
        "11. Generatory"
    ])

    # Karta 1: Surowe Dane
    with tabs[0]:
        st.subheader("Baza danych wejściowych losowań")
        sortowanie = st.radio("Kierunek prezentacji osi czasu:", ["Od najnowszych", "Od najstarszych"], horizontal=True, key="r_raw")
        df_widok = df_analiza.sort_values("Numer Losowania", ascending=(sortowanie == "Od najstarszych"))
        st.dataframe(df_widok, use_container_width=True, hide_index=True)

    # Karta 2: Mapa Skoków
    with tabs[1]:
        st.subheader("Surowa mapa gradientów (przyrosty wartości na pozycjach)")
        st.write("Wartości prezentują przesunięcie kuli na danej pozycji względem poprzedniego losowania chronologicznego.")
        st.dataframe(df_skoki.sort_values("Numer Losowania", ascending=False), use_container_width=True, hide_index=True)

    # Karta 3: Statystyki Rozkładu
    with tabs[2]:
        st.subheader("Parametry statystyczne i empiryczne gęstości")
        st.table(AnalizatorStatystyczny.generuj_podstawowe(df_analiza))
        
        col_s = st.selectbox("Wybierz pozycję przyrostu do wizualizacji gęstości rozkładu:", [f"Skok_P{i}" for i in range(1, 7)])
        st.plotly_chart(KreatorWykresow.histogram_skoku(df_skoki, col_s), use_container_width=True)

    # Karta 4: Dynamiczny Izomorfizm Układu (Nowy Moduł)
    with tabs[3]:
        st.subheader("🔬 Analiza izomorfizmu geometrycznego i dynamiczna aktualizacja")
        st.write(
            "Ten moduł pobiera ostatni zrealizowany wynik, bada jego cechy geometryczne "
            "(parzystość, dystrybucję w dekadach, rozpiętość rozstępu) i wyszukuje w historii losowania "
            "o **identycznym układzie**. Następnie pobiera ich stany t+1 i aktualizuje je (mapuje) "
            "w oparciu o aktualnie najsilniejsze liczby bieżącego cyklu maszynowego."
        )

        # Pobieramy 15 najgorętszych kul z wybranego zakresu jako wektor wagowy aktualizacji
        wszystkie_kule = df_analiza[[f"P{i}" for i in range(1, 7)]].values.flatten()
        gorace_kule_aktualizacji = list(pd.Series(wszystkie_kule).value_counts().head(15).index)

        # Pobranie parametrów wejściowych z najnowszego losowania bazy
        wiersz_wzorcowy = df_analiza.sort_values("Numer Losowania", ascending=False).iloc[0]
        liczby_wzorcowe = [int(wiersz_wzorcowy[f"P{i}"]) for i in range(1, 7)]

        st.info(f"📋 **Identyfikator profilu wzorcowego (Losowanie nr {int(wiersz_wzorcowy['Numer Losowania'])}):** {liczby_wzorcowe}")

        # Wywołanie potoku przetwarzania z modułu analiza_ukladu
        wynik_izomorfizmu = silnik_izomorfizmu.analizuj_i_mapuj_nastepstwa(liczby_wzorcowe, gorace_kule_aktualizacji)

        if wynik_izomorfizmu["sukces"]:
            st.write("**Zidentyfikowane identyczne konfiguracje strukturalne w przeszłości:**")
            st.dataframe(wynik_izomorfizmu["blizniaki"], use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🔮 Wynikowa predykcja adaptacyjna układu:")
            st.markdown(
                "Zestaw wygenerowany poprzez nałożenie aktualnego trendu częstości maszynowej "
                "na historyczne rozkłady przejść po identycznych stanach geometrycznych:"
            )
            st.success(f"Sugerowany zestaw zaktualizowany: **{formatuj_zestaw(wynik_izomorfizmu['zestaw_aktualizowany'])}**")
        else:
            st.warning(wynik_izomorfizmu["komunikat"])

    # Karta 5: Gorące/Zimne
    with tabs[4]:
        st.subheader("Analiza częstotliwości: Gorące i Zimne Liczby")
        horyzont = st.selectbox("Okno obserwacji bębna:", [20, 50, 100, len(df_baza)], format_func=lambda x: f"Ostatnie {x} losowań" if x != len(df_baza) else "Pełna historia")
        czestosc = AnalizatorStatystyczny.oblicz_czestosc_liczb(df_baza, horyzont)
        
        c_col1, c_col2 = st.columns(2)
        c_col1.write("**Top 10 najczęściej losowanych (Gorące):**")
        c_col1.dataframe(czestosc.sort_values(ascending=False).head(10).rename("Trafienia"), use_container_width=True)
        c_col2.write("**Top 10 najrzadziej losowanych (Zimne):**")
        c_col2.dataframe(czestosc.sort_values(ascending=True).head(10).rename("Trafienia"), use_container_width=True)
        
        st.plotly_chart(KreatorWykresow.wykres_czestosci(czestosc, f"Globalny rozkład gęstości wystąpień kul (Okno: {horyzont} losowań)"), use_container_width=True)

    # Karta 6: Pary i Trójki
    with tabs[5]:
        st.subheader("Identyfikacja najczęstszych asocjacji wielokrotnych")
        pary, trojki = AnalizatorStatystyczny.znajdz_pary_i_trojki(df_analiza)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.write("**Najpopularniejsze Pary liczbowe:**")
            st.dataframe(pary, use_container_width=True, hide_index=True)
        with col_p2:
            st.write("**Najpopularniejsze Trójki liczbowe:**")
            st.dataframe(trojki, use_container_width=True, hide_index=True)

    # Karta 7: Stany Maszyny
    with tabs[6]:
        st.subheader("Klasyfikacja entropijna bębna losującego")
        st.dataframe(AnalizatorStatystyczny.analizuj_stany_maszyny(df_analiza).tail(20), use_container_width=True, hide_index=True)

    # Karta 8: Historyczny Bliźniak
    with tabs[7]:
        st.subheader("Wyszukiwanie profilowe (Historyczny Bliźniak)")
        st.write("Wprowadź zestaw unikalnych liczb, aby wyliczyć odległość profilową od stanów historycznych.")
        inp_cols = st.columns(6)
        zestaw_uzytkownika = [inp_cols[i].number_input(f"Liczba {i+1}", 1, 49, i+1, key=f"user_in_{i}") for i in range(6)]
        
        if len(set(zestaw_uzytkownika)) == 6:
            wyniki_blizniakow = silnik_blizniaka.znajdz_blizniakow(zestaw_uzytkownika, top_n=10)
            st.dataframe(pd.DataFrame(wyniki_blizniakow), use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Wszystkie wprowadzone liczby muszą być całkowicie unikalne!")

    # Karta 9: Analiza Następstw
    with tabs[8]:
        st.subheader("Analiza następstw stanów t+1 po najbliższych bliźniakach")
        ostatni_row = df_baza.iloc[0]
        liczby_realne = [int(ostatni_row[f"P{i}"]) for i in range(1, 7)]
        st.info(f"Analiza uruchomiona automatycznie dla ostatniego wyniku historycznego: {liczby_realne}")
        
        blizniacy_nastepstw = silnik_blizniaka.znajdz_blizniakow(liczby_realne, top_n=5)
        lista_nastepnych = []
        for b in blizniacy_nastepstw:
            wiersz_n = df_baza[df_baza["Numer Losowania"] == b["Numer"] + 1]
            if not wiersz_n.empty:
                lista_nastepnych.append({
                    "Po bliźniaku nr": b["Numer"],
                    "Zgodność profilu": f"{b['Podobienstwo_Score']}%",
                    "Wynik w losowaniu t+1": [int(wiersz_n.iloc[0][f"P{i}"]) for i in range(1, 7)]
                })
        if lista_nastepnych:
            st.dataframe(pd.DataFrame(lista_nastepnych), use_container_width=True, hide_index=True)
        else:
            st.write("Brak danych o następstwach (ostatnie losowanie w bazie nie posiada punktu t+1).")

    # Karta 10: Predykcja
    with tabs[9]:
        st.subheader("Wnioskowanie probabilistyczne i kombinacje hybrydowe")
        
        p1 = silnik_predykcji.generuj_predykcje_blizniacy(silnik_blizniaka)
        p2 = silnik_predykcji.generuj_predykcje_skoki()
        p3 = silnik_predykcji.generuj_predykcje_hybrydowa()
        
        st.subheader("🔮 Prediction #1 (Metoda Bliźniaków Profile-Similarity)")
        st.success(f"Sugerowany zestaw: **{formatuj_zestaw(p1)}**")
        
        st.subheader("🔮 Prediction #2 (Metoda Ekstrapolacji Średniego Skoku)")
        st.success(f"Sugerowany zestaw: **{formatuj_zestaw(p2)}**")
        
        st.subheader("🔮 Prediction #3 (Wagowy System Hybrydowy)")
        st.success(f"Sugerowany zestaw: **{formatuj_zestaw(p3)}**")

    # Karta 11: Generatory
    with tabs[10]:
        st.subheader("Zautomatyzowane systemy filtracji kuponów")
        c_g1, c_g2, c_g3 = st.columns(3)
        
        with c_g1:
            st.markdown("### 🏆 Złoty Strzał")
            st.caption("Filtruje kombinacje z puli najczęściej padających kul z zachowaniem optymalnego przedziału sumy.")
            if st.button("Generuj Złoty Strzał", key="btn_zs"):
                st.code(formatuj_zestaw(GeneratorKuponow.generuj_zloty_strzal(df_analiza)))
                
        with c_g2:
            st.markdown("### 📐 Statystyczny Chybił Trafił")
            st.caption("Losuje zakład z pełnego zakresu, automatycznie eliminując anomalie (ciągi kul, brak parzystości).")
            if st.button("Generuj Statystyczny", key="btn_cts"):
                st.code(formatuj_zestaw(GeneratorKuponow.generuj_chybil_trafil_statystyczny(df_analiza)))
                
        with c_g3:
            st.markdown("### 🎲 Totalny Chybił Trafił")
            st.caption("Czysta losowość stochastyczna, bez jakiejkolwiek ingerencji filtrów matematycznych.")
            if st.button("Generuj Losowy Kupon", key="btn_tct"):
                st.code(formatuj_zestaw(GeneratorKuponow.generuj_totalny_chybil_trafil()))

if __name__ == "__main__":
    main()
