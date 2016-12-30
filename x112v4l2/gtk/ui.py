"""
	Functionality for handling the UI elements
"""
import os
from concurrent import futures

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from x112v4l2 import v4l2
from x112v4l2.gtk import utils


class MainUI(object):
	"""
		General wrapper around all the main window functionality
	"""
	main_glade = os.path.join(os.path.dirname(__file__), 'main.glade')
	device_glade = os.path.join(os.path.dirname(__file__), 'device.glade')
	
	STATE_RELOADING = 'reloading'
	MAX_WORKERS = 2
	
	# Icons
	ICON_RELOAD = 'gtk-refresh'
	ICON_YES = 'gtk-yes'
	ICON_NO = 'gtk-no'
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.executor = futures.ProcessPoolExecutor(max_workers=self.MAX_WORKERS)
		
		self.load_main_window()
		self.add_device('/dev/video666', 'Gateway to Hell')
		
	def run(self):
		self.main_window.show_all()
		Gtk.main()
		
	def load_main_window(self):
		"""
			Loads the main window UI from file
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.main_glade)
		builder.connect_signals(SignalHandler(ui=self))
		# We want the main window
		self.main_window = builder.get_object('main')
		# We also want the device-tab widget
		self.device_list = builder.get_object('device_list')
		
		# Finally, clean up the template/demo widgets we don't need
		self.clear_devices()
		
	
	def get_widget(self, name):
		"""
			Return the `name`d widget, or none
		"""
		return utils.find_child_by_id(self.main_window, name)
		
	
	def clear_devices(self):
		"""
			Removes all device configuration tabs from the main UI
		"""
		self.device_list.set_current_page(0)
		for idx in range(0, self.device_list.get_n_pages() - 1):
			self.device_list.remove_page(-1)
		
	def load_device_config(self):
		"""
			Loads the device configuration UI from file
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.device_glade)
		config = builder.get_object('device_config')
		return config
		
	def add_device(self, path, label):
		"""
			Adds a device to the main UI
		"""
		# Use the first tab's label as a template for the new one
		first_page = self.device_list.get_nth_page(0)
		first_label = self.device_list.get_tab_label(first_page)
		
		page = self.load_device_config()
		tab_label = Gtk.Label('{}\n{}'.format(label, path))
		# There's no way to completely copy widget style,
		# and label justification can't be set through CSS,
		# so we manually make sure the justification is consistent.
		tab_label.set_justify(first_label.get_justify())
		
		self.device_list.append_page(page, tab_label)
		
		return page
		
	
	def show_v4l2_available(self, state):
		"""
			Update indicators of v4l2 availability
		"""
		mod_avail_widget = self.get_widget('v4l2_module_available_indicator')
		if state == self.STATE_RELOADING:
			icon = self.ICON_RELOAD
		else:
			icon = self.ICON_YES if state else self.ICON_NO
		mod_avail_widget.set_from_icon_name(icon, Gtk.IconSize.BUTTON)
		
	def show_v4l2_loaded(self, state):
		"""
			Update indicators of v4l2 loadedness
		"""
		mod_loaded_widget = self.get_widget('v4l2_module_loaded_indicator')
		if state == self.STATE_RELOADING:
			icon = self.ICON_RELOAD
		else:
			icon = self.ICON_YES if state else self.ICON_NO
		mod_loaded_widget.set_from_icon_name(icon, Gtk.IconSize.BUTTON)
		
	def show_v4l2_devices(self, devices):
		"""
			Update indicators of v4l2 devices
		"""
		# Update the summary's total device count
		num_devices_widget = self.get_widget('v4l2_num_devices')
		if devices == self.STATE_RELOADING:
			num_devices_widget.set_label('???')
			devices = []
		else:
			num_devices_widget.set_label(str(len(list(devices))))
		
		# Populate the list of device names
		device_names_widget = self.get_widget('v4l2_device_names')
		buff = device_names_widget.get_buffer()
		buff.set_text('\n'.join(dev['label'] for dev in devices))
		
	
class SignalHandler(object):
	"""
		Handle all the signals
	"""
	def __init__(self, ui, **kwargs):
		"""
			Create a new SignalHandler
			
			The `ui` parameter should be an instance of a MainUI class.
		"""
		super().__init__(**kwargs)
		self.ui = ui
		
	
	def exit_application(self, widget, data):
		return Gtk.main_quit(widget, data)
		
	
	def refresh_v4l2_info(self, widget, data=None):
		"""
			Rechecks the state of the v4l2loopback kernel module
		"""
		# Indicate that stuff is reloading
		self.ui.show_v4l2_available(self.ui.STATE_RELOADING)
		self.ui.show_v4l2_loaded(self.ui.STATE_RELOADING)
		self.ui.show_v4l2_devices(self.ui.STATE_RELOADING)
		
		# Async info-getting
		avail_future = self.ui.executor.submit(v4l2.get_module_available)
		avail_future.add_done_callback(
			lambda f: self.ui.show_v4l2_available(f.result())
		)
		
		loaded_future = self.ui.executor.submit(v4l2.get_module_loaded)
		loaded_future.add_done_callback(
			lambda f: self.ui.show_v4l2_loaded(f.result())
		)
		
		devices_future = self.ui.executor.submit(v4l2.get_devices)
		devices_future.add_done_callback(
			lambda f: self.ui.show_v4l2_devices(f.result())
		)
		
	
