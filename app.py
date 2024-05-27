import dash
from dash import dcc, html
import dash_leaflet as dl
from dash.dependencies import Input, Output, State 
import searoute as sr
import dash_bootstrap_components as dbc
from openai import OpenAI
import json
import re
import os
# from dotenv import load_dotenv

# # Load environment variables from a .env file for local development
# load_dotenv()

# Initialize OpenAI API (replace 'YOUR_API_KEY' with your actual OpenAI API key)
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("No API key found. Please set the OPENAI_API_KEY environment variable.")

client = OpenAI(
    # This is the default and can be omitted
    api_key = api_key
)

# Initiate Dash app
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP, 
                    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"
                ], 
                assets_folder = 'assets',
                title="Great Lakes Whale Co.",  # Set the title of the app
                update_title=None,  # Prevents "Updating..." title when navigating
                )

# Strips junk from GPT response
def clean_json_string(json_string):
    pattern = r'^```json\s*(.*?)\s*```$'
    cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
    return cleaned_string.strip()

# Calls GPT to get all data from origin and destination
def get_city_data(city_name):
    if city_name:
        try:
            # Use OpenAI API to get a quirky description
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", 
                     "content": "You are a helpful assistant."
                     },
                    {"role": "user",
                    "content": f"""Fix spelling mistakes and best interpret {city_name} and determine its latitude and longitude. 
                    Then generate a quirky one-sentence description of city.
                    Return only a json object with the following items: city_name, latitude, longitude, quirky_description./n/n""",
                    }
                ],
                model="gpt-4o",
                max_tokens=100
            )
            clean_response = clean_json_string(response.choices[0].message.content)
            response_json = json.loads(clean_response)
            return response_json
        except Exception as e:
            print(f"Error: {e}")
            return None
    else:
        return None

# Calculate map markers and path
def get_route_line(origin_data, destination_data, speed):
    
    # Port data from GPT JSONresponse
    origin = [origin_data["latitude"], origin_data["longitude"]]  
    destination = [destination_data["latitude"], destination_data["longitude"]]

    # Get the route as a GeoJSON LineString Feature
    route = sr.searoute(origin, destination)

    # Parse the GeoJSON
    route_coords = route['geometry']['coordinates']

    # Extract latitude and longitude for plotting
    lons, lats = zip(*route_coords)

    # Modify lat and lon when the first and last coords don't match the origin and destination
    if lons[0] != origin[1]:
        modified_tuple = (origin[1],) + lons[1:]
        lons = modified_tuple

    if lats[0] != origin[0]:
        modified_tuple = (origin[0],) + lats[1:]
        lats = modified_tuple

    # Modify destination lines
    if lons[-1] != destination[1]:
        modified_tuple = lons[:-1] + (destination[1],)
        lons = modified_tuple

    if lats[-1] != destination[0]:
        modified_tuple = lats[:-1] + (destination[0],)
        lats = modified_tuple

    # Create map object from calculated port markers
    markers = []
    
    # Create tooltip for origin marker
    tooltip = origin_data['quirky_description']
    markers.append(  # Calculate markers
        dl.Marker(
            position=(origin_data['latitude'], origin_data['longitude']),
            children=[dl.Tooltip(tooltip)]
        )
    )

    # Create tooltip for destination marker
    tooltip = destination_data['quirky_description']
    markers.append(  # Calculate markers
        dl.Marker(
            position=(destination_data['latitude'], destination_data['longitude']),
            children=[dl.Tooltip(tooltip)]
        )
    )

    cluster = dl.LayerGroup(children=markers)
   
    # Calculate sea path
    markers_line = []
    length = 0
    duration_hours = 0
    origin = [origin_data['longitude'], origin_data['latitude'] ]
    destination = [destination_data['longitude'],destination_data['latitude']]
    searoutes_coords = sr.searoute(origin, destination, append_orig_dest=True, speed_knot=speed)
    searoutes_coords_transposed = [[coord[1], coord[0]] for coord in searoutes_coords['geometry']['coordinates']]
    markers_line += searoutes_coords_transposed
    
    length += searoutes_coords['properties']['length']
    duration_hours += searoutes_coords['properties']['duration_hours']
    duration_days = duration_hours / 24

    # Create map object for calculated path at sea
    line = dl.Polyline(
        positions=markers_line,
        smoothFactor=1.0,
        color='ForestGreen',
        weight=1,
        lineCap='round',
        lineJoin='round'
    )
    # Create arrows on line shoing direction
    patterns = [dict(offset='5%', repeat='30px', endOffset='10%', 
        arrowHead=dict(pixelSize=8, polygon=False, pathOptions=dict(stroke=True, color='ForestGreen', weight=1, opacity=10, smoothFactor=1)
        ))]
    
    # Create a fancy map object of for the line
    dline = dl.PolylineDecorator(children=line, patterns=patterns)
    print(dline)

    # Calculate bounds for the map based on the origin and destination coords
    min_lat = min(lat for lat, lon in markers_line) - 2
    max_lat = max(lat for lat, lon in markers_line) + 2
    min_lon = min(lon for lat, lon in markers_line) - 2
    max_lon = max(lon for lat, lon in markers_line) + 2
    bounds = [[min_lat, min_lon], [max_lat, max_lon]]
    
    # Calculate centroid
    x, y = zip(*markers_line)
    centroid = [sum(x) / len(x), sum(y) / len(y)]

    return cluster, dline, centroid, bounds, duration_hours, duration_days, length


#  Define the modal
modal = html.Div(
    [
        dbc.Button(
            html.I(className="fas fa-info-circle"),  # Font Awesome info icon
            id="open-modal",
            n_clicks=0,
            className="icon-button mb-3",  # Custom class for styling
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("How to Use This App")),
                dbc.ModalBody(
                    html.P([
                    
                        html.B("This app uses AI to help you plot your course:"), html.Br(),
                        "1. Enter the origin and destination in the respective fields", html.Br(),
                        "2. Adjust the speed using the slider", html.Br(),
                        "3. Click on the 'Let's Go!' button to get the route and details", html.Br(),
                    ])
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal", className="ml-auto")
                ),
            ],
            id="modal",
            is_open=False,
        ),
    ]
)

# Define the layout
app.layout = html.Div([
      # Left pane for dropdown and route information
    html.Div([
        # Header logo
        html.Div([
            html.Img(src=app.get_asset_url('lakenav_logo.png'), className='logo'),
            modal
            ],
            className="logo-container"
            ),
        # Inputs
        html.Div([
            # Origin
            html.Div([
                dbc.Label("Origin", style={'color': '#fff', 'fontWeight': 'bold'}),
                dbc.Input(id='origin-input', type='text', value='Michigan City, IN', placeholder='Enter origin city'),
            ],
            className="single-input"
            ),
            # Destination
            html.Div([
                dbc.Label("Destination", style={'color': '#fff', 'fontWeight': 'bold'}),
                dbc.Input(id='destination-input', type='text', value='Thunder Bay, ON', placeholder='Enter destination city'),
            ],
            className="single-input"
            ),
        ], 
        id='inputs', className='inputs'
        ),
        # Speed input
        html.Div([
            dbc.Label("Speed (knots)", style={'color': '#fff', 'fontWeight': 'bold'}),
            dcc.Slider(id='speed-slider', min=1, max=15, step=1, value=5, marks={i: {'label': str(i), 'style': {'color': '#fff'}} for i in range(1, 26)}, tooltip={'always_visible': False}),
        ]),
        # Navigate button anf route info
        html.Div([
            html.Div([
                dbc.Button("Let's Go!", id='navigate-button', className='navigate-button'),
            ],
            className="nav-box-item1", 
            ),
            dcc.Loading([
                html.Div(id='route-info', className='route-info'),
            ], 
            className="nav-box-item2"
            ),
        ],
        className="nav-box"
        )
    ], 
    id='left-pane',
    className='left-pane',
    ),
    
    # Right pane for the map
    html.Div([
        dl.Map(children=dl.LayersControl(
            [
                dl.BaseLayer(dl.TileLayer(url='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'), id='map_base', checked=True, name='Base Map')
            ] +
            [
                dl.Overlay(children=[], id='route_lines', checked=True, name='Route Direction'),
                dl.Overlay(children=[], id='route_markers', checked=True, name='Ports')
            ]
        ), 
         id='events_map', center=[45.310, -84.210], zoom=3, style={'width': '100%', 'height': '100%'})], 
        id='map-pane', className='map-pane'
    )
], 
className='main-container')

# App callback
@app.callback(
    Output('route_markers', 'children'),
    Output('route_lines', 'children'), 
    Output('events_map', 'center'), 
    Output('events_map', 'zoom'),
    Output('events_map', 'bounds'),
    Output('route-info', 'children'),
    Output("modal", "is_open"),
    Input('navigate-button', 'n_clicks'),
    Input("open-modal", "n_clicks"),
    Input("close-modal", "n_clicks"),
    State('origin-input', 'value'),
    State('destination-input', 'value'),
    State('speed-slider', 'value'),
    State("modal", "is_open"),
)


def update_map_and_toggle_modal(n_clicks, open_modal_n_clicks, close_modal_n_clicks, origin, destination, speed, is_modal_open):
    ctx = dash.callback_context

    # Determine which input triggered the callback
    if not ctx.triggered:
        return [], [], [0, 0], 1, [[0, 0], [0, 0]], "", is_modal_open

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Toggle modal
    if triggered_id == "open-modal" or triggered_id == "close-modal":
        is_modal_open = not is_modal_open

    # Handle navigation
    if triggered_id == 'navigate-button' and n_clicks:
        if n_clicks is None:
            origin_data = get_city_data('Michigan City, IN')
            destination_data = get_city_data('Thunder Bay, ON')
        else:
            origin_data = get_city_data(origin)
            destination_data = get_city_data(destination)

        if not origin_data or not destination_data:
            return [], [], [0, 0], 3, [[-50, -80], [50, 80]], "One of the cities could not be found.", is_modal_open
        else:
            cluster, dline, centroid, bounds, duration_hours, duration_days, length = get_route_line(origin_data, destination_data, speed)
            
            route_name = origin_data['city_name'] + ' to ' + destination_data['city_name']
            route_info = [
                html.P([html.B("Route: "), route_name]),
                html.P([html.B("Distance: "), f"{length:.0f} km"]),
                html.P([html.B("Speed: "), f"{speed} knots"]),
                html.P([html.B("Duration: "), f"{duration_hours:.0f} hours({duration_days:.0f} days)"]),         
            ]
            
            # Calculate the center based on the centroid of the bounds
            center = [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]
            
            return cluster, dline, center, 6, bounds, route_info, is_modal_open

    return [], [], [0, 0], 1, [[0, 0], [0, 0]], "", is_modal_open

if __name__ == '__main__':
    # Use this for development
    # app.run_server(debug=True)
    
    # Use this for development
    # Use the PORT environment variable for the port, and 0.0.0.0 for the host to be accessible externally
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)
