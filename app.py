#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is an ugly, preliminary, hacky example.
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import numpy as np

import plotly
import plotly.graph_objects as go

import funcs

# Color Scale
# Taken from: plotly.colors.cmocean.py
amp = [
    "rgb(255, 255, 255)",
    # "rgb(241, 236, 236)",
    "rgb(230, 209, 203)",
    "rgb(221, 182, 170)",
    "rgb(213, 156, 137)",
    "rgb(205, 129, 103)",
    "rgb(196, 102, 73)",
    "rgb(186, 74, 47)",
    "rgb(172, 44, 36)",
    "rgb(149, 19, 39)",
    "rgb(120, 14, 40)",
    "rgb(89, 13, 31)",
    "rgb(60, 9, 17)",
]

# Load data
data, countries, dates, pop = funcs.load_data()


def make_labels(d):
    """Makes hover labels"""
    return [
        f'Change: {d:6d} \nPopulation: {pop[i]:12.2f}'
        for i, d in enumerate(d)
    ]

def calculate_change(d, t):
    """
    Difference in number of cases normalized per country, 
    expressed as per 10.000 people.
    """

    if t:
        t = (-1 * t) - 1  # if t==1: return v[-1] - v[-2] (1 day)

    d = [
        v[-1] - v[t]
        for v in data.values()
    ]

    n = [1e4 * (d/pop[idx]) for idx, d in enumerate(d)]
    return d, n


# Setup app
app = dash.Dash(__name__)

app.layout = html.Div(
    className="content",
    children=[
        html.P(
            'Evolution of COVID-19 Pandemic - IN DEVELOPMENT - DATA MIGHT BE WRONG',
            className='title'
        ),

        html.Div(
            className="selectors",
            children=[
                dcc.RadioItems(
                    id='date-range-button',
                    options=[
                        {'label': '1d', 'value': 1},
                        {'label': '3d', 'value': 3},
                        {'label': '1w', 'value': 7},
                        {'label': '2w', 'value': 14},
                        {'label': '1m', 'value': 30},
                        {'label': 'all', 'value': 0}
                    ],
                    value=1
                ),
                dcc.RadioItems(
                    id='data-format-button',
                    options=[
                        {'label': 'raw', 'value': 'raw'},
                        {'label': 'normalized', 'value': 'norm'},
                    ],
                    value='raw'
                ),
            ]
        ),

        # html.Div(
        #     className="lineplot",
        #     children=[
        #         dcc.Graph(
        #                 id='line-plot',
        #         ),
        #     ]
        # ),

        html.Div(
            className="choropleth",
            children=[
                dcc.Graph(
                        id='map-graph',
                ),
            ]
        ),

        html.Div(
            className="fake-colorbar",
            children=[
                dcc.Graph(
                        id='map-colorbar',
                ),
            ]
        ),

        # html.P(
        #     'Developed & Maintained by Levitt Lab at Stanford',
        #     className='footer'
        # ),
    ]
)

# Interactivity
@app.callback(
    Output('map-graph', 'figure'),
    [
        Input('date-range-button', 'value'),
        Input('data-format-button', 'value')
    ]
)
def draw_choropleth(t, fmt):
    """Draws the map chart. Returns figure."""

    r, n = calculate_change(data, t)
    if fmt == 'raw':
        d = r
    else:
        d = n

    return {
        'data': [
            go.Choropleth(
                locationmode='country names',
                locations=countries,
                z=d,
                colorscale=amp,
                marker_line_color='lightgray', # regional boundaries
                marker_line_width=0.5,
                showscale=False,
                # customdata=None,
                text=make_labels(r)
            ),
        ],
        'layout': go.Layout(
            {
                'height': 1000,
                'geo': {
                    'resolution': 110,
                    'showframe': False,
                    'showcoastlines': True,
                    'coastlinecolor': 'lightgray',
                    'projection_type': 'natural earth'
                },
                'margin': {"r": 0, "t": 0, "l": 0, "b": 0},
                'transition': {'duration': 50},
            }
        )
    }


@app.callback(
    Output('map-colorbar', 'figure'),
    [
        Input('date-range-button', 'value'),
        Input('data-format-button', 'value')
    ]
)
def draw_colorbar(t, fmt):

    # recalculate...
    r, n = calculate_change(data, t)

    if fmt == 'raw':
        d = r
    else:
        d = n

    # Make labels for 'colorbar'
    bins = np.linspace(0, max(d), len(amp))
    _, edges = np.histogram(d, bins)
    edges = [round(i, 1) for i in edges]
    labelanchor = 1/len(edges)
    labelpad = 1/(2*len(edges))

    return {
        'data': [
            # Plotly does not support horizontal colorbars
            # so we explictly make our own as an hbar chart.
            go.Bar(
                orientation='h',
                y=['amp'] * len(amp),
                x=[1] * len(amp),
                marker=dict(color=amp)
            )
        ],
        'layout': go.Layout(
            {
                'title': {
                    'text': 'New Cases per 10.000 people',
                    'xanchor': 'center',
                    'x': 0.5,
                    'yanchor': 'top',
                    'y': 0.99
                },
                'height': 75,
                'margin': {"r": 0, "t": 0, "l": 0, "b": 0},
                'transition': {'duration': 250},
                'barmode': 'stack',
                'barnorm': 'fraction',
                'bargap': 0.5,
                'showlegend': False,
                'xaxis': {
                    'range': [-0.02, 1.02],
                    'showticklabels': False,
                    'showgrid': False,
                    'zeroline': False,
                },
                'yaxis': {
                    'showticklabels': False,
                    'showgrid': False,
                    'zeroline': False,
                },
                'annotations': [
                    {
                        'x': 0 + labelpad+idx*labelanchor, 
                        'y': -0.35, 
                        'xref': 'x', 
                        'yref': 'y', 
                        'text': str(e), 
                        'showarrow': False
                    } for idx, e in enumerate(edges)
                ]
            }
        )
    }

# @app.callback(
#     Output('line-plot', 'figure'),
#     [Input('date-range-button', 'value')]
# )
# def draw_lineplot(t=1):
#     """Draws the line plot. Returns figure."""

#     if t:
#         t = (-1 * t) - 1

#     # plotted_data = []
#     # for v in data.values():
#     #     print(v[t], v[-1])
#     #     if v[t]:
#     #         v = (100 * v[-1]) / v[t]
#     #     plotted_data.append(v)
#     plotted_data = [
#         v[-1] - v[t]  for v in data.values()
#     ]

#     return {
#         'data': [
#             go.Scatter(
#                 x=dates,
#                 y=data['US'],
#                 # locations=countries,
#                 # z=plotted_data,
#                 # colorscale=amp,
#                 # marker_line_color='lightgray', # regional boundaries
#                 # marker_line_width=0.5,
#                 # showscale=False,
#                 # # dragmode=False,
#                 # # customdata=None,
#                 # colorbar={
#                 #         'title': {
#                 #             'text': 'Confirmed Cases',
#                 #         },
#                 #         'lenmode': "fraction",
#                 #         'len': 0.5,
#                 # },
#             ),
#         ],
#         'layout': go.Layout(
#             {
#                 'width': 400,
#                 'height': 400,
#                 'margin': {"r": 0, "t": 0, "l": 0, "b": 0},
#                 'transition': {'duration': 250},
#             }
#         )
#     }

if __name__ == '__main__':
    app.run_server(debug=True)
