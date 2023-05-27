import os, sys
from random_wallpaper import RandomWall
# from image_upscaler import ImageUpscaler

def main():
	# Check if file is a script or frozen executable
	application_path = None
	if getattr(sys, 'frozen', False):
		application_path = os.path.dirname(sys.executable)
	elif __file__:
		application_path = os.path.dirname(__file__)

	# Change current working directory to application path (required)
	os.chdir(application_path)

	random_wall = RandomWall(categories = [
		"animals", "anime",
		"brands",
		"cars", "cartoons",	"celebrities",
		"devices",
		"fortnite",
		"games", "geography",
		"holidays",
		"motor", "movies", "music",
		"nature",
		"other",
		"pokemon",
		"religion", "resolutions",
		"space", "sports", "superheroes",
		"tv-shows"
	])

	try:
		random_wall.set_last_wallpaper()
	except Exception as e:
		print(e) # idk why there will be an error, but it is just in case

	random_wall.run()

if __name__ == "__main__":
	main()