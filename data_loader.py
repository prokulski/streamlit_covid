# %%
from os import remove
from typing import List

import geopandas as gpd
import pandas as pd
import requests

# %%
MAPS_PATH = "../../dane/mapy_shp/"

ZAKAZENIA_URL = (
    "https://api.dane.gov.pl/resources/36277,zakazenia-z-powodu-covid-19/file"
)
ZAKAZENIA_COLS = [
    "data_rap_zakazenia",
    "teryt_pow",
    "plec",
    "wiek",
    "kat_wiek",
    "producent",
    "dawka_ost",
    "liczba_zaraportowanych_zakazonych",
]
ZAKAZENIA_PKL = "data/zakazenia.pkl"

ZGONY_URL = "https://api.dane.gov.pl/resources/36278,zgony-z-powodu-covid-19/file"
ZGONY_COLS = [
    "data_rap_zgonu",
    "teryt_pow",
    "plec",
    "wiek",
    "kat_wiek",
    "producent",
    "dawka_ost",
    "liczba_zaraportowanych_zgonow",
]
ZGONY_PKL = "data/zgony.pkl"

TEMP_FILE = "data/tmp_file.csv"


# %%
def download_csv(url: str, cols: List[str]) -> pd.DataFrame:
    res = requests.get(url)
    if res.status_code != 200:
        raise ValueError

    with open(TEMP_FILE, "wb") as f:
        f.write(res.content)

    df = pd.read_csv(
        TEMP_FILE, sep=";", usecols=cols, date_parser=cols[0], engine="pyarrow"
    )

    remove(TEMP_FILE)
    return df


def find_age_category(i: int) -> str:
    kat_wiek = {
        "0 - 4": (0, 4),
        "5 - 9": (5, 9),
        "10 - 14": (10, 14),
        "15 - 19": (15, 19),
        "20 - 24": (20, 24),
        "25 - 29": (25, 29),
        "30 - 34": (30, 34),
        "35 - 39": (35, 39),
        "40 - 44": (40, 44),
        "45 - 49": (45, 49),
        "50 - 54": (50, 54),
        "55 - 59": (55, 59),
        "60 - 64": (60, 64),
        "65 - 69": (65, 69),
        "70 - 74": (70, 74),
        "75 - 79": (75, 79),
        "80 - 84": (80, 84),
        "85 i więcej": (85, 999),
    }

    for k, v in kat_wiek.items():
        if v[0] <= i <= v[1]:
            break
    return k


def clean_data(df_org: pd.DataFrame) -> pd.DataFrame:

    weekdays = {
        "Monday": "poniedziałek",
        "Tuesday": "wtorek",
        "Wednesday": "środa",
        "Thursday": "czwartek",
        "Friday": "piątek",
        "Saturday": "sobota",
        "Sunday": "niedziela",
    }

    print(df_org.columns)

    df = df_org.copy()

    df.columns = [
        "data",
        "teryt_pow",
        "plec",
        "wiek",
        "kat_wiek",
        "producent",
        "dawka_ost",
        "liczba",
    ]

    df["producent"] = df["producent"].fillna("brak szczepienia")
    df["dawka_ost"] = df["dawka_ost"].fillna("brak")
    df["teryt_pow"] = df["teryt_pow"].apply(
        lambda i: f"{int(i):04}" if not pd.isna(i) else "0000"
    )
    df["teryt_woj"] = df["teryt_pow"].apply(lambda s: s[:2])

    df["wiek"] = df["wiek"].fillna(0).astype(int)
    kat_wiek_map = {i: find_age_category(i) for i in range(max(df["wiek"]))}
    kat_wiek_map["DB"] = "DB"
    kat_wiek_map["95+"] = "DB"
    df["kat_wiek"] = df["wiek"].map(kat_wiek_map)

    df["data"] = pd.to_datetime(df["data"])
    df["data_month"] = df["data"].dt.month
    df["data_week"] = df["data"].dt.isocalendar().week
    df["data_weekday"] = df["data"].dt.day_name().map(weekdays)
    df["data_monday"] = df["data"] - pd.to_timedelta(df["data"].dt.weekday, unit="days")

    df = df[df["plec"].isin(["K", "M"])]
    return df


def process_data(url: str, cols: List[str], output_pickle: str) -> None:
    print("Procesuję dane o zakażeniach:")

    df = download_csv(url, cols)
    print(f"\tplik {url} pobrany")

    df = clean_data(df)
    print(f"\tdane przygotowane - zakres dat: {min(df['data'])} - {max(df['data'])}")

    df.to_pickle(output_pickle)
    print(f"\tplik {output_pickle} zapisany")


def process_map_files(from_file, to_file):
    print(f"Procesuję mapę {from_file}")

    mapa_pow = gpd.read_file(MAPS_PATH + from_file)
    mapa_pow = mapa_pow[["JPT_KOD_JE", "JPT_NAZWA_", "geometry"]]
    print(f"\tplik {from_file} wczytany")

    mapa_pow["JPT_NAZWA_"] = (
        mapa_pow["JPT_NAZWA_"].str.encode("latin1").str.decode("utf8")
    )
    mapa_pow_plt = mapa_pow.to_crs(epsg=2180)
    mapa_pow_plt.geometry = mapa_pow_plt.geometry.simplify(2000)
    print("\tdane przetworzone")

    mapa_pow_plt.to_pickle(to_file)
    print(f"\tplik {to_file} zapisany")


# %%
if __name__ == "__main__":
    process_data(ZGONY_URL, ZGONY_COLS, ZGONY_PKL)
    process_data(ZAKAZENIA_URL, ZAKAZENIA_COLS, ZAKAZENIA_PKL)

    # process_map_files("powiaty.shp", "data/mapa_powiaty_plt.pkl")
    # process_map_files("wojewodztwa.shp", "data/mapa_wojewodztwa_plt.pkl")
