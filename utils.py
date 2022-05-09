# %%
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# %%
FIGSIZE_WIDE = (8, 6)
FIGSIZE_SQUARE = (6, 6)


# %%
def filter_selected_timeline(src_df, time_col="data_monday", **kwargs):

    # agregacja wszystkiego po czasie - żeby mieć bazę
    all_time = src_df[[time_col, "liczba"]].groupby(time_col).sum().reset_index()
    all_time.columns = [time_col, "liczba_total"]

    # filtrowanie po kolejnych kolumnach
    selected = src_df.copy()
    for k, v in kwargs.items():
        if type(v) == list:
            selected = selected[selected[k].isin(v)]
        else:
            selected = selected[selected[k].isin([v])]

    # agregacja wyfiltrowanego wyniku
    selected_time = selected[[time_col, "liczba"]].groupby(time_col).sum().reset_index()

    # złączenie bazy i wyfiltrowanych danych + policzenie %
    plot_data = pd.merge(
        all_time, selected_time, how="left", left_on=time_col, right_on=time_col
    )
    plot_data["liczba"] = plot_data["liczba"].fillna(0)
    plot_data = plot_data[plot_data["liczba"] != 0]
    # plot_data['liczba'] = plot_data['liczba'].astype(int)
    plot_data["liczba_procent"] = 100 * plot_data["liczba"] / plot_data["liczba_total"]

    return plot_data


def plot_selected_timeline(
    df, values=True, full_precent=False, axis_title="Liczba osób zakażonych"
):
    time_col = df.columns[0]
    fig, ax = plt.subplots(1, figsize=FIGSIZE_WIDE, facecolor="white")
    if values:
        sns.lineplot(
            data=df,
            x=time_col,
            y="liczba_total",
            ax=ax,
            linewidth=1.2,
            color="darkgray",
        )
        sns.lineplot(data=df, x=time_col, y="liczba", ax=ax, linewidth=2, color="red")
        # if len(df["liczba"]):
        #     max_value = max(df["liczba"])
        # else:
        #     max_value = 100
    else:
        sns.lineplot(
            data=df, x=time_col, y="liczba_procent", ax=ax, linewidth=2, color="red"
        )
        # if len(df["liczba"]):
        #     max_value = max(df["liczba_procent"])
        # else:
        #     max_value = 100
        if full_precent:
            ax.set_ylim(0, 100)
    ax.patch.set_alpha(0.0)
    ax.set_xlabel("")

    # if max_value > 10_000:
    #     y_ticks = ax.get_yticks().tolist()
    #     ax.set_yticks(y_ticks)
    #     ax.set_yticklabels([f"{x/1000:.0f}" for x in y_ticks])
    #     axis_title = axis_title + "\n(w tysiącach)"

    ax.set_ylabel(axis_title)
    return fig


def prepare_map_data(mapa, data, left_on="JPT_KOD_JE", right_on="teryt_pow"):
    # połączenie danych mapowych z danymi per powiat
    dane_mapa = pd.merge(mapa, data, how="left", left_on=left_on, right_on=right_on)
    return dane_mapa


def filter_selected_map(src_df, **kwargs):

    # agregacja wszystkiego po powiecie - żeby mieć bazę
    all_time = src_df[["teryt_pow", "liczba"]].groupby("teryt_pow").sum().reset_index()
    all_time.columns = ["teryt_pow", "liczba_total"]

    # filtrowanie po kolejnych kolumnach
    selected = src_df.copy()
    for k, v in kwargs.items():
        if type(v) == list:
            selected = selected[selected[k].isin(v)]
        else:
            selected = selected[selected[k].isin([v])]

    # agregacja wyfiltrowanego wyniku
    selected_time = (
        selected[["teryt_pow", "liczba"]].groupby("teryt_pow").sum().reset_index()
    )

    # złączenie bazy i wyfiltrowanych danych + policzenie %
    plot_data = pd.merge(
        all_time, selected_time, how="left", left_on="teryt_pow", right_on="teryt_pow"
    )
    plot_data["liczba"] = plot_data["liczba"].fillna(0)
    # plot_data['liczba'] = plot_data['liczba'].astype(int)
    plot_data = plot_data[plot_data["liczba"] != 0]
    plot_data["liczba_procent"] = 100 * plot_data["liczba"] / plot_data["liczba_total"]

    return plot_data


def plot_selected_map(
    dane, mapa_p, mapa_w, values=True, legend_title="Liczba osób zakażonych"
):
    dane_mapa = prepare_map_data(mapa_p, dane)

    # przygotowanie statycznego obrazka
    fig, ax = plt.subplots(1, figsize=FIGSIZE_SQUARE)

    # baza z szarymi powiatami (domyślnie brak danych)
    mapa_p.plot(ax=ax, linewidth=0.8, edgecolor="gray", facecolor="lightgray")

    # powiaty z danymi
    legend_kwds = {"label": legend_title, "orientation": "horizontal"}
    if values:
        dane_mapa.plot(
            ax=ax,
            column="liczba",
            cmap="YlOrRd",
            linewidth=0.8,
            edgecolor="gray",
            legend=True,
            legend_kwds=legend_kwds,
        )
    else:
        dane_mapa.plot(
            ax=ax,
            column="liczba_procent",
            cmap="YlOrRd",
            linewidth=0.8,
            edgecolor="gray",
            legend=True,
            legend_kwds=legend_kwds,
        )

    # granice województw
    mapa_w.plot(ax=ax, linewidth=1.2, edgecolor="black", facecolor="none")

    ax.axis("off")

    ax.patch.set_alpha(0.0)
    return fig
