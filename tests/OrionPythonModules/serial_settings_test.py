# serial_settings_test - A placeholder for the module on the OrionLXm
import unittest

if __name__ == '__main__':
	import os, sys
	importDirectory = os.getcwd()
	while os.path.basename(importDirectory) in ['tests', 'OrionPythonModules']:
		importDirectory = os.path.dirname(importDirectory)
	sys.path = [importDirectory] + sys.path

from OrionPythonModules import serial_settings

class TestMsgMonitor(unittest.TestCase):
	def setUp(self):
		pass
	def test_ObjectCreation(self):
		settings = serial_settings.SerialSettings()
		self.assertTrue(isinstance(settings, serial_settings.SerialSettings))
	def test_apply(self):
		settings = serial_settings.SerialSettings()
		settings.apply()

def runtests():
	unittest.main()
if __name__ == '__main__':
	runtests()
