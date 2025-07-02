import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px

# === Load Data ===
drivers = pd.read_csv('drivers.csv')
results = pd.read_csv('results.csv')
constructors = pd.read_csv('constructors.csv')
races = pd.read_csv('races.csv')

# === Merge pentru analiză ===
merged = results.merge(drivers, on='driverId') \
                .merge(constructors, on='constructorId') \
                .merge(races, on='raceId')

# === Top 10 Piloți all-time ===
top_drivers = (
    merged.groupby('surname')['points']
    .sum()
    .reset_index()
    .sort_values(by='points', ascending=False)
    .head(10)
)

fig_top_drivers = px.bar(
    top_drivers, x='surname', y='points',
    title='🏎️ Top 10 Piloți All-Time (după puncte)',
    labels={'surname': 'Pilot', 'points': 'Puncte'},
    color='points'
)

# === Dash app setup ===
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("F1 Dashboard – Istoric All-Time", style={'textAlign': 'center'}),
    dcc.Graph(figure=fig_top_drivers)
])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
