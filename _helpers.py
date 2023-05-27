import os, ctypes, sys

# Need for avoiding problems with pyinstaller and normal python
def resource_path(file_path):
	base_path = None
	try:
		base_path = sys._MEIPASS
	except:
		base_path = os.path.abspath('.')

	return os.path.join(base_path, file_path)

def do_alert(title, text, style):
	##  Styles:
	##  0 : OK
	##  1 : OK | Cancel
	##  2 : Abort | Retry | Ignore
	##  3 : Yes | No | Cancel
	##  4 : Yes | No
	##  5 : Retry | Cancel
	##  6 : Cancel | Try Again | Continue

	return ctypes.windll.user32.MessageBoxW(0, text, title, style)