# Importiamo le librerie necessarie
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

 

# Step 1: Caricamento dei dati meteo storici e l'archivio delle catastrofi
#sensori = pd.read_csv('LCD_ITM00016344_2017.csv')
#sensori = pd.read_csv('3823045.csv')
italy_sensori = pd.read_csv('open-meteo-52.55N13.41E38m.csv')
#catastrofi = pd.read_csv('natural-disasters.csv')
#italy_catastrofi = catastrofi[catastrofi['Country name'] == 'Italy']
#italy_catastrofi = pd.read_csv('catastrofi.csv', sep=';')
italy_catastrofi = pd.read_excel('disastri.xlsx', sheet_name='EM-DAT Data')

italy_catastrofi.dropna(subset=['Start Day'], inplace=True)
italy_catastrofi['Start Day'] = italy_catastrofi['Start Day'].astype(int)
italy_catastrofi['Start Month'] = italy_catastrofi['Start Month'].astype(int)
italy_catastrofi['Start Year'] = italy_catastrofi['Start Year'].astype(int)
italy_catastrofi['Date'] = pd.to_datetime(italy_catastrofi['Start Year'].astype(str) + '-' +
                                          italy_catastrofi['Start Month'].astype(str) + '-' +
                                          italy_catastrofi['Start Day'].astype(str), 
                                          errors='coerce')

# Primo dataset
italy_catastrofi = italy_catastrofi[['Country', 'DisNo.', 'Latitude', 'Longitude', 'Date']] #'Start Year', 'Start Month', 'Start Day'
italy_catastrofi = italy_catastrofi.dropna(subset=['Latitude', 'Longitude']) #na in latitude and longitude



#print(italy_sensori['time'])
# print(italy_catastrofi['Date'])

# filtered_italy_catastrofi = italy_catastrofi['Date'][(italy_catastrofi['Date'] >= '2015-01-01')]

# italy_sensori['time'] = pd.to_datetime(italy_sensori['time'], errors='coerce')
# italy_catastrofi['Date'] = pd.to_datetime(italy_catastrofi['Date'], errors='coerce')

# # Estrai mese e anno per entrambe le colonne
# italy_sensori['year_month'] = italy_sensori['time'].dt.to_period('M')
# italy_catastrofi['year_month'] = italy_catastrofi['Date'].dt.to_period('M')

# # Trova i valori comuni di year_month
# common_dates = italy_sensori[italy_sensori['year_month'].isin(italy_catastrofi['year_month'])] #date in entrambi i dataset per anno e mese

# # Effettua il merge dei due dataset sui valori comuni di 'year_month'
# merged_data = pd.merge(italy_sensori, italy_catastrofi[['Date', 'year_month']], on='year_month', how='inner')

# Visualizza il risultato
# print("Dati dei sensori con la data della catastrofe nello stesso anno e mese:")
# print(merged_data)


import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://archive-api.open-meteo.com/v1/archive"


print(italy_catastrofi)
# List to hold parameter dictionaries
params_list = []

italy_catastrofi['Date']=italy_catastrofi['Date'].dt.strftime('%Y-%m-%d')

# Iterate through the rows of the DataFrame
for index, row in italy_catastrofi.iterrows():
    end_date = pd.to_datetime(row['Date'])
    #start_date=end_date - pd.Timedelta(days=6)
    start_date = end_date - pd.DateOffset(years=1)
    start_date_string = start_date.strftime('%Y-%m-%d')

    print(end_date)
    print(start_date_string)

    params = {
        "latitude": row['Latitude'],
        "longitude": row['Longitude'],
        "start_date":  start_date_string, #"2023-10-25",
	    "end_date": row['Date'],  #"2024-10-25",
	    "daily": ["weather_code", "temperature_2m_mean", "rain_sum", "wind_speed_10m_max"]
    }
    # Append the dictionary to the list
    params_list.append(params)

all_daily_dataframes = []
# Optionally, print the list of parameters
for params in params_list:
    print(params)
    responses = openmeteo.weather_api(url, params=params)

     # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_mean = daily.Variables(1).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(2).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(3).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
    	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = daily.Interval()),
    	inclusive = "left"
    )}
    daily_data["weather_code"] = daily_weather_code
    daily_data["temperature_2m_mean"] = daily_temperature_2m_mean
    daily_data["rain_sum"] = daily_rain_sum
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
    daily_data["latitude"] = params['latitude']
    daily_data["longitude"] = params['longitude']

    daily_dataframe = pd.DataFrame(data = daily_data)
    all_daily_dataframes.append(daily_dataframe)

# Concatenate all DataFrames into one big DataFrame
final_daily_dataframe = pd.concat(all_daily_dataframes, ignore_index=True)

final_daily_dataframe = final_daily_dataframe[['date', 'latitude', 'longitude', 'temperature_2m_mean', 'rain_sum', 'wind_speed_10m_max']]

# Filter the DataFrame
filtered_records = final_daily_dataframe[
    (final_daily_dataframe['date'].dt.year == 2008) & 
    (final_daily_dataframe['latitude'] == 41.8300) & 
    (final_daily_dataframe['longitude'] == 13.160)
]

# Display the filtered records
# Calculate max and min for the specified columns
max_values = filtered_records[['temperature_2m_mean', 'rain_sum', 'wind_speed_10m_max']].max()
min_values = filtered_records[['temperature_2m_mean', 'rain_sum', 'wind_speed_10m_max']].min()

# Create a summary DataFrame to display the results
summary_df = pd.DataFrame({
    'Max': max_values,
    'Min': min_values
})

# Display the summary DataFrame
print(summary_df)



# Filter the DataFrame
filtered_records = final_daily_dataframe[
    (final_daily_dataframe['date'].dt.year == 2009) & 
    (final_daily_dataframe['latitude'] == 38.1100) & 
    (final_daily_dataframe['longitude'] == 15.730)
]

print(italy_catastrofi)

exit()


