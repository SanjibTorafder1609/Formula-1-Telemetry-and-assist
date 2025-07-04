import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import json
import numpy as np

# Load decoded telemetry
with open('decoded_telemetry.json') as f:
    frames = json.load(f)

# Extract data from car_telemetry
frame_ids = []
throttle = []
brake = []
gear = []

for frame_id, packets in frames.items():
    telemetry = packets.get("car_telemetry")
    if telemetry:
        time_sec = int(frame_id) / 60.0  # convert frame_id to seconds
        frame_ids.append(time_sec)
        throttle.append(telemetry.get("throttle", 0))
        brake.append(telemetry.get("brake", 0))
        gear.append(telemetry.get("gear", 0))

# Sort by time
combined = sorted(zip(frame_ids, throttle, brake, gear), key=lambda x: x[0])
frame_ids, throttle, brake, gear = zip(*combined)
frame_ids = np.array(frame_ids)
throttle = np.array(throttle)
brake = np.array(brake)
gear = np.array(gear)

# Dash app setup
app = dash.Dash(__name__)
app.title = "F1 Telemetry Dashboard"

# Parameters
max_time = frame_ids[-1]
window_size = 5  # seconds
update_interval = 50  # milliseconds between updates
scroll_speed = 0.05  # seconds advanced each update

# Layout
app.layout = html.Div([
    html.H1("F1 Telemetry Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Button('▶ Play', id='play-button', n_clicks=0, 
                  style={'margin': '10px'}),
        html.Button('❚❚ Pause', id='pause-button', n_clicks=0,
                  style={'margin': '10px'}),
        html.Button('⟲ Reset', id='reset-button', n_clicks=0,
                  style={'margin': '10px'}),
    ], style={'textAlign': 'center'}),
    
    dcc.Graph(id='throttle-brake-graph'),
    dcc.Graph(id='gear-graph'),

    html.Div(id='current-window', style={'display': 'none'}, children=str(0)),
    
    dcc.Interval(
        id='interval-component',
        interval=update_interval,
        n_intervals=0,
        disabled=True
    )
])

# Combined callback for all playback controls
@app.callback(
    [Output('current-window', 'children'),
     Output('interval-component', 'disabled'),
     Output('play-button', 'style'),
     Output('pause-button', 'style')],
    [Input('play-button', 'n_clicks'),
     Input('pause-button', 'n_clicks'),
     Input('reset-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')],
    [State('current-window', 'children')]
)
def control_playback(play_clicks, pause_clicks, reset_clicks, n_intervals, current_window_str):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        # Initial load
        return str(0), True, {'margin': '10px'}, {'margin': '10px'}
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_window = float(current_window_str)
    
    # Handle button clicks
    if trigger_id == 'play-button':
        return (current_window_str, False, 
                {'margin': '10px', 'backgroundColor': 'lightgreen'}, 
                {'margin': '10px'})
    
    elif trigger_id == 'pause-button':
        return (current_window_str, True, 
                {'margin': '10px'}, 
                {'margin': '10px', 'backgroundColor': 'lightcoral'})
    
    elif trigger_id == 'reset-button':
        return str(0), True, {'margin': '10px'}, {'margin': '10px'}
    
    elif trigger_id == 'interval-component':
        # Auto-scroll logic
        new_window = current_window + scroll_speed
        
        if new_window + window_size > max_time:
            new_window = max(max_time - window_size, 0)
            return str(new_window), True, {'margin': '10px'}, {'margin': '10px'}  # Stop when reaching end
        
        return str(new_window), False, {'margin': '10px'}, {'margin': '10px'}
    
    return current_window_str, True, {'margin': '10px'}, {'margin': '10px'}

# Update graphs
@app.callback(
    [Output('throttle-brake-graph', 'figure'),
     Output('gear-graph', 'figure')],
    Input('current-window', 'children')
)
def update_graphs(current_window_str):
    current_window = float(current_window_str)
    window_start = current_window
    window_end = window_start + window_size

    mask = (frame_ids >= window_start) & (frame_ids <= window_end)
    window_times = frame_ids[mask]
    window_throttle = throttle[mask]
    window_brake = brake[mask]
    window_gear = gear[mask]

    # Throttle & Brake Graph
    throttle_brake_fig = {
        'data': [
            go.Scatter(
                x=window_times,
                y=window_throttle,
                mode='lines',
                name='Throttle',
                line=dict(color='green', width=2)
            ),
            go.Scatter(
                x=window_times,
                y=window_brake,
                mode='lines',
                name='Brake',
                line=dict(color='red', width=2)
            )
        ],
        'layout': go.Layout(
            title='Throttle and Brake',
            xaxis={'title': '', 'range': [window_start, window_end]},
            yaxis={'range': [0, 1]},
            hovermode='closest',
            margin=dict(l=40, r=40, t=40, b=40)
        )
    }

    # Gear Graph
    gear_fig = {
        'data': [
            go.Scatter(
                x=window_times,
                y=window_gear,
                mode='lines+markers',
                name='Gear',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            )
        ],
        'layout': go.Layout(
            title='Gear',
            xaxis={'title': '', 'range': [window_start, window_end]},
            yaxis={'title': 'Gear', 'dtick': 1,'range': [0, max(gear) ]},
            hovermode='closest',
            margin=dict(l=40, r=40, t=40, b=40)
        )
    }

    return throttle_brake_fig, gear_fig

if __name__ == '__main__':
    app.run(debug=True)