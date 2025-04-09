from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json
import pzwglobals

logger = pzwglobals.logger

"""
map open weather codes and icon names to names of our custom icons
"""

CODE_MAP = {
	'200' : 'rain', #Thunderstorm	thunderstorm with light rain	 11d
	'201' : 'rain', #Thunderstorm	thunderstorm with rain	 11d
	'202' : 'rain', #Thunderstorm	thunderstorm with heavy rain	 11d
	'210' : 'rain', #Thunderstorm	light thunderstorm	 11d
	'211' : 'rain', #Thunderstorm	thunderstorm	 11d
	'212' : 'rain', #Thunderstorm	heavy thunderstorm	 11d
	'221' : 'rain', #Thunderstorm	ragged thunderstorm	 11d
	'230' : 'rain', #Thunderstorm	thunderstorm with light drizzle	 11d
	'231' : 'rain', #Thunderstorm	thunderstorm with drizzle	 11d
	'232' : 'rain', #Thunderstorm	thunderstorm with heavy drizzle	 11d
	'300' : 'sleet', #Drizzle	light intensity drizzle	 09d
	'301' : 'sleet', #Drizzle	drizzle	 09d
	'302' : 'sleet', #Drizzle	heavy intensity drizzle	 09d
	'310' : 'sleet', #Drizzle	light intensity drizzle rain	 09d
	'311' : 'sleet', #Drizzle	drizzle rain	 09d
	'312' : 'sleet', #Drizzle	heavy intensity drizzle rain	 09d
	'313' : 'sleet', #Drizzle	shower rain and drizzle	 09d
	'314' : 'sleet', #Drizzle	heavy shower rain and drizzle	 09d
	'321' : 'sleet', #Drizzle	shower drizzle	 09d
	'500' : 'sleet', #Rain	light rain	 10d
	'501' : 'rain', #Rain	moderate rain	 10d
	'502' : 'rain', #Rain	heavy intensity rain	 10d
	'503' : 'rain', #Rain	very heavy rain	 10d
	'504' : 'rain', #Rain	extreme rain	 10d
	'511' : 'sleet', #Rain	freezing rain	 13d
	'520' : 'sleet', #Rain	light intensity shower rain	 09d
	'521' : 'sleet', #Rain	shower rain	 09d
	'522' : 'rain', #Rain	heavy intensity shower rain	 09d
	'531' : 'rain', #Rain	ragged shower rain	 09d
	'600' : 'snowflake', #Snow	light snow	 13d
	'601' : 'snowflake', #Snow	Snow	 13d
	'602' : 'blizzard', #Snow	Heavy snow	 13d
	'611' : 'snowflake', #Snow	Sleet	 13d
	'612' : 'snowflake', #Snow	Light shower sleet	 13d
	'613' : 'snowflake', #Snow	Shower sleet	 13d
	'615' : 'sleet', #Snow	Light rain and snow	 13d
	'616' : 'sleet', #Snow	Rain and snow	 13d
	'620' : 'snowflake', #Snow	Light shower snow	 13d
	'621' : 'snowflake', #Snow	Shower snow	 13d
	'622' : 'blizzard', #Snow	Heavy shower snow	 13d
	'701' : 'sleet', #Mist	mist	 50d
	'711' : 'fog', #Smoke	Smoke	 50d
	'721' : 'fog', #Haze	Haze	 50d
	'731' : 'fog', #Dust	sand/ dust whirls	 50d
	'741' : 'fog', #Fog	fog	 50d
	'751' : 'fog', #Sand	sand	 50d
	'761' : 'fog', #Dust	dust	 50d
	'762' : 'fog', #Ash	volcanic ash	 50d
	'771' : 'wind', #Squall	squalls	 50d
	'781' : 'wind', #Tornado	tornado	 50d
	'800' : 'sun', #Clear	clear sky	 01d 01n
	'801' : 'cloud', #Clouds	few clouds: 11-25%	 02d 02n
	'802' : 'cloudy', #Clouds	scattered clouds: 25-50%	 03d 03n
	'803' : 'cloudy', #Clouds	broken clouds: 51-84%	 04d 04n
	'804' : 'cloudy', #Clouds	overcast clouds: 85-100%	 04d 04n
}

ICON_MAP = {
	'01d' : 'sun',
	'01n' : 'moon',
	'02d' : 'cloudy-day',
	'02n' : 'cloudy-night',
	'03d' : 'cloudy-day',
	'03n' : 'cloudy-night',
	'04d' : 'cloudy-day',
	'04n' : 'cloudy-night'
}

OPEN_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}&units=imperial".format(pzwglobals.LATITUDE, pzwglobals.LONGITUDE, pzwglobals.OPEN_WEATHER_APP_ID)

LOG_DATE_FORMAT = '%Y%m%d%H%M%S'

"""
OpenWeather

	query open weather api for current weather
	store data on public prop weather
"""
class OpenWeather():
	def __init__(self, debug=False):
		self.code_map = CODE_MAP
		self.icon_map = ICON_MAP
		
		try:
			with open(pzwglobals.DATA_DIRECTORY + "openweather.json") as f:
				log = json.load(f)
		except:
			logger.warning("couldn't open log")
			log = {}
	
		if log is not None and "last_load" in log:
			last_load = datetime.strptime(log["last_load"], LOG_DATE_FORMAT)
			now = datetime.now()
			tdiff = now - last_load
		
			logger.debug("time difference: " + last_load.strftime(LOG_DATE_FORMAT) + " - " + now.strftime(LOG_DATE_FORMAT))
			logger.debug(tdiff)
			
			if (tdiff < timedelta(minutes=10) or debug is True):
				logger.info("using logged openweather data")
				self.weather = {
					'code': log["code"],
					'icon': log["icon"],
					#'summary': log["summary"],
					'temperature': log["temperature"],
					'pressure': log["pressure"],
					'humidity': log["humidity"],
					'last_load': log["last_load"]
				}
				return None
				
		self.weather = self.get_weather()
		
		self.weather['last_load'] = datetime.now().strftime(LOG_DATE_FORMAT)

		with open(pzwglobals.DATA_DIRECTORY + "openweather.json", 'w') as f:
			json.dump(self.weather, f)
			
		return None
	"""
	Query Open Weather
	"""
	def get_weather(self):
		weather = {}
		res = requests.get(OPEN_WEATHER_URL)
		if res.status_code == 200:
			
			#text = json.dumps(res.json(), sort_keys=True, indent=4)
			#print(text)
			
			jsondata = res.json()

			weather["code"] = jsondata['weather'][0]['id']
			weather["icon"] = jsondata['weather'][0]['icon']
			#weather["summary"] = jsondata['weather'][0]['main']
			weather["temperature"] = jsondata['main']['temp']
			weather["pressure"] = jsondata['main']['pressure']
			weather["humidity"] = jsondata['main']['humidity']

			return weather
		return {}
