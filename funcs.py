#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module holding auxiliary functions for app.
"""

import collections
import pandas as pd

def load_data():
    """Loads data from github.com/datasets as a dictionary of arrays"""

    source = "https://raw.githubusercontent.com/datasets/covid-19/master/data/"
    dataset = "time-series-19-covid-combined.csv"

    df = pd.read_csv(source + dataset)
    # df['Date'] = pd.to_datetime(df['Date'])

    df.drop(columns=['Lat', 'Long', 'Deaths', 'Recovered'], inplace=True)
    
    df = df.groupby(['Country/Region', 'Date'], as_index=False).sum()

    # Duplicated Countries:
    #   Timor-Leste/East Timor
    #     data matches Timor-Leste official site.
    #   Cabo Verde/Cape Verde
    #     data matches Cabo Verde official site.
    ignore = set(['East Timor', 'Cabo Verde', 'Cruise Ship'])
    
    synonyms = {
        'United States of America': 'US',
        'Congo': 'Congo (Brazzaville)',
        'Democratic Republic of the Congo': 'Congo (Kinshasa)',
        'Iran (Islamic Republic of)': 'Iran',
        # 'Timor-Leste': 'East Timor',
        'Brunei Darussalam': 'Brunei',
        'China, Taiwan Province of China': 'Taiwan*',
        'United Republic of Tanzania': 'Tanzania',
        'Republic of Moldova': 'Moldova',
        'Bahamas, The': 'Bahamas',
        'Venezuela (Bolivarian Republic of)': 'Venezuela, Bolivarian Republic of',
        'Bolivia (Plurinational State of)': 'Bolivia, Plurinational State of',
        'Russian Federation': 'Russia',
        'Viet Nam': 'Vietnam',
        'Bolivia (Plurinational State of)': 'Bolivia',
        'Gambia, The': 'Gambia',
        "Dem. People's Republic of Korea": 'Korea, South',
        'Syrian Arab Republic': 'Syria',
        'Cabo Verde': 'Cape Verde',
    }

    pop_df = pd.read_csv('data/world_population.csv')
    pop_dict = {}
    for (_, _, country, value) in pop_df.values:
        tr_country = synonyms.get(country, country)
        pop_dict[tr_country] = float(value) * 1000

    data = collections.defaultdict(list)
    population, dates = {}, {}
    for (country, date, value) in df.values:
        if country in ignore:
            continue

        data[country].append(value)
        dates[date] = None  # ordered unique
        population[pop_dict[country]] = None

    assert len(population) == len(data), f"{len(population)}, {len(data)}"

    return (data, list(data), list(dates), list(population))


def load_data2():

    ignore = set(['Cruise Ship'])

    source = "https://s3-us-west-1.amazonaws.com/starschema.covid/JHU_COVID-19.csv"

    df = pd.read_csv(source)

    # Select Confirmed Cases
    df = df[df['Case_Type'] == 'Confirmed']

    # Drop accessory columns
    df.drop(columns=['Lat', 'Long', 'Case_Type', 'Difference', 'ISO3166-2', 'Last_Update_Date'], inplace=True)

    # Group by country
    df = df.groupby(['Country/Region', 'Date'], as_index=False).sum()

    # Merge with population numbers from UN
    pop_df = pd.read_csv('data/world_population.csv')
    df = df.set_index('Country/Region').join(pop_df.set_index('Country/Region')).reset_index()

    data = collections.defaultdict(list)
    population, dates = {}, {}
    for (country, date, cases, pop) in df.values:
        if country in ignore:
            continue

        data[country].append(cases)
        dates[date] = None  # ordered unique
        population[float(pop)] = None

    # print(df[df['PopTotal'].isna()]['Country/Region'].unique())

    # Check that all countries have all data points. Pad with 0s otherwise.
    n_dates = len(dates)
    for name in data:
        v = data[name]
        if len(v) < n_dates:
            # print(f'Padding: {name}')
            n_pad = [0 for _ in range(n_dates - len(v))]
            data[name] = n_pad + data[name]


    return (data, list(data), list(dates), list(population))


if __name__ == '__main__':
    load_data()