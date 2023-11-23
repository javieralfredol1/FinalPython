import dash
from dash import Dash,dcc,html,Input,Output
from dash import dash_table
import plotly.express as px
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import yfinance as yf
import datetime
import pyfolio as pf
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt.efficient_frontier import EfficientFrontier
import numpy as np

stocks2 =["KO","PG","CAT","PM","MDLZ"]
stocks2

end = datetime.datetime.now() 
start = end - datetime.timedelta(days=365*3)

Precio2 = yf.download(stocks2, start=start, end=end)["Adj Close"]


#PortafolioPesos
Ret2 = Precio2.pct_change()
Retorno2 = (1+Ret2).cumprod()
pesos = np.array([0.2,0.2,0.2,0.2,0.2])
Ret2["PortafolioPesos"] = Ret2.dot(pesos)
RetornoPesos = (1+Ret2).cumprod()

#PortafolioSharpe
pesos1 = np.array([0.2613913233539849,0.0,0.3151758802142486,0.0,0.4234327964317664])
Ret2S = Precio2.pct_change()
Retorno2S = (1+Ret2S).cumprod()
Ret2S["PortafolioSharpe"]=Ret2S.dot(pesos1)
RetornoSharpe = (1+Ret2S).cumprod()

#PortafolioVolatilidad
pesos2 = np.array([0.1188255551759774,0.2967099817172744,0.1133024040250448,
                   0.2980230651358765,0.173138993945827])
Ret2V = Precio2.pct_change()
Retorno2V = (1+Ret2V).cumprod()
Ret2V["PortafolioVolatilidad"]=Ret2V.dot(pesos2)
RetornoVolatilidad = (1+Ret2V).cumprod()

#Nuevo dataframe con los retornos acumulados

ColumnaPesos = RetornoPesos["PortafolioPesos"]
ColumnaSharpe = RetornoSharpe["PortafolioSharpe"]
ColumnaVolatilidad = RetornoVolatilidad["PortafolioVolatilidad"]

RetornosP = pd.concat([ColumnaPesos, ColumnaSharpe, ColumnaVolatilidad], axis=1)

RetornosP.reset_index(inplace=True)

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.title = "Dashboard"

app.layout = html.Div([
    # dropdown checklist
    html.Div(dcc.Dropdown(
        id="empresas", value=["KO", "PG", "CAT", "PM", "MDLZ"], clearable=False, multi=True,
        options=[{'label': col, 'value': col} for col in Precio2.columns]),
        style={"width": "45%"},
    ),

    # dropdown precio / retorno acumulado
    html.Div(dcc.Dropdown(
        id="cuentas", value="Precio2", clearable=True,
        options=[{'label': "Precio2", 'value': "Precio2"},
                 {'label': "Retorno2", 'value': "Retorno2"}],
        style={"width": "35%"},
    )),

    dcc.Graph(id="linechart"),

    dcc.RangeSlider(
        id="fechas",
        marks={i: (start + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(0, 365 * 3, 100)},
        min=0,
        max=365 * 3,
        step=15,
        value=[0, 365 * 3]
    ),
    
    dcc.Graph(id="Comparación"),
    dcc.Graph(id="GPSharpe"),
    dcc.Graph(id="GPVolatilidad"),
])

@app.callback([Output("linechart", "figure"),
               Output("Comparación", 'figure'),
               Output("GPSharpe", 'figure'),
               Output("GPVolatilidad", 'figure')],
              [Input("empresas", "value"),
               Input("cuentas", "value"),
               Input("fechas", "value")]
)
    
def update_linechart(selected_empresas, selected_cuenta, selected_fechas):
    if selected_cuenta == "Precio2":
        df_filtered = Precio2[selected_empresas].iloc[selected_fechas[0]:selected_fechas[1]]
    elif selected_cuenta == "Retorno2":
        df_filtered = (1 + Precio2[selected_empresas].pct_change()).cumprod().iloc[selected_fechas[0]:selected_fechas[1]]
    else:
        df_filtered = pd.DataFrame()

    fig = px.line(df_filtered, x=df_filtered.index, y=df_filtered.columns, labels={'value': selected_cuenta},
                  title=f'{selected_cuenta} de {", ".join(selected_empresas)}')
    
    Comparación = px.line(RetornosP, x="Date", y=["PortafolioPesos", "PortafolioSharpe", "PortafolioVolatilidad"],
              title="Retornos de diferentes portafolios",
              labels={"value": "Retorno", "Date": "Fecha"})

    GPSharpe = px.histogram(Ret2S, x="PortafolioSharpe",title="Distribución del retorno histórico del PortafolioSharpe", 
                            labels={"PortafolioSharpe": "Cambio diario en el rendimiento"})
    
    GPVolatilidad = px.histogram(Ret2V, x="PortafolioVolatilidad",title="Distribución del retorno histórico del PortafolioVolatilidad", 
                            labels={"PortafolioVolatilidad": "Cambio diario en el rendimiento"})
    
    return fig, Comparación, GPSharpe, GPVolatilidad

if __name__ == '__main__':
    app.run_server(debug=False,host="0.0.0.0",port=15000)
