# Importiamo le librerie necessarie
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from prophet import Prophet


 

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
italy_catastrofi = italy_catastrofi[['Country', 'DisNo.', 'Latitude', 'Longitude', 'Date', 'Total Deaths', 'Total Affected']] #'Start Year', 'Start Month', 'Start Day'
italy_catastrofi = italy_catastrofi.dropna(subset=['Latitude', 'Longitude']) #na in latitude and longitude


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
    start_date=end_date - pd.Timedelta(days=6)
    #start_date = end_date - pd.DateOffset(years=1)
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


print(final_daily_dataframe)

dataframes_per_anno = {year: final_daily_dataframe[final_daily_dataframe['date'].dt.year == year] for year in final_daily_dataframe['date'].dt.year.unique()}

print(dataframes_per_anno)

# Lista per raccogliere i dataframe annuali di riepilogo
summary_dfs = []

max_min_df = []
# Cicla su ogni anno e dataframe nel dizionario
for anno, df in dataframes_per_anno.items():
    # latitude=df['latitude'].iloc[0]
    # longitude=df['longitude'].iloc[0]

    # Calcola i valori massimi e minimi per le colonne specificate
    max_values = df[['temperature_2m_mean', 'rain_sum', 'wind_speed_10m_max']].max()
    min_values = df[['temperature_2m_mean', 'rain_sum', 'wind_speed_10m_max']].min()

    temp_max = max_values["temperature_2m_mean"]
    rain_max = max_values["rain_sum"]
    wind_max = max_values["wind_speed_10m_max"]

    temp_min = min_values["temperature_2m_mean"]
    rain_min = min_values["rain_sum"]
    wind_min = min_values["wind_speed_10m_max"]

    df['temp_max'] = temp_max
    df['rain_max'] = rain_max
    df['wind_max'] = wind_max

    df['temp_min'] = temp_min
    df['rain_min'] = rain_min
    df['wind_min'] = wind_min

    df['latitude'] = df['latitude'].round(2)
    df['longitude'] = df['longitude'].round(2)

    # Aggiungi il dataframe di riepilogo alla lista
    max_min_df.append(df)

# Concatenazione dei dataframe in un unico dataframe finale
final_max_min_df = pd.concat(max_min_df, ignore_index=True)
print(final_max_min_df)

previsioni = pd.read_csv("previsioni_meteo_2025_stagionale.csv")

print(previsioni)

merged_df = pd.merge(previsioni, final_max_min_df[['latitude', 'longitude',"temp_min","temp_max","rain_min","rain_max", "wind_min","wind_max"]], on=['latitude', 'longitude'], how='inner')


print("EVENTI ESTREMI")
# Filtra le righe in cui 'temperature_2m_mean' rientra nell'intervallo [Min, Max]
filtered_df = merged_df[
    (merged_df['temperature_2m_mean'] >= merged_df['temp_min']) &
    (merged_df['temperature_2m_mean'] <= merged_df['temp_max']) &
    (merged_df['rain_sum'] >= merged_df['rain_min']) &
    (merged_df['rain_sum'] <= merged_df['rain_max']) &
    (merged_df['wind_speed_10m_max'] >= merged_df['wind_min']) &
    (merged_df['wind_speed_10m_max'] <= merged_df['wind_max'])
]

filtered_df = filtered_df.drop_duplicates()
print(filtered_df)


previsioni['date'] = pd.to_datetime(previsioni['date'])

base_previsioni=pd.read_csv("meteo_2023_2024")
base_previsioni = base_previsioni[['date','latitude', 'longitude', 'temperature_2m_mean', 'rain_sum', 'wind_speed_10m_max']]
base_previsioni=base_previsioni.dropna()
# Remove the timezone part by splitting and keeping only the date and time
base_previsioni['date'] = base_previsioni['date'].str.split('+').str[0]
# Convert `date` to datetime format
base_previsioni['date'] = pd.to_datetime(base_previsioni['date'])
print(base_previsioni)


# Define a function to fit and predict each target variable
def forecast_location_variable(df, target_column, periods=365*5):
    # Prepare the dataframe for Prophet
    df_prophet = df[['date', target_column]].rename(columns={'date': 'ds', target_column: 'y'})
    
    # Instantiate and fit the Prophet model
    model = Prophet()
    model.fit(df_prophet)
    
    # Make future dataframe and predict
    #future = model.make_future_dataframe(periods=periods, freq='D')
    future = model.make_future_dataframe(periods=6*365, freq='D')  # 6 anni di previsioni giornaliere
    forecast = model.predict(future)

     # Filtra il periodo tra il 2025 e il 2030
    forecast_2025_2030 = forecast[(forecast['ds'] >= '2024-10-25') & (forecast['ds'] <= '2031-01-01')]

    print(forecast_2025_2030)
    # Return the forecast with only the required columns
    #return forecast[['ds', 'yhat']].rename(columns={'yhat': target_column})
    return forecast_2025_2030[['ds', 'yhat']].rename(columns={'yhat': target_column})

# Initialize empty list to collect forecast data
all_forecasts = []

# Loop through each unique (longitude, latitude) pair
for (longitude, latitude), df_location in base_previsioni.groupby(['longitude', 'latitude']):
    # Forecast each variable
    temp_forecast = forecast_location_variable(df_location, 'temperature_2m_mean')
    rain_forecast = forecast_location_variable(df_location, 'rain_sum')
    wind_forecast = forecast_location_variable(df_location, 'wind_speed_10m_max')
    
    # Merge forecasts for this location on 'ds'
    location_forecast = temp_forecast.merge(rain_forecast, on='ds').merge(wind_forecast, on='ds')
    
    # Add longitude and latitude columns to each forecast
    location_forecast['longitude'] = longitude
    location_forecast['latitude'] = latitude
    
    # Append to the list
    all_forecasts.append(location_forecast)

# Combine all forecasts into a single dataframe
combined_2025_2030_forecast = pd.concat(all_forecasts).rename(columns={'ds': 'date'})

print(combined_2025_2030_forecast)

print("DATI PREVISIONE")
print(combined_2025_2030_forecast.head(1500))

# TEMPERATURE SBALLATISSIME (-137)

exit()


exit()
merged_df = pd.merge(combined_2025_2030_forecast, final_max_min_df[['latitude', 'longitude',"temp_min","temp_max","rain_min","rain_max", "wind_min","wind_max"]], on=['latitude', 'longitude'], how='inner')
#print(merged_df)

print("EVENTI ESTREMI 2025-2030")
filtered_df_2025_2030 = merged_df[
    (merged_df['temperature_2m_mean'] >= merged_df['temp_min']) &
    (merged_df['temperature_2m_mean'] <= merged_df['temp_max']) &
    (merged_df['rain_sum'] >= merged_df['rain_min']) &
    (merged_df['rain_sum'] <= merged_df['rain_max']) &
    (merged_df['wind_speed_10m_max'] >= merged_df['wind_min']) &
    (merged_df['wind_speed_10m_max'] <= merged_df['wind_max'])
]

filtered_df_2025_2030 = filtered_df_2025_2030.drop_duplicates()
#print(filtered_df)
print("DATI FILTRATI")
print(filtered_df.head(20))

exit()

italy_catastrofi['latitude'] = italy_catastrofi['Latitude'].round(2)
italy_catastrofi['longitude'] = italy_catastrofi['Longitude'].round(2)
# print(italy_catastrofi)

merged_df_deaths_affected = pd.merge(filtered_df_2025_2030, italy_catastrofi[['latitude', 'longitude',"Total Deaths", "Total Affected"]], on=['latitude', 'longitude'], how='inner')


# Replace NaN values with 0
merged_df_deaths_affected.fillna(0, inplace=True)

# Convert all columns to integer type
# First, ensure the DataFrame is free from NaN values
merged_df_deaths_affected = merged_df_deaths_affected.astype(int)
print(merged_df_deaths_affected)
#trovare i morti più danni economici e fare scala