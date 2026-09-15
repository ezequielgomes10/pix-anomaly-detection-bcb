import pandas as pd
import requests
import plotly.express as px


def carregar_dados_pix():
    url = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/EstatisticasFraudesPix(Database=@Database)?$format=json&@Database='202509'"
    resposta = requests.get(url, timeout=15)
    resposta.raise_for_status()
    return pd.DataFrame(resposta.json()["value"])


def preparar_base(pix):
    pix = pix[["AnoMes", "QtdePixcontestados", "PercentualdeDevolucao"]].copy()
    pix.columns = ["mes", "contestacoes", "devolucao"]
    pix["mes"] = pd.to_datetime(pix["mes"].astype(str), format="%Y%m")
    pix["contestacoes"] /= 1_000_000
    return pix.sort_values("mes").reset_index(drop=True)


def identificar_atipicos(pix, n_desvios=2):
    media = pix["contestacoes"].mean()
    desvio = pix["contestacoes"].std()
    limite_inferior = max(0, media - n_desvios * desvio)
    limite_superior = media + n_desvios * desvio
    pix["atipico"] = ~pix["contestacoes"].between(limite_inferior, limite_superior)
    return pix, media


def estilo(fig):
    fig.update_layout(
        template="plotly_white",
        width=950,
        height=400,
        showlegend=False,
        font=dict(family="Arial", size=12, color="#4B5563"),
        title_font=dict(size=18, color="#025C75"),
        margin=dict(l=50, r=30, t=75, b=45)
    )
    fig.update_xaxes(title=None, tickformat="%m/%Y", dtick="M1", showgrid=False)
    fig.update_yaxes(title=None, gridcolor="#EEF1F4", zeroline=False)
    fig.add_layout_image(
        source="https://upload.wikimedia.org/wikipedia/commons/9/96/Banco-central-do-brasil-logo.png",
        xref="paper",
        yref="paper",
        x=1,
        y=1.16,
        sizex=.15,
        sizey=.15,
        xanchor="right",
        yanchor="top"
    )


def plotar_contestacoes(pix, atipicos, media):
    fig = px.line(
        pix,
        x="mes",
        y="contestacoes",
        title="Pix contestados",
        color_discrete_sequence=["#025C75"]
    )
    fig.update_traces(
        line_width=2.5,
        hovertemplate="%{x|%m/%Y}<br>%{y:.2f} milhões<extra></extra>"
    )
    fig.add_hline(
        y=media,
        line_dash="dot",
        line_color="#BFC5CA",
        line_width=1.5
    )
    fig.add_annotation(
        x=1,
        y=media,
        xref="paper",
        yref="y",
        text="Média",
        showarrow=False,
        xanchor="right",
        yshift=10,
        font=dict(size=10, color="#8A8F98")
    )
    fig.add_scatter(
        x=atipicos["mes"],
        y=atipicos["contestacoes"],
        mode="markers+text",
        text=["Atípico"] * len(atipicos),
        textposition="top center",
        marker=dict(size=12, color="white", line=dict(color="#025C75", width=3)),
        textfont=dict(size=10, color="#025C75"),
        hovertemplate="%{x|%m/%Y}<br>%{y:.2f} milhões<br>Mês atípico<extra></extra>"
    )
    fig.update_yaxes(ticksuffix=" mi", rangemode="tozero")
    estilo(fig)
    fig.show()


def plotar_devolucao(pix):
    fig = px.bar(
        pix,
        x="mes",
        y="devolucao",
        text="devolucao",
        title="Percentual de devolução",
        color_discrete_sequence=["#025C75"]
    )
    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="%{x|%m/%Y}<br>%{y:.2f}%<extra></extra>"
    )
    fig.update_yaxes(
        ticksuffix="%",
        range=[0, pix["devolucao"].max() * 1.2]
    )
    estilo(fig)
    fig.show()


pix = preparar_base(carregar_dados_pix())
pix, media = identificar_atipicos(pix)
atipicos = pix[pix["atipico"]]

print("Meses analisados:", len(pix))
print("Meses atípicos:", atipicos["mes"].dt.strftime("%m/%Y").tolist())

plotar_contestacoes(pix, atipicos, media)
plotar_devolucao(pix)