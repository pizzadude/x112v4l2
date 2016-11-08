"""
	Gubbins for interfacing with ffmpeg
"""
import subprocess


def screenshot(screen_id, geometry, filename):
	"""
		Creates a screenshot image from the X screen
		
		`screen_id` should be the full name (including display name)
		of the X11 screen to capture. Eg: ":0.0".
		`geometry` should be a dict-like object providing values
		for x, y, width, and height.
		`filename` is the filesystem location where the
		screenshot will be written.
		
		The return value is a subprocess.Popen instance.
		
		NB. All output of the ffmpeg process is devnull'ed.
	"""
	cmd = [
		'ffmpeg',
		# Input options
		'-f', 'x11grab',
		'-s', '{}x{}'.format(geometry['width'], geometry['height']),
		'-i', '{screen}+{x},{y}'.format(
			screen=screen_id,
			x=geometry['x'],
			y=geometry['y'],
		),
		# Output options
		'-vframes', '1',
		'-y', # Overwrite without asking
		filename,
	]
	return subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	

def capture_window(window, filename):
	"""
		Take a screenshot of the given X `window`
	"""
	return screenshot(
		screen_id=window.screen.full_id,
		geometry=window.get_abs_geometry(),
		filename=filename,
	)
