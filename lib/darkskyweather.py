import requests
from bs4 import BeautifulSoup
import pzwglobals

logger = pzwglobals.logger

DARK_SKY_URL = "https://darksky.net/forecast/{}/us12/en".format(",".join([pzwglobals.LATITUDE, pzwglobals.LONGITUDE]))

"""
DarkSkyWeather

	lightly adapted from InkyPhat example script
	scrape darksky for temp, pressure and humidity
	store data on public prop weather
"""
class DarkSkyWeather():
	def __init__(self):
		self.weather = self.get_weather()

	"""
	Query Dark Sky (https://darksky.net/) to scrape current weather data
	"""
	def get_weather(self):
		weather = {}
		res = requests.get(DARK_SKY_URL)
		if res.status_code == 200:
			soup = BeautifulSoup(res.content, "lxml")
			curr = soup.find_all("span", "currently")
			weather["summary"] = curr[0].img["alt"].split()[0]
			weather["temperature"] = int(curr[0].find("span", "summary").text.split()[0][:-1])
			press = soup.find_all("div", "pressure")
			weather["pressure"] = int(press[0].find("span", "num").text)
			hum = soup.find_all("div", "humidity")
			weather["humidity"] = int(hum[0].find("span", "num").text)
			return weather
		return None
