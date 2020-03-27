#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analysis Dashboard for COVID-19 Pandemic Evolution.
"""

import collections
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np
import pandas as pd

from statsmodels.nonparametric import smoothers_lowess

def _unique_sort(iterable):
    """Returns unique elements in the iterable, in order of appearance"""
    d = collections.OrderedDict()
    for i in iterable:
        d[i] = None
    return list(d.keys())


# Source of data
# DATA = "https://s3-us-west-1.amazonaws.com/starschema.covid/JHU_COVID-19.csv"
DATA = "https://levitt-covid19-data.s3-us-west-1.amazonaws.com/Data_COVID-19.csv"

def read_data_as_dataframe(url):

    df = pd.read_csv(
        url,
        # Which cols to load
        usecols=[
            'Country/Region',
            'Province/State',
            'County',
            'Date',
            'Case_Type',
            'Cases'
        ],
        # Specify dtype to save memory on load
        dtype={
            'Country/Region': 'str',
            'Province/State': 'str',
            'County': 'str',
            'Date': 'str',
            'Case_Type': 'str',
            'Cases': 'int'
        }
    )

    # Convert dates to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')

    return df


# Read and prepare data/inputs
df = read_data_as_dataframe(DATA)

countries = list(df['Country/Region'].unique())
provinces = list(df['Province/State'].unique())
counties = list(df['County'].unique())
agg_regions = countries + provinces + counties

dates_as_str = [
    d.strftime('%b %d')
    for d in _unique_sort(df['Date'])
]

region_selector_options = [
    {'label': str(item), 'value': str(item)}
    for item in agg_regions
]

dataset_selector_options = [
    {'label': str(v), 'value': str(v)}
    for v in df['Case_Type'].unique()
]

# Create Dash/Flask app
app = dash.Dash(__name__)
server = app.server  # for heroku deployment

app.layout = html.Div(
    id="content",
    children=[

        html.Div(
            id="title",
            children=[
                html.P(
                    'Dashboard to analyze COVID-19 datasets',
                ),
            ]
        ),

        html.Div(
            id="selectors",
            children=[
                html.Label(
                    id='dataset-label',
                    children=[
                        "Select a subset of the data:",
                        dcc.Dropdown(
                            id='dataset-selector',
                            multi=True,
                            options=[
                                {'label': 'Confirmed', 'value': 'Confirmed'}
                            ],
                            value=['Confirmed']
                        ),
                    ]
                ),

                html.Label(
                    id='region-label',
                    children=[
                        "Select a region:",
                        dcc.Dropdown(
                            id='region-selector',
                            multi=True,
                            # Some defaults
                            options=[
                                {'label': 'Spain', 'value': 'Spain'},
                                {'label': 'Italy', 'value': 'Italy'}
                            ],
                            value=['Spain', 'Italy']
                        ),
                    ]
                ),
            ]
        ),

        html.Div(
            id='data-mode-container',
            children=[
                html.Label(
                    children=[
                        dcc.Checklist(
                            id='lowess-checkbox',
                            options=[
                                {'label': 'Smooth with LOWESS', 'value': 'fit'},
                            ],
                            value=['']
                        ),
                    ]
                ),
                html.Label(
                    children=[
                        dcc.Checklist(
                            id='log-checkbox',
                            options=[
                                {'label': 'Use log scale', 'value': 'log'},
                            ],
                            value=['']
                        ),
                    ]
                ),
            ]
        ),

        html.Div(
            className="graph-area",
            children=[
                html.Div(
                    id='rawplot'
                ),
                html.Div(
                    id='ratioplot'
                ),

                dcc.RangeSlider(
                    id='date-selector',
                    min=0,
                    max=len(dates_as_str),
                    step=1,
                    pushable=1,  # min 1 day
                    allowCross=False,
                    value=[0, len(dates_as_str)],  # default, all data points
                    marks={
                        idx: dates_as_str[idx]
                        for idx in range(0, len(dates_as_str), 7)
                    },
                ),
            ]
        )
    ]
)


# Callbacks
# We can be smarter and update the charts in tandem, to avoid recalculations
# but for now it'll do.

@app.callback(
    Output("dataset-selector", "options"),
    [Input("dataset-selector", "search_value")],
    [State("dataset-selector", "value")],
)
def update_dataselector_options(search_value, value):
    """Fills the search box dinamically as users type."""

    if not search_value:
        raise PreventUpdate

    return [
        o for o in dataset_selector_options
        if search_value in o["label"] or o["value"] in (value or [])
    ]

@app.callback(
    Output("region-selector", "options"),
    [Input("region-selector", "search_value")],
    [State("region-selector", "value")],
)
def update_region_selector_options(search_value, value):
    """Fills the search box dinamically as users type."""

    if not search_value:
        raise PreventUpdate

    return [
        o for o in region_selector_options
        if search_value in o["label"] or o["value"] in (value or [])
    ]


@app.callback(
    Output("rawplot", "children"),
    [
        Input('dataset-selector', 'value'),
        Input('region-selector', 'value'),
        Input('date-selector', 'value'),
        Input('lowess-checkbox', 'value'),
        Input('log-checkbox', 'value')
    ],
)
def draw_lineplots(datasets, regions, dates, datamode, transform):
    """Updates plots with options from region-selector"""

    datamode = datamode[-1]  # stupid hack for stupid checkboxes
    transform = transform[-1]

    if not regions:
        raise PreventUpdate

    # Select x range
    x0, xN = dates
    x_data = dates_as_str[x0: xN]

    figdata = []
    for dataset in datasets:

        # Get selected data
        y_data = select_data(df, dataset, regions)

        # Trim Y data accordingly
        y_data = [y[x0: xN] for y in y_data]

        # Fit before transforming.
        if datamode == 'fit':
            y_data = list(map(lowess, y_data))

        # Log scale?
        if transform == 'log':
            y_data = list(map(np.log, y_data))

        # Make Figure Data
        figdata += make_figdata(x_data, y_data, regions, dataset)

    fig = dcc.Graph(
        id='confirmed-cases',
        figure={
            'data': figdata,
            'layout': {
                'xaxis': {
                    'zeroline': False,
                    'showline': True,
                    'mirror': True,
                    'linewidth': 1,
                    'linecolor': 'black'
                },
                'yaxis': {
                    'title': 'Number of Cases',
                    'zeroline': False,
                    'showline': True,
                    'mirror': True,
                    'linewidth': 1,
                    'linecolor': 'black'
                },
                'margin': {'t': 20, 'pad': 0},
                'hovermode': 'closest',
            },
        },
    )

    return [fig]


@app.callback(
    Output("ratioplot", "children"),
    [
        Input('dataset-selector', 'value'),
        Input('region-selector', 'value'),
        Input('date-selector', 'value'),
        Input('lowess-checkbox', 'value'),
        Input('log-checkbox', 'value')
    ],
)
def draw_change_ratio(datasets, regions, dates, datamode, transform):
    """Updates plots with options from region-selector"""

    datamode = datamode[-1]  # stupid hack for stupid checkboxes
    transform = transform[-1]

    if not regions:
        raise PreventUpdate

    # Select x range
    x0, xN = dates
    x_data = dates_as_str[x0: xN]

    # Set y_range
    y_range = [-0.5, 1.5]

    figdata = []
    for dataset in datasets:
        # Get selected data
        y_data = select_data(df, dataset, regions)

        # Trim Y data accordingly
        y_data = [y[x0: xN] for y in y_data]

        # Do we fit?
        if datamode == 'fit':
            y_data = list(map(lowess, y_data))

        # Calculate change ratio
        y_data = change_ratio(y_data)

        # Log scale?
        if transform == 'log':
            y_data = list(map(np.log, y_data))
            y_range = list(map(np.log, y_range))

        # Make Figure Data
        figdata += make_figdata(x_data, y_data, regions, dataset)

    fig = dcc.Graph(
        id='confirmed-cases',
        figure={
            'data': figdata,
            'layout': {
                'xaxis': {
                    'zeroline': False,
                    'showline': True,
                    'mirror': True,
                    'linewidth': 1,
                    'linecolor': 'black'
                },
                'yaxis': {
                    'title': 'Case Change Ratio (1 day)',
                    'zeroline': False,
                    'showline': True,
                    'mirror': True,
                    'linewidth': 1,
                    'linecolor': 'black',
                    'range': y_range
                },
                'margin': {'t': 20, 'pad': 0},
                'hovermode': 'closest',
            }
        }
    )

    return [fig]


# Auxiliary functions
def lowess(data, frac=0.15, it=0):
    return smoothers_lowess.lowess(
        endog=data,
        exog=list(range(len(data))),
        frac=frac,
        it=it
    )[:, 1]


def make_figdata(x_data, y_data, labels, dataset_name):
    """Returns a figure.data list to pass to dcc.Graph"""

    return [
        {
            'x': x_data,
            'y': y_data[i],
            'name': f"{l} ({dataset_name})",
            # 'mode': 'markers',
            # 'marker': {'size': 10}
            'mode': 'lines+markers',
            'line': {'width': 2.5},
            'marker': {'size': 8}
        } for i, l in enumerate(labels)
    ]


def select_data(dataframe, subset, regions):
    """Returns a subset of the entire dataframe"""

    y_data = []

    for r in regions:
        mask = (
            (dataframe['Country/Region'] == r) | \
            (dataframe['Province/State'] == r) | \
            (dataframe['County'] == r)
        ) & (dataframe['Case_Type'] == subset)

        y = dataframe[mask]
        if len(y) > len(dates_as_str):  # eg China selects all provinces
            y = dataframe[mask].groupby('Date').sum()

        y = list(y['Cases'])
        y_data.append(y)

    # Some data (US counties) only has data from a certain date. Left-pad with 0
    for idx, ytrace in enumerate(y_data[:]):
        diff = len(dates_as_str) - len(ytrace)
        if diff > 0:
            y_data[idx] = [0 for _ in range(diff)] + ytrace

    return y_data


def change_ratio(data):
    """Calculates the ratio N+1/N for each element in data"""

    d = data[:]
    for idx, trace in enumerate(data):
        ratio = []
        derivative = [a-b for a,b in zip(trace[1:], trace[:-1])]
        cumulative = trace[1:]

        for a, b in zip(derivative, cumulative):
            try:
                r = a / b
            except ZeroDivisionError:
                r = 0.0

            ratio.append(r)

        d[idx] = [0] + ratio

    return d


if __name__ == '__main__':
    app.run_server(debug=False)
