from dash import Dash, html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

# Function to render the app header
def render_appheader():
    return html.Div([
        html.H1('Welcome to Neuron', id='app-title', style={'flex': 1}),
        html.H2(id='current-time', style={'flex': 1, 'textAlign': 'right'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 
              'padding': '10px'})



if __name__ == '__main__':
    app = Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])
    app.layout = html.Div([
        render_appheader(),
        dcc.Interval(
            id='interval-update',
            interval=1000,  # Update every 1000 milliseconds (1 second)
            n_intervals=0
        )
    ])
    app.run(debug=True)
