import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# === Load Data ===
drivers = pd.read_csv("data/drivers.csv")
constructors = pd.read_csv("data/constructors.csv")
results = pd.read_csv("data/results.csv")
races = pd.read_csv("data/races.csv")

# === Merge pentru analiză ===
merged = results.merge(drivers, on='driverId', how='left') \
                .merge(constructors, on='constructorId', how='left') \
                .merge(races, on='raceId', how='left')

# === Top 10 Piloți All-Time ===
top_drivers = (
    merged.groupby(['driverId', 'forename', 'surname'])['points']
    .sum()
    .reset_index()
)
top_drivers['full_name'] = top_drivers['forename'] + ' ' + top_drivers['surname']
top_drivers = top_drivers.sort_values(by='points', ascending=False).head(10)

fig_top_drivers = px.bar(
    top_drivers,
    x='full_name',
    y='points',
    title='🏎️ Top 10 Piloți All-Time',
    labels={'full_name': 'Pilot', 'points': 'Puncte'},
    color='points',
    color_continuous_scale='Reds'
)

# === Dash App ===
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("F1 Dashboard Interactiv", style={'textAlign': 'center'}),
    
    dcc.Graph(
        id='pilot-chart',
        figure=fig_top_drivers
    ),

    html.Div(id='echipe-pilot', children=[
        html.H3("Echipele pilotului selectat"),
        dcc.Graph(id='echipe-chart')
    ])
])

# === Callback interactiv ===
@app.callback(
    Output('echipe-chart', 'figure'),
    Input('pilot-chart', 'clickData')
)
def update_echipe_chart(clickData):
    if clickData is None:
        return px.bar(title="Selectează un pilot pentru a vedea echipele sale")

    selected_name = clickData['points'][0]['x']
    driver_row = top_drivers[top_drivers['full_name'] == selected_name]
    
    if driver_row.empty:
        return px.bar(title="Nu există date pentru acest pilot")

    driver_id = driver_row.iloc[0]['driverId']

    echipe = (
        merged[merged['driverId'] == driver_id]
        .groupby('name')['points']
        .sum()
        .reset_index()
        .sort_values(by='points', ascending=False)
    )

    fig = px.bar(
        echipe,
        x='name',
        y='points',
        title=f"🔧 Echipele pilotului {selected_name}",
        labels={'name': 'Echipă', 'points': 'Puncte'},
        color='points',
        color_continuous_scale='Blues'
    )
    return fig

# === Run Server ===
if __name__ == '__main__':
    app.run_server(debug=True)
