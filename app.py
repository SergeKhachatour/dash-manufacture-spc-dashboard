from dash import Dash, dcc, html, dash_table, Input, Output, State, callback_context, no_update
import dash_daq as daq
import pandas as pd
import copy
from textwrap import dedent
import plotly.graph_objects as go

app = Dash(
    __name__,
    suppress_callback_exceptions=True
)
server = app.server

df = pd.read_csv("data/spc_data.csv")

params = list(df)
max_length = len(df)

suffix_row = '_row'
suffix_button_id = '_button'
suffix_sparkline_graph = '_sparkline_graph'
suffix_count = '_count'
suffix_ooc_n = '_OOC_number'
suffix_ooc_g = '_OOC_graph'
suffix_indicator = '_indicator'

theme = {
    'dark': True,
    'detail': '#2d3038',  # Background-card
    'primary': '#007439',  # Green
    'secondary': '#FFD15F',  # Accent
}


def build_banner():
    return html.Div(
        id='banner',
        className="banner",
        children=[
            html.H5('Manufacturing SPC Dashboard - Process Control and Exception Reporting'),
            html.Button(
                id='learn-more-button',
                children="LEARN MORE",
                n_clicks=0,
            ),
            html.Img(
                src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png")
        ]
    )


def build_tabs():
    return html.Div(
        id='tabs',
        className='row container scalable',
        children=[
            dcc.Tabs(
                id='app-tabs',
                value='tab2',
                className='custom-tabs',
                children=[
                    dcc.Tab(
                        id='Specs-tab',
                        label='Specification Settings',
                        value='tab1',
                        className='custom-tab',
                        selected_className='custom-tab--selected',
                        disabled_style={
                            'backgroundColor': '#2d3038',
                            'color': '#95969A',
                            'borderColor': '#23262E',
                            'display': 'flex',
                            'flex-direction': 'column',
                            'alignItems': 'center',
                            'justifyContent': 'center'
                        },
                        disabled=False
                    ),
                    dcc.Tab(
                        id='Control-chart-tab',
                        label='Control Charts Dashboard',
                        value='tab2',
                        className='custom-tab',
                        selected_className='custom-tab--selected',
                        disabled_style= {
                            'backgroundColor': '#2d3038',
                            'color': '#95969A',
                            'borderColor': '#23262E',
                            'display': 'flex',
                            'flex-direction': 'column',
                            'alignItems': 'center',
                            'justifyContent': 'center'
                        },
                        disabled=False)
                ]
            )
        ]
    )


def init_df():
    ret = {}
    for col in list(df[1:]):
        data = df[col]
        stats = data.describe()

        std = stats['std'].tolist()
        ucl = (stats['mean'] + 3 * stats['std']).tolist()
        lcl = (stats['mean'] - 3 * stats['std']).tolist()
        usl = (stats['mean'] + stats['std']).tolist()
        lsl = (stats['mean'] - stats['std']).tolist()

        ret.update({
            col: {
                'count': stats['count'].tolist(),
                'data': data,
                'mean': stats['mean'].tolist(),
                'std': std,
                'ucl': round(ucl, 3),
                'lcl': round(lcl, 3),
                'usl': round(usl, 3),
                'lsl': round(lsl, 3),
                'min': stats['min'].tolist(),
                'max': stats['max'].tolist(),
                'ooc': populate_ooc(data, ucl, lcl)
            }
        })

    return ret


def populate_ooc(data, ucl, lcl):
    ooc_count = 0
    ret = []
    for i in range(len(data)):
        if data[i] >= ucl or data[i] <= lcl:
            ooc_count += 1
            ret.append(ooc_count / (i + 1))
        else:
            ret.append(ooc_count / (i + 1))
    return ret


state_dict = init_df()


def init_value_setter_store():
    """Initialize store data with values from dataset"""
    initial_data = {}
    for param in params[1:]:  # Skip 'Batch'
        data = df[param]
        stats = data.describe()
        
        # Calculate control limits based on statistics
        mean = stats['mean']
        std = stats['std']
        
        # Get the actual control limits from your dataset
        # Assuming your dataset has these columns: param_UCL, param_LCL, param_USL, param_LSL
        param_ucl = df[f'{param}_UCL'].iloc[0] if f'{param}_UCL' in df else round(mean + 2 * std, 3)
        param_lcl = df[f'{param}_LCL'].iloc[0] if f'{param}_LCL' in df else round(mean - 2 * std, 3)
        param_usl = df[f'{param}_USL'].iloc[0] if f'{param}_USL' in df else round(mean + 3 * std, 3)
        param_lsl = df[f'{param}_LSL'].iloc[0] if f'{param}_LSL' in df else round(mean - 3 * std, 3)
        
        initial_data[param] = {
            'data': data.tolist(),
            'usl': param_usl,
            'lsl': param_lsl,
            'ucl': param_ucl,
            'lcl': param_lcl,
            'mean': round(mean, 3),
            'std': round(std, 3),
            'ooc': populate_ooc(data, param_ucl, param_lcl)
        }
        
        print(f"Debug - Initialized {param} with values:")
        print(f"  UCL: {param_ucl}")
        print(f"  LCL: {param_lcl}")
        print(f"  USL: {param_usl}")
        print(f"  LSL: {param_lsl}")
        
    return initial_data


def build_tab_1():
    return [
        # Manually select metrics
        html.Div(
            id='set-specs-intro-container',
            className='twelve columns',
            children=html.P("Use historical control limits to establish a benchmark, or set new values.")
        ),
        html.Div(
            className='five columns',
            children=[
                html.Label(id='metric-select-title', children='Select Metrics'),
                html.Br(),
                dcc.Dropdown(
                    id='metric-select-dropdown',
                    options=list({'label': param, 'value': param} for param in params[1:]),
                    value=params[1]  # Set initial value to first parameter
                )
            ]
        ),
        html.Div(
            className='five columns',
            children=[
                # Add the numeric inputs here
                html.Div(
                    id='value-setter-panel'
                ),
                # Add the numeric input components
                html.Div([
                    daq.NumericInput(
                        id='ud_usl_input',
                        size=200,
                        max=9999999,
                        style={'width': '100%', 'height': '100%'}
                    ),
                    daq.NumericInput(
                        id='ud_lsl_input',
                        size=200,
                        max=9999999,
                        style={'width': '100%', 'height': '100%'}
                    ),
                    daq.NumericInput(
                        id='ud_ucl_input',
                        size=200,
                        max=9999999,
                        style={'width': '100%', 'height': '100%'}
                    ),
                    daq.NumericInput(
                        id='ud_lcl_input',
                        size=200,
                        max=9999999,
                        style={'width': '100%', 'height': '100%'}
                    ),
                ], style={'display': 'none'}),  # Hide these inputs as they're just for state management
                html.Br(),
                html.Button('Update', id='value-setter-set-btn'),
                html.Button('View current setup', id='value-setter-view-btn', n_clicks=0),
                html.Div(id='value-setter-view-output', className='output-datatable')
            ]
        )
    ]


def build_value_setter_line(line_num, label, value, col3):
    if line_num == 'value-setter-panel-header':
        return html.Div(
            id=line_num,
            children=[
                html.Label(label, className='three columns'),
                html.Label(value, className='three columns'),
                html.Label(col3, className='three columns')
            ],
            className='row'
        )
    else:
        # Extract the type of limit from the line_num
        limit_type = line_num.split('-')[-1]  # Will get 'usl', 'lsl', 'ucl', or 'lcl'
        input_id = f'ud_{limit_type}_input'  # Changed to match the ud_ prefix
        
        return html.Div(
            id=line_num,
            children=[
                html.Label(label, className='three columns'),
                html.Label(value, className='three columns'),
                dcc.Input(
                    id=input_id,
                    className='three columns',
                    type='number',
                    placeholder='Enter new value',
                    style={'backgroundColor': '#2d3038', 'color': '#95969A'}
                )
            ],
            className='row'
        )


def generate_modal():
    return html.Div(
        id='markdown',
        className="modal",
        style={'display': 'none'},
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className='close-container',
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton"
                        )
                    ),
                    html.Div(
                        className='markdown-text',
                        children=dcc.Markdown(
                            children=dedent('''
                        **What is this mock app about?**

                        'dash-manufacture-spc-dashboard` is a dashboard for monitoring read-time process quality along manufacture production line. 

                        **What does this app shows**

                        Click on buttons in `Parameter' column to visualize details of measurement trendlines on the bottom panel.

                        The Sparkline on top panel and Control chart on bottom panel show Shewhart process monitor using mock data. 
                        The trend is updated every other second to simulate real-time measurements. Data falling outside of six-sigma control limit are signals indicating 'Out of Control(OOC)', and will 
                        trigger alerts instantly for a detailed checkup. 
                    '''))
                    )
                ]
            )
        )
    )


def create_specs_table(stored_data, dd_select):
    """Create a table showing current specification limits for the selected parameter"""
    if not stored_data or dd_select not in stored_data:
        return html.Div("No data available")
        
    data = stored_data[dd_select]
    
    # Create the data for the table
    table_data = [
        {"Limit Type": "Upper Specification Limit (USL)", "Value": data['usl']},
        {"Limit Type": "Lower Specification Limit (LSL)", "Value": data['lsl']},
        {"Limit Type": "Upper Control Limit (UCL)", "Value": data['ucl']},
        {"Limit Type": "Lower Control Limit (LCL)", "Value": data['lcl']}
    ]
    
    return dash_table.DataTable(
        data=table_data,
        columns=[
            {"name": "Limit Type", "id": "Limit Type"},
            {"name": "Value", "id": "Value", "type": "numeric", 
             "format": {"specifier": ".3f"}}
        ],
        style_header={
            'backgroundColor': '#2d3038',
            'color': '#95969A',
            'fontWeight': 'bold'
        },
        style_cell={
            'backgroundColor': '#2d3038',
            'color': '#95969A',
            'textAlign': 'left',
            'padding': '10px'
        },
        style_table={
            'overflowX': 'auto'
        }
    )

# Callbacks start here
@app.callback(
    [Output('value-setter-panel', 'children'),
     Output('ud_usl_input', 'value', allow_duplicate=True),
     Output('ud_lsl_input', 'value', allow_duplicate=True),
     Output('ud_ucl_input', 'value', allow_duplicate=True),
     Output('ud_lcl_input', 'value', allow_duplicate=True)],
    [Input('metric-select-dropdown', 'value')],
    [State('value-setter-store', 'data')],
    prevent_initial_call='initial_duplicate'
)
def update_value_setter_panel(dd_select, stored_data):
    # If no selection yet, default to first parameter
    if dd_select is None and len(params) > 1:
        dd_select = params[1]  # First parameter after 'Batch'
    
    if dd_select not in stored_data:
        return no_update, no_update, no_update, no_update, no_update
    
    # Create the panel content
    panel_content = [
        build_value_setter_line('value-setter-panel-header', 'Specs', 'Historical Value', 'Set new value'),
        build_value_setter_line('value-setter-panel-usl', 'Upper Specification limit',
                               str(stored_data[dd_select]['usl']), 'USL'),
        build_value_setter_line('value-setter-panel-lsl', 'Lower Specification limit',
                               str(stored_data[dd_select]['lsl']), 'LSL'),
        build_value_setter_line('value-setter-panel-ucl', 'Upper Control limit', 
                               str(stored_data[dd_select]['ucl']), 'UCL'),
        build_value_setter_line('value-setter-panel-lcl', 'Lower Control limit', 
                               str(stored_data[dd_select]['lcl']), 'LCL')
    ]
    
    # Return both panel content and current values
    return (
        panel_content,
        stored_data[dd_select]['usl'],
        stored_data[dd_select]['lsl'],
        stored_data[dd_select]['ucl'],
        stored_data[dd_select]['lcl']
    )


@app.callback(
    Output('value-setter-store', 'data'),
    [Input('value-setter-set-btn', 'n_clicks')],
    [State('metric-select-dropdown', 'value'),
     State('value-setter-store', 'data'),
     State('ud_usl_input', 'value'),
     State('ud_lsl_input', 'value'),
     State('ud_ucl_input', 'value'),
     State('ud_lcl_input', 'value')],
    prevent_initial_call=True
)
def update_value_setter_store(n_clicks, metric, stored_data, usl, lsl, ucl, lcl):
    if n_clicks is None:
        return no_update
        
    new_data = copy.deepcopy(stored_data)
    
    try:
        if metric in new_data:
            changed = False
            if usl is not None:
                new_data[metric]['usl'] = float(usl)
                changed = True
            if lsl is not None:
                new_data[metric]['lsl'] = float(lsl)
                changed = True
            if ucl is not None:
                new_data[metric]['ucl'] = float(ucl)
                changed = True
            if lcl is not None:
                new_data[metric]['lcl'] = float(lcl)
                changed = True
            
            if changed:
                # Recalculate OOC based on new limits
                new_data[metric]['ooc'] = populate_ooc(
                    new_data[metric]['data'],
                    new_data[metric]['ucl'],
                    new_data[metric]['lcl']
                )
                
                print(f"Debug - Updated values for {metric}: {new_data[metric]}")  # Debug print
                return new_data
            
    except Exception as e:
        print(f"Error updating values: {e}")
    
    return stored_data


@app.callback(
    Output('value-setter-view-output', 'children'),
    [Input('value-setter-view-btn', 'n_clicks'),
     Input('value-setter-set-btn', 'n_clicks'),
     Input('metric-select-dropdown', 'value')],
    [State('value-setter-store', 'data')],
    prevent_initial_call=True
)
def show_current_specs(view_clicks, set_clicks, dd_select, stored_data):
    ctx = callback_context
    if not ctx.triggered:
        return ''
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'value-setter-view-btn' and view_clicks == 0:
        return ''
        
    return create_specs_table(stored_data, dd_select)


def generate_section_banner(title):
    return html.Div(
        className="section-banner",
        children=title,
    )


def build_top_panel():
    return html.Div(
        id='top-section-container',
        className='row',
        style={'height': '45vh'},
        children=[
            # Metrics summary
            html.Div(
                id='metric-summary-session',
                className='eight columns',
                style={'height': '100%'},
                children=[
                    generate_section_banner('Process Control Metrics Summary'),
                    generate_metric_list_header(),
                    html.Div(
                        style={
                            'height': 'calc(100% - 90px)',
                            'overflow-y': 'scroll'
                        },
                        children=[
                            generate_metric_row_helper(i) for i in range(1, len(params))
                        ]
                    )
                ]
            ),
            # Piechart
            html.Div(
                id='ooc-piechart-outer',
                className='four columns',
                children=[
                    generate_section_banner('% OOC per Parameter'),
                    generate_piechart()
                ]
            )
        ]
    )


def generate_piechart():
    return dcc.Graph(
        id='piechart',
        figure={
            'data': [
                {
                    'labels': params[1:],
                    'values': [1, 1, 1, 1, 1, 1, 1],
                    'type': 'pie',
                    'marker': {'line': {'color': '#53555B', 'width': 2}},
                    'hoverinfo': 'label',
                    'textinfo': 'label'
                }],
            'layout': {
                'showlegend': True,
                'paper_bgcolor': 'rgb(45, 48, 56)',
                'plot_bgcolor': 'rgb(45, 48, 56)'
            }
        }
    )


# Build header
def generate_metric_list_header():
    return generate_metric_row(
        'metric_header',
        {
            'height': '30px',
            'margin': '10px 0px',
            'textAlign': 'center'
        },
        {
            'id': "m_header_1",
            'children': html.Div("Parameter")
        },
        {
            'id': "m_header_2",
            'children': html.Div("Count")
        },
        {
            'id': "m_header_3",
            'children': html.Div("Sparkline")
        },
        {
            'id': "m_header_4",
            'children': html.Div("OOC%")
        },
        {
            'id': "m_header_5",
            'children': html.Div("%OOC")
        },
        {
            'id': "m_header_6",
            'children': "Pass/Fail"
        })


def generate_metric_row_helper(index):
    item = params[index]

    div_id = item + suffix_row
    button_id = item + suffix_button_id
    sparkline_graph_id = item + suffix_sparkline_graph
    count_id = item + suffix_count
    ooc_percentage_id = item + suffix_ooc_n
    ooc_graph_id = item + suffix_ooc_g
    indicator_id = item + suffix_indicator

    # Get all data points for sparkline
    x_array = df['Batch'].tolist()
    y_array = df[item].tolist()

    return generate_metric_row(
        div_id, None,
        {
            'id': item,
            'children': html.Button(
                id=button_id,
                children=item,
                title="Click to visualize live SPC chart",
                n_clicks=0
            )
        },
        {
            'id': count_id,
            'children': str(len(y_array))  # Show total count
        },
        {
            'id': item + '_sparkline',
            'children': dcc.Graph(
                id=sparkline_graph_id,
                style={
                    'width': '100%',
                    'height': '95%',
                },
                config={
                    'staticPlot': False,
                    'editable': False,
                    'displayModeBar': False
                },
                figure={
                    'data': [{
                        'x': x_array,
                        'y': y_array,
                        'mode': 'lines+markers',
                        'name': item,
                        'line': {'color': 'rgb(255,209,95)'}
                    }],
                    'layout': {
                        'uirevision': True,
                        'margin': dict(l=0, r=0, t=4, b=4, pad=0),
                        'paper_bgcolor': 'rgb(45, 48, 56)',
                        'plot_bgcolor': 'rgb(45, 48, 56)',
                        'showgrid': False,
                        'showaxis': False,
                        'zeroline': False,
                        'showticklabels': False
                    }
                }
            )
        },
        {
            'id': ooc_percentage_id,
            'children': '0.00%'
        },
        {
            'id': ooc_graph_id + '_container',
            'children': daq.GraduatedBar(
                id=ooc_graph_id,
                color={"gradient": True, "ranges": {"green": [0, 3], "yellow": [3, 7], "red": [7, 15]}},
                showCurrentValue=False,
                max=15,
                value=0
            )
        },
        {
            'id': item + '_pf',
            'children': daq.Indicator(
                id=indicator_id,
                value=True,
                color=theme['primary']
            )
        }
    )


def generate_metric_row(id, style, col1, col2, col3, col4, col5, col6):
    if style is None:
        style = {
            'height': '100px',
            'width': '100%',
        }
    return html.Div(
        id=id,
        className='row metric-row',
        style=style,
        children=[
            html.Div(
                id=col1['id'],
                style={},
                className='one column',
                children=col1['children']
            ),
            html.Div(
                id=col2['id'],
                style={'textAlign': 'center'},
                className='one column',
                children=col2['children']
            ),
            html.Div(
                id=col3['id'],
                style={
                    'height': '100%',
                },
                className='four columns',
                children=col3['children']
            ),
            html.Div(
                id=col4['id'],
                style={},
                className='one column',
                children=col4['children']
            ),
            html.Div(
                id=col5['id'],
                style={
                    'height': '100%',

                },
                className='three columns',
                children=col5['children']
            ),
            html.Div(
                id=col6['id'],
                style={
                    'display': 'flex',
                    'justifyContent': 'center'
                },
                className='one column',
                children=col6['children']
            )
        ]
    )


def build_chart_panel():
    return html.Div(
        id='control-chart-container',
        className='twelve columns',
        children=[
            generate_section_banner('Live SPC Chart'),
            dcc.Graph(
                id="control-chart-live",
                figure=go.Figure({
                    'data': [
                        {
                            'x': [],
                            'y': [],
                            'mode': 'lines+markers',
                            'name': params[1]
                        }
                    ],
                    'layout': {
                        'paper_bgcolor': 'rgb(45, 48, 56)',
                        'plot_bgcolor': 'rgb(45, 48, 56)',
                        'showlegend': True,
                        'legend': {'font': {'color': '#95969A'}},
                        'font': {'color': '#95969A'},
                        'xaxis': {'title': 'Batch'},
                        'yaxis': {'title': params[1]},
                        'margin': {'l': 70, 'b': 70, 't': 70, 'r': 70}
                    }
                })
            )
        ]
    )


def generate_graph(interval, stored_data, param):
    """Generate main control chart with all data points"""
    if param not in stored_data:
        return {'data': [], 'layout': {}}
    
    # Use all data points
    x_array = df['Batch'].tolist()
    y_array = df[param].tolist()
    
    return {
        'data': [
            # Data points trace
            {
                'x': x_array,
                'y': y_array,
                'mode': 'lines+markers',
                'name': param,
                'line': {'color': '#119DFF'}
            },
            # UCL line
            {
                'x': x_array,
                'y': [stored_data[param]['ucl']] * len(x_array),
                'mode': 'lines',
                'name': 'UCL',
                'line': {'color': '#EF553B', 'dash': 'dash'}
            },
            # LCL line
            {
                'x': x_array,
                'y': [stored_data[param]['lcl']] * len(x_array),
                'mode': 'lines',
                'name': 'LCL',
                'line': {'color': '#EF553B', 'dash': 'dash'}
            },
            # USL line
            {
                'x': x_array,
                'y': [stored_data[param]['usl']] * len(x_array),
                'mode': 'lines',
                'name': 'USL',
                'line': {'color': '#FF9900', 'dash': 'dot'}
            },
            # LSL line
            {
                'x': x_array,
                'y': [stored_data[param]['lsl']] * len(x_array),
                'mode': 'lines',
                'name': 'LSL',
                'line': {'color': '#FF9900', 'dash': 'dot'}
            }
        ],
        'layout': {
            'uirevision': param,
            'xaxis': {'title': 'Batch', 'gridcolor': '#636363', 'showgrid': True},
            'yaxis': {'title': param, 'gridcolor': '#636363', 'showgrid': True},
            'showlegend': True,
            'legend': {'font': {'color': '#95969A'}},
            'paper_bgcolor': 'rgb(45, 48, 56)',
            'plot_bgcolor': 'rgb(45, 48, 56)',
            'font': {'color': '#95969A'},
            'margin': {'l': 70, 'b': 70, 't': 70, 'r': 70},
            'hovermode': 'closest'
        }
    }


@app.callback(
    [Output('app-tabs', 'value'),
     Output('app-content', 'children'),
     Output('Specs-tab', 'disabled'),
     Output('Control-chart-tab', 'disabled'),
     Output('tab-trigger-btn', 'style')],
    [Input('tab-trigger-btn', 'n_clicks'),
     Input('app-tabs', 'value')],  # Add input from tab clicks
    prevent_initial_call=True
)
def render_tab_content(tab_switch, tab_value):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'app-tabs':
        # Handle tab clicks
        if tab_value == 'tab1':
            return [
                'tab1',
                build_tab_1(),
                False,  # Specs-tab not disabled
                False,  # Control-chart-tab not disabled
                {'display': 'inline-block', 'float': 'right'}
            ]
        else:  # tab2
            return [
                'tab2',
                html.Div([
                    build_top_panel(),
                    build_chart_panel()
                ]),
                False,  # Specs-tab not disabled
                False,  # Control-chart-tab not disabled
                {'display': 'none'}
            ]
    else:  # Handle button click
        if tab_switch == 0:
            return [
                'tab1',
                build_tab_1(),
                False,
                False,
                {'display': 'inline-block', 'float': 'right'}
            ]
        return [
            'tab2',
            html.Div([
                build_top_panel(),
                build_chart_panel()
            ]),
            False,  # Changed from True to False
            False,
            {'display': 'none'}
        ]


# ======= Callbacks for modal popup =======
@app.callback(
    Output("markdown", "style"),
    [Input("learn-more-button", "n_clicks"),
     Input("markdown_close", "n_clicks")]
)
def update_markdown_visibility(button_click, close_click):
    ctx = callback_context

    if not ctx.triggered:
        return {"display": "none"}
    
    prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if prop_id == "learn-more-button":
        return {"display": "block"}
    elif prop_id == "markdown_close":
        return {"display": "none"}
    
    return {"display": "none"}  # default case


# Control chart callback
@app.callback(
    Output('control-chart-live', 'figure'),
    [Input(param + suffix_button_id, 'n_clicks') for param in params[1:]],
    [State('value-setter-store', 'data')]
)
def update_control_chart(*args):
    stored_data = args[-1]  # Last argument is the stored_data State
    
    ctx = callback_context
    if not ctx.triggered:
        return generate_graph(None, stored_data, params[1])  # Default to first parameter

    # Get the parameter that triggered the callback
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    param = trigger_id.replace(suffix_button_id, '')  # Remove '_button' suffix
    
    return generate_graph(None, stored_data, param)


# Parameter row update callbacks
def create_param_callback(param):
    @app.callback(
        [Output(param + suffix_count, 'children'),
         Output(param + suffix_sparkline_graph, 'extendData'),
         Output(param + suffix_ooc_n, 'children'),
         Output(param + suffix_ooc_g, 'value'),
         Output(param + suffix_indicator, 'color')],
        [Input(param + suffix_button_id, 'n_clicks')],
        [State('value-setter-store', 'data')]
    )
    def update_param_row(n_clicks, stored_data):
        if n_clicks is None:
            return '0', {'x': [[]], 'y': [[]]}, '0.00%', 0.00001, theme['primary']

        # Get the data for this parameter
        param_data = stored_data.get(param, {})
        count = str(len(param_data.get('data', [])))
        
        # Calculate OOC
        ooc_list = param_data.get('ooc', [])
        if ooc_list:
            ooc_n = f"{(ooc_list[-1] * 100):.2f}%"
            ooc_g_value = (ooc_list[-1] * 100) + 0.00001  # Add small value to prevent zero
        else:
            ooc_n = '0.00%'
            ooc_g_value = 0.00001

        # Determine indicator color
        indicator = theme['primary'] if ooc_g_value < 6 else theme['secondary']
        
        # Update sparkline
        spark_line_data = {
            'x': [[len(param_data.get('data', []))]],
            'y': [[param_data.get('data', [])[-1] if param_data.get('data', []) else 0]]
        }

        return count, spark_line_data, ooc_n, ooc_g_value, indicator


# Create callbacks for each parameter
for param in params[1:]:  # Skip 'Batch' parameter
    create_param_callback(param)


# Update piechart callback
@app.callback(
    Output('piechart', 'figure'),
    [Input(param + suffix_button_id, 'n_clicks') for param in params[1:]],  # Input from all parameter buttons
    [State('value-setter-store', 'data')]
)
def update_piechart(*args):
    stored_data = args[-1]  # Last argument is the stored_data State
    values = []
    colors = []
    
    for param in params[1:]:
        try:
            if param in stored_data:
                ooc_list = stored_data[param]['ooc']
                if ooc_list:
                    ooc_param = (ooc_list[-1] * 100) + 1
                else:
                    ooc_param = 1
            else:
                ooc_param = 1
            values.append(ooc_param)
            colors.append('rgb(206,0,5)' if ooc_param > 6 else 'rgb(0, 116, 57)')
        except (KeyError, IndexError):
            values.append(1)
            colors.append('rgb(0, 116, 57)')

    return {
        'data': [{
            'labels': params[1:],
            'values': values,
            'type': 'pie',
            'marker': {
                'colors': colors,
                'line': dict(color='#53555B', width=2)
            },
            'hoverinfo': 'label',
            'textinfo': 'label'
        }],
        'layout': {
            'uirevision': True,
            'font': {'color': '#95969A'},
            'showlegend': True,
            'legend': {'font': {'color': '#95969A'}},
            'paper_bgcolor': 'rgb(45, 48, 56)',
            'plot_bgcolor': 'rgb(45, 48, 56)'
        }
    }

# Add this callback to sync visible inputs with hidden numeric inputs
@app.callback(
    [Output('ud_usl_input', 'value'),
     Output('ud_lsl_input', 'value'),
     Output('ud_ucl_input', 'value'),
     Output('ud_lcl_input', 'value')],
    [Input('ud_usl_input', 'value'),
     Input('ud_lsl_input', 'value'),
     Input('ud_ucl_input', 'value'),
     Input('ud_lcl_input', 'value'),
     Input('metric-select-dropdown', 'value')],
    [State('value-setter-store', 'data')]
)
def update_numeric_inputs(panel_usl, panel_lsl, panel_ucl, panel_lcl, dd_select, stored_data):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # If triggered by panel inputs, return those values
    if trigger_id in ['ud_usl_input', 'ud_lsl_input', 'ud_ucl_input', 'ud_lcl_input']:
        return panel_usl, panel_lsl, panel_ucl, panel_lcl
    
    # If triggered by dropdown, return stored values for selected metric
    elif trigger_id == 'metric-select-dropdown' and dd_select in stored_data:
        return (stored_data[dd_select]['usl'],
                stored_data[dd_select]['lsl'],
                stored_data[dd_select]['ucl'],
                stored_data[dd_select]['lcl'])
    
    return no_update, no_update, no_update, no_update

# Move app.layout here, after all helper functions are defined
app.layout = html.Div(
    children=[
        build_banner(),
        build_tabs(),
        # Main app
        html.Div(
            id='app-content',
            className='container scalable',
            children=html.Div([  # Add initial content for tab2
                build_top_panel(),
                build_chart_panel()
            ])
        ),
        html.Button('Proceed to Measurement', id='tab-trigger-btn', n_clicks=0,
                    style={'display': 'none'}),  # Hide button initially
        dcc.Store(
            id='value-setter-store',
            data=init_value_setter_store(),
            storage_type='memory'
        ),
        generate_modal(),
    ]
)
# Running the server
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
