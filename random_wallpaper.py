import pystray, requests, random, os, sys, ctypes, json
from PIL import Image, ImageFile
from bs4 import BeautifulSoup as BS

from _helpers import resource_path, do_alert

WALLPAPERCAVE_HOST = "https://wallpapercave.com"

RANDOM_WALLPAPER_SESSION_HEADERS = {
	"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
	"Accept-Encoding" : "gzip",
	"Accept-Language" : "en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,tk-TM;q=0.6,tk;q=0.5",
	"Cache-Control" : "max-age=0",
	"Content-Type" : "",
	"Dnt" : "1",
	"Referer" : "https://www.google.com",
	"Sec-Ch-Ua" : '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
	"Sec-Ch-Ua-Mobile": '?0',
	"Sec-Ch-Ua-Platform": '"Windows"',
	"Sec-Fetch-Dest" : "document",
	"Sec-Fetch-Mode" : "navigate",
	"Sec-Fetch-Site" : "cross-site",
	"Sec-Fetch-User" : "?1",
	"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
	"Upgrade-Insecure-Requests" : "1",
}

class RandomWall:
	object_name = "Random Wallpaper"
	icon_name = "icon.png"

	config_path = "./config.json"
	config = {
		"last_wallpaper" : None,
		"only_landscape_wallpapers" : False,
		"only_fhd" : False
	}

	# min resolution for considering image as Full HD
	full_hd_min = (1920, 1080)

	def __init__(self, categories = [], download_folder = "wallpapers", image_upscaler_object = None):
		print("[Init] Starting...")
		self.session = requests.Session()
		self.session.headers = RANDOM_WALLPAPER_SESSION_HEADERS
		self.session.get(WALLPAPERCAVE_HOST) # get cookies
		print("[Session] Cookies:", self.session.cookies)
		print("[Session] Got cookies")

		self.categories = categories
		print("[Categories]", self.categories)

		self.download_folder = download_folder
		print("[DownloadFolder]", self.download_folder)

		self.image_upscaler = image_upscaler_object
		if self.image_upscaler:
			if self.image_upscaler.is_ready():
				self.image_upscaler.set_download_folder(self.download_folder)
				print("[ImageUpscaler] Ready")
			else:
				print("[ImageUpscaler] Not Ready")
		else:
			print("[ImageUpscaler] Not Available")

		if not os.path.isdir(self.download_folder):
			try:
				os.mkdir(self.download_folder)
			except:
				pass

		if not self.categories:
			self.categories = self.parse_categories()

		self.image = Image.open(resource_path(self.icon_name))

		self.icon = pystray.Icon("random_wallpaper", self.image, self.object_name, menu = self.menu_items())

		self.load_config()
		print("[Init] Done!")

	def __menu_items(self):
		yield pystray.MenuItem("Set Random Wallpaper ", self.set_random_wallpaper, default = True)
		yield pystray.MenuItem("Categories", pystray.Menu(*self.create_menu_items_from_categories()))

		if self.image_upscaler:
			if self.image_upscaler.is_ready():
				yield pystray.MenuItem("2x Upscale Current Wallpaper", self.upscale_current_wallpaper)

		yield pystray.MenuItem("Only Landscape Wallpapers", self.toggle_16_9, checked = lambda _ : self.config["only_landscape_wallpapers"])
		yield pystray.MenuItem("Only Full HD Wallpapers", self.toggle_min_fhd, checked = lambda _ : self.config["only_fhd"])

		yield pystray.Menu.SEPARATOR
		yield pystray.MenuItem("Exit", self.stop)

	def menu_items(self):
		return (item for item in self.__menu_items())

	def icon_update_menu(self):
		self.icon.menu = pystray.Menu(*self.menu_items())

	def run(self):
		self.icon.run()

	def stop(self, icon, _):
		self.icon.stop()

	def create_menu_items_from_categories(self):
		return (pystray.MenuItem(cat.title(), self.set_random_wallpaper) for cat in self.categories)

	def save_config(self):
		with open(self.config_path, "w", encoding = "utf-8") as file:
			json.dump(self.config, file, indent = 4)

	def load_config(self):
		if not os.path.isfile(self.config_path):
			return

		try:
			with open(self.config_path, "r", encoding = "utf-8") as file:
				self.config = json.loads(file.read())
		except:
			return

	def toggle_16_9(self):
		self.config["only_landscape_wallpapers"] = not self.config["only_landscape_wallpapers"]
		self.save_config()

	def toggle_min_fhd(self):
		self.config["only_fhd"] = not self.config["only_fhd"]
		self.save_config()

	def upscale_image(self, image_path):
		new_image_path = self.image_upscaler.upscale(image_path)

		if new_image_path != None:
			new_image_path = os.path.abspath(new_image_path)

		return new_image_path

	def get_image_resolution(self, image_url):
		image = self.session.get(image_url, stream = True)
		p = ImageFile.Parser()
		for chunk in image.iter_content(chunk_size = 1024):
			p.feed(chunk)
			if p.image:
				return p.image.size
			break
		return None, None

	def download_wallpaper(self, url):
		image_width, image_height = self.get_image_resolution(url)
		image = self.session.get(url, stream = True)
		image_name = image.headers["Content-Disposition"]
		image_name = image_name[image_name.find("filename") + 10:-1]

		image_path = os.path.join(self.download_folder, image_name)

		if self.config["only_landscape_wallpapers"]:
			if image_width == image_height == None:
				print("Couldn't get image resolution, skipping")
				return -1

			if (16 / 10) < (image_width / image_height) < (19 / 9):
				print("Skipping image as it is not wide")
				return -1

		if self.config["only_fhd"]:
			fhdmin = self.full_hd_min
			
			if image_width < image_height:
				if fhdmin[0] > fhdmin[1]:
					fhdmin = fhdmin[1], fhdmin[0]

			if image_width < fhdmin[0] or image_height < fhdmin[1]:
				print("Skipping image as it doesn't stisfy min FHD resolution")
				return -1


		# don't download file if it exists in download_folder
		if not (os.path.isfile(image_path)):
			with open(image_path, "wb") as file:
				for chunk in image.iter_content(chunk_size = 8192):
					file.write(chunk)

		return os.path.abspath(image_path)

	def parse_categories(self):
		return ["anime"] # temporary

	def get_random_category(self):
		return WALLPAPERCAVE_HOST + "/categories/" + random.choice(self.categories)

	def get_random_theme_in_category(self, cat):
		response = self.session.get(cat)

		soup = BS(response.text, "lxml")
		themes = soup.find_all(class_ = ("albumthumbnail", "even"))

		random_theme = random.choice(themes).get("href")

		return WALLPAPERCAVE_HOST + random_theme

	def get_random_wallpaper_in_theme(self, theme):
		response = self.session.get(theme)

		soup = BS(response.text, "lxml")
		urls = soup.find_all("a", class_ = "download")

		random_url = random.choice(urls).get("href")

		return WALLPAPERCAVE_HOST + random_url

	def get_random_wallpaper(self, cat = None):
		if cat is None:
			cat = self.get_random_category()
		theme = self.get_random_theme_in_category(cat)
		wallpaper = self.get_random_wallpaper_in_theme(theme)
		wallpaper_path = self.download_wallpaper(wallpaper)

		return [wallpaper_path, wallpaper]

	def set_random_wallpaper(self, icon = None, query = None):
		self.icon.title = "Searching for Random Wallpaper"
		cat = ""

		try:
			if query:
				cat = str(query).strip().lower()
				if cat != "set random wallpaper":
					cat = WALLPAPERCAVE_HOST + "/categories/" + cat
				else:
					cat = None

			retries = 5
			wallpaper_path = None
			wallpaper = None

			while retries:
				try:
					wallpaper_path, wallpaper = self.get_random_wallpaper(cat)
					retries = 0
				except Exception as e:
					print(e)
					retries -= 1
					self.icon.title = str(5 - retries) + ": Exception occured. Trying again..."

			if wallpaper_path is None:
				raise ValueError("Couldn't download wallpaper. Please check your Network connection! Retry?")
			elif wallpaper_path == -1:
				self.set_random_wallpaper(icon, query)
				return

			self.set_wallpaper(wallpaper_path)

		except Exception as e:
			print(e)

			if do_alert("Error", str(e), 5) == 4:
				self.set_random_wallpaper(icon, query)

		self.icon.title = self.object_name

	def set_last_wallpaper(self):
		last_wallpaper = self.config["last_wallpaper"]

		if not last_wallpaper:
			return

		if not os.path.isfile(last_wallpaper):
			return

		self.set_wallpaper(last_wallpaper)

	def set_wallpaper(self, wallpaper_path):
		ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 0)
		self.config["last_wallpaper"] = wallpaper_path
		self.save_config()
		print("Set wallpaper: " + os.path.split(wallpaper_path)[-1])

	def upscale_current_wallpaper(self):
		if not self.image_upscaler.is_ready():
			print("Image Upscaler is not ready")
			return

		if self.config["last_wallpaper"] is None:
			print("Config doesn't have :last_wallpaper: property")
			return

		self.icon.title = "Upscaling Wallpaper..."

		image_path = self.config["last_wallpaper"]
		upscaled_image_path = self.upscale_image(image_path)
		if upscaled_image_path != None:
			self.set_wallpaper(upscaled_image_path)
		else:
			print(":upscaled_image_path: is NoneType. Couldn't upscale.")

		self.icon.title = self.object_name
