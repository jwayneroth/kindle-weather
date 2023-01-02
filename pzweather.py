#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import subprocess
from datetime import datetime
import textwrap
import argparse
from PIL import Image, ImageDraw, ImageFont
import pzwglobals

from lib.satelliteimage import SatelliteImage
from lib.noaaforecast import NoaaForecast
from lib.darkskyweather import DarkSkyWeather

logger = pzwglobals.logger

KINDLE_IP = '192.168.2.2'

BLACK = (0,0,0) #1
WHITE = (255, 255, 255) #0
RED = (255, 0, 0) #2

LR_PADDING = 25
TB_PADDING = 45

FONT_SIZE = 80
FONT_SIZE_MEDIUM = 60
FONT_SIZE_SMALL = 50
FONT_Y_OFFSET = 11

ICON_SIZE_SMALL = 160

OUTPUT_FILENAME = 'pz-weather.png'

FONT_LARGE = ImageFont.truetype(pzwglobals.FONT_DIRECTORY + "Impact.ttf", FONT_SIZE)
FONT_MEDIUM = ImageFont.truetype(pzwglobals.FONT_DIRECTORY + "Impact.ttf", FONT_SIZE_MEDIUM)
FONT_SMALL = ImageFont.truetype(pzwglobals.FONT_DIRECTORY + "Impact.ttf", FONT_SIZE_SMALL)

fonts = {
	'large': FONT_LARGE,
	'medium': FONT_MEDIUM,
	'small': FONT_SMALL
}

parser = argparse.ArgumentParser()
parser.add_argument('--debug', '-d', type=str, required=False, choices=['true', 'True', 'false', 'False'], help="run in debug mode") 
parser.add_argument('--icon', '-i', type=str, required=False, choices=['wind', 'sun', 'snowflake', 'sleet', 'rain', 'moon', 'hot', 'hail', 'fog', 'cold', 'cloudy', 'cloudy-night', 'cloudy-day', 'cloud', 'blizzard'], help="force a specific weather icon to display")
parser.add_argument('--dither', '-a', type=str, required=False, choices=['bayer', 'cluster', 'yliluoma'], help="set a dither algorithm for the background")
parser.add_argument('--threshold', '-t', type=int, required=False, choices=[128, 64, 32], help="set the dither algorithm threshold for dithering")
args = parser.parse_args()

"""
helper to exit program in case we need special rpi consideration in future
"""
def kill():
	if pzwglobals.RUN_ON_RASPBERRY_PI:
		sys.exit(0)
	else:
		sys.exit(0)

"""
Create a transparency mask.

	Takes a paletized source image and converts it into a mask
	permitting all the colours supported by Inky pHAT (0, 1, 2)
	or an optional list of allowed colours.

	:param mask: Optional list of Inky pHAT colours to allow.
"""
def create_mask(source, mask=(0, 1)):
	mask_image = Image.new("RGBA", source.size)
	w, h = source.size
	for x in range(w):
		for y in range(h):
			p = source.getpixel((x, y))
			#logger.info('pixel {} {} {}'.format(x,y,p))
			if p in mask:
				mask_image.putpixel((x, y), (0,0,0,255))
			else:
				mask_image.putpixel((x, y), (0,0,0,0))
	return mask_image

"""
render a string onto our surface
	measure width to figure x point if right aligned
	render in white first for ersatz dropshadow, then black

	:param string: text to render
	:param xy: tuple with top and right or left corner
	:param align: optional align left or right
"""
def draw_text(string, xy, font_name, align="left"):
	over = 4 if font_name is 'small' else 6
	font = fonts[font_name]
	x,y = xy
	if align is "right":
		w,h = draw.textsize(string, font=font)
		x = x - w
	cx = x
	for c in string:
		draw.text((cx-over,y-over), c, WHITE, font=font)
		draw.text((cx,y-over), c, WHITE, font=font)
		draw.text((cx+over,y-over), c, WHITE, font=font)
		draw.text((cx-over,y), c, WHITE, font=font)
		draw.text((cx+over,y), c, WHITE, font=font)
		draw.text((cx-over,y+over), c, WHITE, font=font)
		draw.text((cx,y+over), c, WHITE, font=font)
		draw.text((cx+over,y+over), c, WHITE, font=font)
		cw = draw.textsize(c, font=font)[0]
		cx = cx + cw
	cx = x
	for c in string:
		draw.text((cx,y), c, BLACK, font=font)
		cw = draw.textsize(c, font=font)[0]
		cx = cx + cw

"""
main
"""
if __name__ == '__main__':
	logger.info('pizero weather started at ' + datetime.now().strftime("%m/%d/%Y %I:%M %p"))
	
	debug = False
	if args.debug is 'true' or args.debug is 'True':
		debug = True
	
	now = datetime.now()
	
	bg = SatelliteImage(args.dither, args.threshold, debug=debug).image
	
	noaa = NoaaForecast(debug=debug)
	forecast = noaa.forecast
	logger.debug(forecast)
	
	"""
	darksky = DarkSkyWeather(debug=debug)
	current = darksky.weather
	logger.debug(current)
	"""
	
	draw = ImageDraw.Draw(bg)
	
	# print today's day, time, current temp and humidity
	day = now.strftime("%A")
	if day == "Wednesday":
		day = "Wed"
	
	date = now.strftime("%m/%d")
	if date[0] is "0":
		date = date[1:]
	
	time = now.strftime("%I:%M %p")
	if time[0] is "0":
		time = time[1:]
	
	draw_text(day, (LR_PADDING, 10), 'medium')
	draw_text(date, (LR_PADDING, TB_PADDING - FONT_Y_OFFSET + 40), 'large')
	draw_text(time, (pzwglobals.DISPLAY_WIDTH - LR_PADDING - 2, TB_PADDING - FONT_Y_OFFSET + 10), 'large', align="right")

	"""
	if current is not None:
		if "temperature" in current:
			temp_str = u"{}°".format(current["temperature"])
			mid_y = TB_PADDING + int((pzwglobals.DISPLAY_HEIGHT - TB_PADDING) / 4.75) - int(draw.textsize(temp_str, font=FONT_LARGE)[1] / 2) - int(FONT_Y_OFFSET / 2)
			draw_text(temp_str, (pzwglobals.DISPLAY_WIDTH - LR_PADDING - 12, mid_y), 'large', align="right")

		if "humidity" in current:
			bottom_y = TB_PADDING + int((pzwglobals.DISPLAY_HEIGHT - TB_PADDING) / 2.375) - draw.textsize(temp_str, font=FONT_LARGE)[1] - FONT_Y_OFFSET
			draw_text("{} %".format(current["humidity"]), (pzwglobals.DISPLAY_WIDTH - LR_PADDING, bottom_y), 'large', align="right")
	"""
	
	# print today's icon
	# we have some noaa icons that take precedence for display
	# otherwise we use our map of darksky icon summaries to our icon images
	# with a fallback noaa icon map
	
	icon_name = None
	
	#check if user forced an icon via command line arg
	if args.icon is not None:
		icon_name = args.icon

	#else determine icon based on our data
	else:

		#if we have a noaa icon for today, we check it first for priority images
		noaa_icon = forecast["icons"][0]
		
		if noaa_icon is not None:
			if noaa_icon in noaa.priority_icons:
				icon_name = noaa.icon_map[noaa_icon]
			
		#no priority icon, use the darksky summary icon
		"""
		if icon_name is None:
			if "summary" in current:
				if current["summary"] in darksky.icon_map:
					icon_name = darksky.icon_map[current["summary"]]
		"""
		
		#something went wrong with darksky, use any noaa icon
		if icon_name is None and noaa_icon is not None:
			if noaa_icon in noaa.icon_map:
				icon_name = noaa.icon_map[noaa_icon]
	
	#if we determined an icon, try to load it
	if icon_name is not None:
		try:
			icon = pzwglobals.IMG_DIRECTORY + "icons/" + icon_name + ".png"
			icon_img = Image.open(icon)
			mask = create_mask(icon_img)
			bg.paste(icon_img, (LR_PADDING, 175), mask)
		except:
			pass
	
	# print day, high and low, and icon for our forecast days
	rx = LR_PADDING
	ry = TB_PADDING + int(pzwglobals.DISPLAY_HEIGHT / 2)
	col_width = int((pzwglobals.DISPLAY_WIDTH - LR_PADDING * 2) / 3)
	line_height = FONT_SIZE_SMALL + 10
	
	for i in range(1,4):
		draw_text(forecast["date_names"][i], (rx, ry), 'medium', align="left")
		draw_text("{}° - {}°".format(forecast["temps"][1][i], forecast["temps"][0][i]), (rx, ry + line_height + 10), 'small', align="left")
		
		if forecast["icons"][i] is not None and forecast["icons"][i] in noaa.icon_map:
			icon = pzwglobals.IMG_DIRECTORY + "icons/" + noaa.icon_map[forecast["icons"][i]] + ".png"
			icon_img = Image.open(icon)
			mask = create_mask(icon_img)
			icon_img.thumbnail((ICON_SIZE_SMALL, ICON_SIZE_SMALL))
			mask.thumbnail((ICON_SIZE_SMALL, ICON_SIZE_SMALL))
			bg.paste(icon_img, (rx, ry + line_height * 2 + 20), mask)
		else:
			summary_text = forecast["summaries"][i]
			summary_lines = textwrap.wrap(summary_text, width=9)
			summary_y = ry + line_height * 3 + 20
			for s_line in summary_lines:
				s_lineh = draw.textsize(s_line, font=FONT_SMALL)[1]
				draw_text(s_line, (rx, summary_y), 'small', align="left")
				summary_y = summary_y + s_lineh
		
		rx = rx + col_width

	bg = bg.convert('L')
	bg.save( pzwglobals.IMG_DIRECTORY + OUTPUT_FILENAME)
	
	if pzwglobals.RUN_ON_RASPBERRY_PI:
		try:
			#http://pi.hole/weather/pz-weather.png
			cp = 'cp {} /var/www/html/weather/{}'.format(pzwglobals.IMG_DIRECTORY + OUTPUT_FILENAME, OUTPUT_FILENAME)
			logger.debug('cp command: {}'.format(cp))
			subprocess.Popen(cp, shell=True, stdout=subprocess.PIPE)
		except:
			logger.warning("could not copy weather image to server")
		"""
		try:
			scp = 'scp -i ~/.ssh/id_rsa {} root@{}:/mnt/us/weather/{}'.format(pzwglobals.IMG_DIRECTORY + OUTPUT_FILENAME, KINDLE_IP, OUTPUT_FILENAME)
			logger.debug('scp command: {}'.format(scp))
			subprocess.Popen(scp, shell=True, stdout=subprocess.PIPE)
		except:
			logger.warning("could not upload weather image to kindle")
		"""
	kill()






