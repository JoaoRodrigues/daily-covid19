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
		'Bahamas': 'Bahamas, The',
		'Venezuela (Bolivarian Republic of)': 'Venezuela',
		'Russian Federation': 'Russia',
		'Viet Nam': 'Vietnam',
		'Bolivia (Plurinational State of)': 'Bolivia',
		'Gambia': 'Gambia, The',
		"Dem. People's Republic of Korea": 'Korea, South',
		'Syrian Arab Republic': 'Syria',
		'Cabo Verde': 'Cape Verde',
	}

	pop_df = pd.read_csv('data/world_population.csv')
	pop_dict = {}
	for (_, _, country, value) in pop_df.values:
		country = synonyms.get(country, country)
		pop_dict[country] = float(value) * 1000

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

if __name__ == '__main__':
	load_data()