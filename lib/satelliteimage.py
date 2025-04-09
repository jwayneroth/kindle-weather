import os
import time
import re
from urllib.request import urlretrieve
import requests
from xml.dom import minidom
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import hitherdither
import pzwglobals

DEFAULT_BG = pzwglobals.IMG_DIRECTORY + 'default-bg.png'

DEFAULT_DITHER_ALGORITHM = 'bayer' #'yliluoma'
DEFAULT_DITHER_THRESHOLD = 64

NOAA_IMG_URL = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/ne/GEOCOLOR/"

CROP_LEFT = 340 #254
CROP_TOP = 160
BG_WIDTH = 600
BG_HEIGHT = 800

logger = pzwglobals.logger

palette = hitherdither.palette.Palette(
	[0xffffff, 0x000000]
)

"""
SatelliteImage

	attempt to download latest NOAA satellite image
	crop and dither it for Inky display
	store new image or local default on public prop image
"""
class SatelliteImage():
	def __init__(self, dither, threshold, debug=False):
		
		if debug is True:
			self.image = self.getDefault()
			return None
		
		if dither is None:
			dither = DEFAULT_DITHER_ALGORITHM
		if threshold is None:
			threshold = DEFAULT_DITHER_THRESHOLD
		
		self.dither = dither
		self.threshold = threshold
		
		logger.debug("SatelliteImage init with dither: {} at {}".format(self.dither, self.threshold))
		
		url = self.getLatestImageUrl()
		
		if not url:
			self.image = self.getDefault()
			return None
		
		img = self.downloadLatest(url)
		
		if not img:
			self.image = self.getDefault()
			return None
		
		crop = self.cropTriState(img)
		
		#self.image = self.pillowIndex(crop)
		
		#self.image = self.diffusionDither(crop)
		
		self.image = crop #self.ditheredIndex(crop)
		
		return None

	"""
	 find latest 1200 x 1200 satellite image on server
	"""
	def getLatestImageUrl(self):
		try:
			res = requests.get(NOAA_IMG_URL)
			if res.status_code == 200:
				soup = BeautifulSoup(res.content, 'html.parser')
				img_urls = soup.find_all('a', string=re.compile("1200x1200"))
				if not img_urls:
					logger.warning('Error: no image urls found')
					return None
				logger.debug('latest image anchor: ')
				logger.debug(img_urls[-1])
				return NOAA_IMG_URL + img_urls[-1]['href']
		except:
			pass
		return None
	
	"""
	 download latest satellite image
	"""
	def downloadLatest(self, url):
		sat_img_localname = "noaa-download" + time.strftime("%Y%m%d%H%M") + ".jpg"
		try:
			sat_img_local, headers = urlretrieve(url, sat_img_localname)
			img = Image.open(sat_img_local)
			os.remove(sat_img_local)
			return img
		except:
			return None
	
	"""
	 crop nyc area from satellite image
	"""
	def cropTriState(self, img):
		return img.crop((CROP_LEFT, CROP_TOP, CROP_LEFT + BG_WIDTH, CROP_TOP + BG_HEIGHT))

	"""
	 convert rgb image to 3 color indexed image using Pil quantize with custom palette
	"""
	def pillowIndex(self, img):
		img = img.crop((CROP_LEFT, CROP_TOP, CROP_LEFT + BG_WIDTH, CROP_TOP + BG_HEIGHT))
		idx_img = Image.new("P", (1, 1))
		idx_img.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)
		img2 = img.quantize(palette=idx_img)
		return img2

	"""
	 convert rgb image to 3 color indexed image
	 with custom dithering via hitherdither library
	"""
	def ditheredIndex(self, img):
		
		#Yliluoma's Algorithm 1
		if self.dither is 'yliluoma':
			img_dithered = hitherdither.ordered.yliluoma.yliluomas_1_ordered_dithering(img, palette, order=8)
		
		#Bayer dithering
		elif self.dither is 'bayer':
			threshold = self.threshold
			img_dithered = hitherdither.ordered.bayer.bayer_dithering(img, palette, [threshold, threshold, threshold], order=8)
		
		#Cluster dot
		else:
			threshold = self.threshold
			img_dithered = hitherdither.ordered.cluster.cluster_dot_dithering(img, palette, [threshold, threshold, threshold], order=8)
		
		return img_dithered
	
	"""
	 do dither using one of hitherdither's diffusion dither algorithms
	"""
	def diffusionDither(self, img):
		return hitherdither.diffusion.error_diffusion_dithering(img, palette, method='stevenson-arce')
		
	"""
	 use default satellite background
	"""
	def getDefault(self):
		return Image.open(DEFAULT_BG)
