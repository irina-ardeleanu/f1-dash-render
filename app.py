import dash
from dash import dcc, html, Input, Output
import pandas as pd
import requests
from dash import dash_table
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
all_drivers = all_drivers.sort_values(by='points', ascending=False).reset_index(drop=True)
all_drivers['rank'] = all_drivers.index + 1  # Clasamentul (locul)
def get_recent_races_with_results(season="2024", limit=5):
    url = f"https://ergast.com/api/f1/{season}/results.json?limit={limit}&offset=0"
    response = requests.get(url)
    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json()
    races = data['MRData']['RaceTable']['Races']
    rows = []

    for race in races:
        if not race['Results']:
            continue

        winner = race['Results'][0]['Driver']
        team = race['Results'][0]['Constructor']['name']

        rows.append({
            "race_name": race['raceName'],
            "circuit": race['Circuit']['circuitName'],
            "location": f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}",
            "date": race['date'],
            "winner": f"{winner['givenName']} {winner['familyName']}",
            "team": team
        })

    return pd.DataFrame(rows)

# === App layout ===
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("F1 Dashboard Interactiv", style={'textAlign': 'center'}),

    dcc.Graph(id='pilot-chart'),

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
        dcc.Graph(id='echipe-chart'),
        html.Div([
        html.H2("🏁 Ultimele curse – Sezon curent"),
        html.Button("Încarcă curse recente", id="load-races-btn", n_clicks=0),
        dcc.Loading(
            id="loading-races",
            children=html.Div(id="recent-races-table"),
            type="circle"
        )
    ], style={"marginTop": "40px"})
    ])
])

# === Callback ===
@app.callback(
    Output('pilot-chart', 'figure'),
    Output('echipe-chart', 'figure'),
    Output('echipe-titlu', 'children'),
    Input('pilot-dropdown', 'value'),
    Input('pilot-chart', 'clickData')
)
def update_charts(dropdown_value, clickData):
    selected_name = dropdown_value
    if not selected_name and clickData:
        selected_name = clickData['points'][0]['x']

    return dash_table.DataTable(
        data=races_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in races_df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'fontWeight': 'bold'},
        page_size=10
    )

    # === Grafic Piloți ===
    top_drivers = all_drivers.head(10).copy()
    if selected_name and selected_name not in top_drivers['full_name'].values:
        selected_driver = all_drivers[all_drivers['full_name'] == selected_name]
        top_drivers = pd.concat([top_drivers, selected_driver])

    # Marcăm dacă pilotul e selectat
    top_drivers['selected'] = top_drivers['full_name'].apply(lambda x: 'Selectat' if x == selected_name else 'Alții')

    fig_piloti = px.bar(
        top_drivers,
        x='full_name',
        y='points',
        color='selected',
        color_discrete_map={'Selectat': 'green', 'Alții': 'red'},
        labels={'full_name': 'Pilot', 'points': 'Puncte'},
        title='🏎️ Piloți All-Time',
        hover_data=['rank', 'points']
    )

    # === Grafic Echipe ===
    if not selected_name:
        top_teams = (
            merged.groupby('constructor_name')['points']
            .sum()
            .reset_index()
            .sort_values(by='points', ascending=False)
            .head(10)
        )
        fig_teams = px.bar(
            top_teams,
            x='constructor_name',
            y='points',
            title='🔧 Top 10 Echipe All-Time',
            labels={'constructor_name': 'Echipă', 'points': 'Puncte'},
            color='points',
            color_continuous_scale='Blues'
        )
        return fig_piloti, fig_teams, "🔧 Top 10 Echipe All-Time"

    driver_row = all_drivers[all_drivers['full_name'] == selected_name]
    if driver_row.empty:
        return fig_piloti, px.bar(title="Nu există date pentru acest pilot"), "❌ Date lipsă pentru acest pilot"

    driver_id = driver_row.iloc[0]['driverId']

    echipe = (
        merged[merged['driverId'] == driver_id]
        .groupby('constructor_name')['points']
        .sum()
        .reset_index()
        .sort_values(by='points', ascending=False)
    )

    fig_teams = px.bar(
        echipe,
        x='constructor_name',
        y='points',
        title=f"🔧 Echipele pilotului {selected_name}",
        labels={'constructor_name': 'Echipă', 'points': 'Puncte'},
        color='points',
        color_continuous_scale='Blues'
    )

    # Titlu detaliat cu loc și puncte
    rank = driver_row.iloc[0]['rank']
    points = driver_row.iloc[0]['points']
    titlu = f"🔧 Echipele pilotului {selected_name} (Loc {rank}, {points} puncte)"

    return fig_piloti, fig_teams, titlu
@app.callback(
    Output("recent-races-table", "children"),
    Input("load-races-btn", "n_clicks"),
    prevent_initial_call=True
)
def load_recent_races(n_clicks):
    races_df = get_recent_races_with_results()
    if races_df.empty:
        return html.Div("❌ Nu s-au putut încărca cursele.")

    return dash_table.DataTable(
        data=races_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in races_df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'fontWeight': 'bold'},
        page_size=10
    )

# === Run Server ===
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
