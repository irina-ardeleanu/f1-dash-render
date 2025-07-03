import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# === Load Data ===
drivers = pd.read_csv("data/drivers.csv")
constructors = pd.read_csv("data/constructors.csv")
results = pd.read_csv("data/results.csv")
races = pd.read_csv("data/races.csv")

# === Pregătire date ===
constructors.rename(columns={'name': 'constructor_name'}, inplace=True)

# === Merge complet pentru analiză ===
merged = results.merge(drivers, on='driverId', how='left') \
                .merge(constructors, on='constructorId', how='left') \
                .merge(races, on='raceId', how='left')

# === Toți piloții ===
all_drivers = (
    merged.groupby(['driverId', 'forename', 'surname'])['points']
    .sum()
    .reset_index()
)
all_drivers['full_name'] = all_drivers['forename'] + ' ' + all_drivers['surname']
all_drivers = all_drivers.sort_values(by='points', ascending=False)

# === Top 10 Piloți ===
fig_top_drivers = px.bar(
    all_drivers.head(10),
    x='full_name',
    y='points',
    title='🏎️ Piloți All-Time',
    labels={'full_name': 'Pilot', 'points': 'Puncte'},
    color='points',
    color_continuous_scale='Reds'
)

# === App layout ===
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("F1 Dashboard Interactiv", style={'textAlign': 'center'}),

    dcc.Graph(
        id='pilot-chart',
        figure=fig_top_drivers
    ),

    html.Div([
        html.Label("Selectează un pilot:"),
        dcc.Dropdown(
            id='pilot-dropdown',
            options=[{'label': name, 'value': name} for name in all_drivers['full_name']],
            placeholder="Caută un pilot...",
            style={'width': '50%'}
        )
    ], style={'margin': '20px'}),

    html.Div([
        html.H3(id='echipe-titlu'),
        dcc.Graph(id='echipe-chart')
    ])
])

# === Callback ===
@app.callback(
    Output('echipe-chart', 'figure'),
    Output('echipe-titlu', 'children'),
    Input('pilot-dropdown', 'value'),
    Input('pilot-chart', 'clickData')
)
def update_echipe_chart(dropdown_value, clickData):
    selected_name = dropdown_value
    if not selected_name and clickData:
        selected_name = clickData['points'][0]['x']

    if not selected_name:
        top_teams = (
            merged.groupby('constructor_name')['points']
            .sum()
            .reset_index()
            .sort_values(by='points', ascending=False)
            .head(10)
        )
        fig = px.bar(
            top_teams,
            x='constructor_name',
            y='points',
            title='🔧 Top 10 Echipe All-Time',
            labels={'constructor_name': 'Echipă', 'points': 'Puncte'},
            color='points',
            color_continuous_scale='Blues'
        )
        return fig, "🔧 Top 10 Echipe All-Time"

    driver_row = all_drivers[all_drivers['full_name'] == selected_name]
    if driver_row.empty:
        return px.bar(title="Nu există date pentru acest pilot"), "❌ Date lipsă pentru acest pilot"

    driver_id = driver_row.iloc[0]['driverId']

    echipe = (
        merged[merged['driverId'] == driver_id]
        .groupby('constructor_name')['points']
        .sum()
        .reset_index()
        .sort_values(by='points', ascending=False)
    )

    fig = px.bar(
        echipe,
        x='constructor_name',
        y='points',
        title=f"🔧 Echipele pilotului {selected_name}",
        labels={'constructor_name': 'Echipă', 'points': 'Puncte'},
        color='points',
        color_continuous_scale='Blues'
    )
    return fig, f"🔧 Echipele pilotului {selected_name}"

# === Run Server ===
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
