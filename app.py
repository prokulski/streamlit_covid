# %%
import logging

import pandas as pd
import seaborn as sns
import streamlit as st

from utils import (
    filter_selected_map,
    filter_selected_timeline,
    plot_selected_map,
    plot_selected_timeline,
)

# from streamlit.report_thread import get_report_ctx


# %%
logger = logging.Logger(__name__)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

fh = logging.FileHandler("app.log")
fh.setFormatter(formatter)
logger.addHandler(fh)

sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.ERROR)
logger.addHandler(sh)


# %%
TIME_COL = "data"
# TIME_COL = 'data_monday'

# %%
sns.set_theme(style="ticks")


# %%
st.set_page_config(page_title="Statystyki zakażeń COVID-19 w 2021 roku", layout="wide")

# %%
session_id = "ses_id"  # get_report_ctx().session_id

logger.info(f"{session_id=} Skrypt uruchomiony / wykonana akcja na wybierakach")

# %%
@st.cache
def load_data():
    # wczytanie stałych danych
    logger.info(f"{session_id=} Zaczynam wczytywanie danych")
    # liczba zakażonych
    zakazenia = pd.read_pickle("data/zakazenia.pkl")
    zakazenia = zakazenia[zakazenia["plec"].isin(["K", "M"])]
    logger.info(f"{session_id=} Dane o zakażeniach wczytane")

    zgony = pd.read_pickle("data/zgony.pkl")
    zgony = zgony[zgony["plec"].isin(["K", "M"])]
    logger.info(f"{session_id=} Dane o zgonach wczytane")

    # liczba ludności w powiatach do skalowania do procentów
    ludnosc = pd.read_csv("data/ludnosc_powiaty_grupa_wiekowa_plec.csv")
    ludnosc["teryt_pow"] = ludnosc["teryt_pow"].apply(
        lambda i: f"{int(i):04}" if not pd.isna(i) else "0000"
    )

    # mapki
    mapa_pow_plt = pd.read_pickle("data/mapa_powiaty_plt.pkl")
    mapa_woj_plt = pd.read_pickle("data/mapa_wojewodztwa_plt.pkl")
    logger.info(f"{session_id=} Mapy wczytane")

    return zakazenia, zgony, ludnosc, mapa_pow_plt, mapa_woj_plt


# %%
zakazenia, zgony, ludnosc, mapa_pow_plt, mapa_woj_plt = load_data()

dataset = st.sidebar.radio("Zbiór danych", ("Zakażenia", "Zgony"))
time_col = st.sidebar.radio("Dane", ("dzienne", "tygodniowe"))
if not time_col:
    time_col = TIME_COL
    logger.info(f"{session_id=} Zmiana rozdzielczości danych na {time_col=}")

plec = st.sidebar.multiselect("Płeć", ("K", "M"))
kat_wiek = st.sidebar.multiselect(
    "Kategoria wiekowa",
    (
        "0 - 4",
        "5 - 9",
        "10 - 14",
        "15 - 19",
        "20 - 24",
        "25 - 29",
        "30 - 34",
        "35 - 39",
        "40 - 44",
        "45 - 49",
        "50 - 54",
        "55 - 59",
        "60 - 64",
        "65 - 69",
        "70 - 74",
        "75 - 79",
        "80 - 84",
        "85 i więcej",
    ),
)
producent = st.sidebar.multiselect(
    "Szczepionka",
    [
        "brak szczepienia",
        "Astra Zeneca",
        "Johnson&Johnson",
        "Moderna",
        "Pfizer",
        "brak danych",
    ],
)


@st.cache
def prepare_data(
    p_dataset="Zakażenia",
    p_time_col=TIME_COL,
    p_plec=[],
    p_kat_wiek=[],
    p_producent=[],
):
    logger.info(
        f"{session_id=} Wywołana funkcja prepare_data(): {p_dataset=}, {p_plec=}, {p_kat_wiek=}, {p_producent=}"
    )
    # filtrowanie danych
    filtry = {}

    if p_plec:
        logger.info(f"{session_id=} Filtr: {p_plec=}")
        filtry["plec"] = p_plec
    if p_kat_wiek:
        logger.info(f"{session_id=} Filtr: {p_kat_wiek=}")
        filtry["kat_wiek"] = p_kat_wiek
    if p_producent:
        logger.info(f"{session_id=} Filtr: {p_producent=}")
        filtry["producent"] = p_producent

    if p_time_col == "dzienne":
        logger.info(
            f"{session_id=} Zmiana rozdzielczości danych w prepare_data() na {time_col=}"
        )
        p_time_col = "data"
    else:
        logger.info(
            f"{session_id=} Zmiana rozdzielczości danych w prepare_data() na {time_col=}"
        )
        p_time_col = "data_monday"

    if p_dataset == "Zakażenia":
        plot_df_time = filter_selected_timeline(
            zakazenia, time_col=p_time_col, **filtry
        )
        logger.info(f"{session_id=} Przefiltrowane dane czasowe o zakażeniach")
        plot_df_map = filter_selected_map(zakazenia, **filtry)
        logger.info(f"{session_id=} Przefiltrowane dane geograficzne o zakażeniach")
    else:
        plot_df_time = filter_selected_timeline(zgony, time_col=p_time_col, **filtry)
        logger.info(f"{session_id=} Przefiltrowane dane czasowe o zgonach")
        plot_df_map = filter_selected_map(zgony, **filtry)
        logger.info(f"{session_id=} Przefiltrowane dane geograficzne o zgonach")

    return plot_df_time, plot_df_map


# %%
plot_df_time, plot_df_map = prepare_data(dataset, time_col, plec, kat_wiek, producent)

df_time = plot_df_time.copy()
df_time.columns = ["Data", "Liczba wszystkich", "Liczba w wybranej grupie", "%"]
df_time["Data"] = df_time["Data"].apply(lambda dt: str(dt)[:11])


df_mapa = pd.merge(
    plot_df_map,
    mapa_pow_plt[["JPT_KOD_JE", "JPT_NAZWA_"]],
    left_on="teryt_pow",
    right_on="JPT_KOD_JE",
)

df_mapa = df_mapa[["JPT_NAZWA_", "liczba_total", "liczba", "liczba_procent"]]
df_mapa.columns = ["Powiat", "Liczba wszystkich", "Liczba w wybranej grupie", "%"]

# %%
# rysowanie timeline'ów
fig1 = plot_selected_timeline(
    plot_df_time, values=True, full_precent=True, axis_title="Liczba osób"
)
fig2 = plot_selected_timeline(
    plot_df_time, values=False, full_precent=False, axis_title="Procent"
)

# rysowanie mapek
fig3 = plot_selected_map(
    plot_df_map, mapa_pow_plt, mapa_woj_plt, values=True, legend_title="Liczba osób"
)
fig4 = plot_selected_map(
    plot_df_map, mapa_pow_plt, mapa_woj_plt, values=False, legend_title="Procent"
)

# %%
st.title(f"Statystyki COVID-19 w 2021 roku - {dataset.lower()}")


row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.header("Liczba osób")
    st.pyplot(fig1, use_container_width=True)

with row1_col2:
    st.header("Wybrana grupa (procent)")
    st.pyplot(fig2, use_container_width=True)


row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.header("Liczba osób")
    st.pyplot(fig3, use_container_width=True)

with row2_col2:
    st.header("Wybrana grupa (procent)")
    st.pyplot(fig4, use_container_width=True)


row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.header("Dane szczegółowe (ujęcie czasowe)")
    st.dataframe(df_time[df_time["Liczba w wybranej grupie"] != 0])

with row3_col2:
    st.header("Dane szczegółowe (ujęcie geograficzne)")
    st.dataframe(df_mapa[df_mapa["Liczba w wybranej grupie"] != 0])
