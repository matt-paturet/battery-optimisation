import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots

from optimizer import run

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(title='Battery optimisation', external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
server = app.server

df = pd.read_csv('prices.csv')

app.layout = html.Div([
    html.H3('Battery optimisation in power market'),
    html.Div([
        html.P('by', style={'margin-right': 4}),
        html.A('@matt-paturet', href='https://github.com/matt-paturet'),
    ], style={'display': 'flex'}),
    html.Hr(),
    html.P('Simple algorithm for optimal dispatch of a battery given electricity prices vector. '
           'Select your battery parameters below & press RUN.'),
    html.Div([
        html.Div([
            html.Label('Battery capacity (MW):'),
            dcc.Input(id='capacity', type='number', value=1, min=1),
            html.Label('Battery volume (MWh):'),
            dcc.Input(id='volume', type='number', value=1, min=1),
            html.Label('Round-trip efficiency (%):'),
            html.Div([
                dcc.Slider(
                    id='efficiency', min=0, max=100, step=1, value=85,
                    marks={i: {'label': f'{i}%'} for i in range(0, 120, 20)}
                ),
            ], style={'width': '80%'}),
            html.Label('Starting state of charge (SoC) [%]:'),
            html.Div([
                dcc.Slider(
                    id='input-soc', min=0, max=100, step=1, value=50,
                    marks={i: {'label': f'{i}%'} for i in range(0, 120, 20)}
                ),
            ], style={'width': '80%'})
        ], style={'display': 'inline-block', 'width': '50%', 'vertical-align': 'top'}),
        html.Div([
            html.Label('Charging costs (£/MWh):'),
            dcc.Input(id='charging-costs', type='number', value=5),
            html.Label('Discharging costs (£/MWh):'),
            dcc.Input(id='discharging-costs', type='number', value=5),
            html.Label('Strike price (£/MWh):'),
            dcc.Input(id='strike-price', type='number', value=10),
        ], style={'display': 'inline-block', 'width': '50%', 'vertical-align': 'top'})
    ]),
    html.Button('RUN', id='run', n_clicks=0, style={'margin-top': 10}),
    html.Hr(),
    dcc.Loading(id='results', children=[])
], style={'margin-right': '10%', 'margin-left': '10%'})


@app.callback(Output('results', 'children'),
              [Input('run', 'n_clicks')],
              [State('capacity', 'value'),
               State('volume', 'value'),
               State('efficiency', 'value'),
               State('input-soc', 'value'),
               State('charging-costs', 'value'),
               State('discharging-costs', 'value'),
               State('strike-price', 'value')])
def run_model(n_clicks, capacity, volume, efficiency, input_soc, charge_cost, discharge_cost, strike):

    if n_clicks == 0:
        return None

    prices = df['day_ahead'].values

    charge, discharge, soc, sol = run(
        capacity=capacity,
        volume=volume,
        efficiency=efficiency/100.0,
        input_soc=input_soc/100.0,
        prices=prices,
        charge_cost=charge_cost,
        discharge_cost=discharge_cost,
        activation=strike
    )

    t = df['timestamp']

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True)

    fig.add_scatter(x=t, y=prices, name='Price', row=1, col=1)
    fig.add_bar(x=t, y=-charge, name='Charging', row=2, col=1)
    fig.add_bar(x=t, y=discharge, name='Discharging', row=2, col=1)
    fig.add_scatter(x=t, y=soc * 100, name='SoC', row=3, col=1)

    fig.update_yaxes(title='£/MWh', row=1, col=1)
    fig.update_yaxes(title='MW', row=2, col=1)
    fig.update_yaxes(title='%', row=3, col=1)

    fig.update_layout(
        title=f'Model results (optimization status: {sol.success})',
        barmode='stack',
        legend={'traceorder': 'reversed'},
        height=800
    )

    return [
        dcc.Graph(figure=fig)
    ]


if __name__ == '__main__':
    app.run_server()
