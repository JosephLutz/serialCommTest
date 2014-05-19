# serial_settings_test - A placeholder for the module on the OrionLXm
import unittest
import sys
import os

if __name__ == '__main__':
	importDirectory = os.getcwd()
	while os.path.basename(importDirectory) in ['tests', 'OrionPythonModules']:
		importDirectory = os.path.dirname(importDirectory)
	sys.path = [importDirectory] + sys.path

from OrionPythonModules import serial_settings


class TestSerialSettings(unittest.TestCase):
	def test_object_creation(self):
		settings = serial_settings.SerialSettings()
		self.assertTrue(isinstance(settings, serial_settings.SerialSettings))

	def test_apply(self):
		settings = serial_settings.SerialSettings()
		settings.apply()


def runtests():
	unittest.main()


if __name__ == '__main__':
	runtests()
