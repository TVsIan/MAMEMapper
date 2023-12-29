import sys
import getopt
import os
import subprocess
import platform
import configparser
import json
import xmltodict
import fnmatch
import codecs
import fileinput
from xml.dom import minidom
from copy import deepcopy
from datetime import datetime
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QDialog, QMessageBox, QTabWidget, QComboBox, QListWidget, QListWidgetItem, QPushButton,
	QProgressDialog, QLabel, QFileDialog, QGroupBox, QRadioButton, QCheckBox, QLineEdit, QTreeWidget, QWidget, QLineEdit,
)
from PyQt6.uic import loadUi

class mainWindow(QMainWindow):
	def __init__(self):
		global selectedController
		global isLoading

		# Initialize GUI
		super(mainWindow, self).__init__()
		loadUi(f'{scriptDir}{os.path.sep}ui{os.path.sep}MainWindow.ui', self)
		self.setWindowIcon(QIcon(f'{scriptDir}{os.path.sep}ui{os.path.sep}icon.png'))
		self.connectSignalsSlots()
		self.setFixedSize(591,361)

		# If saved MAME folder exists, set label
		if mameDir != '' and os.path.isdir(mameDir):
			self.pathLabel.setText(mameDir)

		# Fill in lists
		isLoading = True
		for controller in controllerTypes.keys():
			self.controllerType.addItem(controller)
		for mappingType in mappingTypes.keys():
			item = QListWidgetItem(mappingType)
			item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
			if mappingType in applyMappings:
				item.setCheckState(Qt.CheckState.Checked)
			else:
				item.setCheckState(Qt.CheckState.Unchecked)
			self.mappingsList.addItem(item)
		isLoading = False

		# Set controller type to the saved if it exists, Xinput if not.
		if selectedController not in controllerTypes.keys():
			selectedController = 'Xinput (Xbox Style)'
		selectedIndex = self.controllerType.findText(selectedController)
		if selectedIndex > -1:
			self.controllerType.setCurrentIndex(selectedIndex)

		isLoading = True
		# Set other options to match saved values
		for check in range(0, 4):
			self.pCheck[check].setChecked(playerChecks[check])
		match buttonLayout:
			case 'NES':
				self.layoutRadio[0].setChecked(True)
			case 'SNES':
				self.layoutRadio[1].setChecked(True)
			case _:
				self.layoutRadio[1].setChecked(True)
		self.primaryCheck.setChecked(swapPrimary)
		self.singleCheck.setChecked(singleButton)
		self.hotkeyCheck.setChecked(hotkeyMode)
		self.leftRadio[leftStickMode - 1].setChecked(True)
		if self.leftRadio[3].isChecked():
			self.rightStickGroup.setEnabled(False)
		else:
			self.rightStickGroup.setEnabled(True)
		self.rightRadio[rightStickMode - 1].setChecked(True)
		self.remap4pCheck.setChecked(remap4p)
		self.cloneCheck.setChecked(parentOnly)
		self.ctrlrCheck.setChecked(makeCtrlr)
		self.iniCheck.setChecked(addToINI)
		self.mapDevicesCheck.setChecked(mapDevices)
		self.saveDefaultCheck.setChecked(saveDefault)
		self.devButtonCheck.setChecked(devButtons)
		self.analogCheck.setChecked(digitalAnalog)
		self.neogeoCheck.setChecked(neogeo)
		if 'Neo Geo' in applyMappings:
			self.neogeoCheck.setEnabled(True)
		else:
			self.neogeoCheck.setEnabled(False)

		# Conditional controls
		if self.pCheck[0].isChecked():
			self.hotkeyCheck.setEnabled(True)
		else:
			self.hotkeyCheck.setEnabled(False)

		if self.pCheck[0].isEnabled() and self.pCheck[1].isChecked():
			self.rightRadio[3].setEnabled(True)
		else:
			self.rightRadio[3].setEnabled(False)

		if (self.pCheck[0].isEnabled() and self.pCheck[1].isChecked() and
			self.pCheck[2].isEnabled() and self.pCheck[3].isChecked()):
			self.leftRadio[3].setEnabled(True)
			self.remap4pCheck.setEnabled(True)
		else:
			self.leftRadio[3].setEnabled(False)
			self.remap4pCheck.setEnabled(False)
		isLoading = False

		self.fillDeviceList()
		self.fillFixedDeviceList()

		self.runButton.setEnabled(canWeRun(self))
		self.previewTab.setEnabled(canWeRun(self))
		self.mapDevicesCheck.setEnabled(makeCtrlr)
		self.iniCheck.setEnabled(makeCtrlr)
		if makeCtrlr and mapDevices:
			self.deviceTab.setEnabled(True)
		else:
			self.deviceTab.setEnabled(False)

		bgfxChains = ['default', 'unfiltered', 'hlsl', 'crt-geom', 'crt-geom-deluxe', 'lcd-grid']
		bgfxBackends = ['auto', 'opengl', 'gles']
		if platform.system() == 'Windows':
			bgfxBackends.extend(['d3d9', 'd3d11', 'd3d12', 'vulkan'])
		elif platform.system() == 'Darwin':
			bgfxBackends.append('metal')
		else:
			bgfxBackends.append('vulkan')
		videoModes = ['auto', 'bgfx', 'opengl', 'gdi']
		if platform.system() == 'Windows':
			videoModes.append('d3d')

		self.videoCombo.addItems(videoModes)
		self.bgfxCombo.addItems(bgfxBackends)
		self.chainsCombo.addItems(bgfxChains)
		self.lcdChainsCombo.addItems(bgfxChains)
		self.svgChainsCombo.addItems(bgfxChains)
		self.mixedScreensCheck.setChecked(mixedScreens)

	def connectSignalsSlots(self):
		self.pCheck = []
		self.layoutRadio = []
		self.hotkeysRadio = []
		self.leftRadio = []
		self.rightRadio = []

		# Connect controls to variables & functions
		self.exitButton = self.findChild(QPushButton, 'exitButton')
		self.exitButton.clicked.connect(self.closeApp)
		self.runButton = self.findChild(QPushButton, 'runButton')
		self.runButton.clicked.connect(self.runGeneration)
		self.loadButton = self.findChild(QPushButton, 'loadButton')
		self.loadButton.clicked.connect(self.loadCustom)
		self.deleteButton.clicked.connect(self.deleteCustom)
		self.deleteButton = self.findChild(QPushButton, 'deleteButton')
		self.deleteButton.clicked.connect(self.deleteCustom)
		self.mameButton = self.findChild(QPushButton, 'mameButton')
		self.mameButton.clicked.connect(self.locateMAME)
		self.pathLabel = self.findChild(QLabel, 'pathLabel')
		self.tabStrip = self.findChild(QTabWidget, 'tabStrip')
		self.tabStrip.currentChanged.connect(self.tabChanged)
		self.controllerType = self.findChild(QComboBox, 'controllerType')
		self.controllerType.currentIndexChanged.connect(self.controllerChange)
		self.controllerPic = self.findChild(QLabel, 'controllerPic')
		self.pCheck.insert(0, self.findChild(QCheckBox, 'p1Check'))
		self.pCheck.insert(1, self.findChild(QCheckBox, 'p2Check'))
		self.pCheck.insert(2, self.findChild(QCheckBox, 'p3Check'))
		self.pCheck.insert(3, self.findChild(QCheckBox, 'p4Check'))
		self.pCheck[0].toggled.connect(self.pToggle)
		self.pCheck[1].toggled.connect(self.pToggle)
		self.pCheck[2].toggled.connect(self.pToggle)
		self.pCheck[3].toggled.connect(self.pToggle)
		self.layoutRadio.insert(0, self.findChild(QRadioButton, 'layoutRadio0'))
		self.layoutRadio.insert(1, self.findChild(QRadioButton, 'layoutRadio1'))
		self.layoutRadio[0].toggled.connect(self.layoutToggle)
		self.layoutRadio[1].toggled.connect(self.layoutToggle)
		self.primaryCheck = self.findChild(QCheckBox, 'primaryCheck')
		self.primaryCheck.toggled.connect(self.primaryToggle)
		self.singleCheck = self.findChild(QCheckBox, 'singleCheck')
		self.singleCheck.toggled.connect(self.singleToggle)
		self.hotkeyCheck = self.findChild(QCheckBox, 'hotkeyCheck')
		self.hotkeyCheck.toggled.connect(self.hotkeyToggle)
		self.leftRadio.insert(0, self.findChild(QRadioButton, 'leftRadio1'))
		self.leftRadio.insert(1, self.findChild(QRadioButton, 'leftRadio2'))
		self.leftRadio.insert(2, self.findChild(QRadioButton, 'leftRadio3'))
		self.leftRadio.insert(3, self.findChild(QRadioButton, 'leftRadio4'))
		self.leftRadio[0].toggled.connect(self.leftToggle)
		self.leftRadio[1].toggled.connect(self.leftToggle)
		self.leftRadio[2].toggled.connect(self.leftToggle)
		self.leftRadio[3].toggled.connect(self.leftToggle)
		self.rightRadio.insert(0, self.findChild(QRadioButton, 'rightRadio1'))
		self.rightRadio.insert(1, self.findChild(QRadioButton, 'rightRadio2'))
		self.rightRadio.insert(2, self.findChild(QRadioButton, 'rightRadio3'))
		self.rightRadio.insert(3, self.findChild(QRadioButton, 'rightRadio4'))
		self.rightRadio[0].toggled.connect(self.rightToggle)
		self.rightRadio[1].toggled.connect(self.rightToggle)
		self.rightRadio[2].toggled.connect(self.rightToggle)
		self.rightRadio[3].toggled.connect(self.rightToggle)
		self.rightStickGroup = self.findChild(QGroupBox, 'rightStickGroup')
		self.remap4pCheck = self.findChild(QCheckBox, 'remap4pCheck')
		self.remap4pCheck.toggled.connect(self.remap4pToggle)
		self.cloneCheck = self.findChild(QCheckBox, 'cloneCheck')
		self.cloneCheck.toggled.connect(self.cloneToggle)
		self.ctrlrCheck = self.findChild(QCheckBox, 'ctrlrCheck')
		self.ctrlrCheck.toggled.connect(self.ctrlrToggle)
		self.iniCheck = self.findChild(QCheckBox, 'iniCheck')
		self.iniCheck.toggled.connect(self.iniToggle)
		self.mapDevicesCheck = self.findChild(QCheckBox, 'mapDevicesCheck')
		self.mapDevicesCheck.toggled.connect(self.mapDevicesToggle)
		self.saveDefaultCheck = self.findChild(QCheckBox, 'saveDefaultCheck')
		self.saveDefaultCheck.toggled.connect(self.saveDefaultToggle)
		self.devButtonCheck = self.findChild(QCheckBox, 'devButtonCheck')
		self.devButtonCheck.toggled.connect(self.devButtonToggle)
		self.analogCheck = self.findChild(QCheckBox, 'analogCheck')
		self.analogCheck.toggled.connect(self.analogToggle)
		self.neogeoCheck = self.findChild(QCheckBox, 'neogeoCheck')
		self.neogeoCheck.toggled.connect(self.neogeoToggle)
		self.mappingsList = self.findChild(QListWidget, 'mappingsList')
		self.mappingsList.itemChanged.connect(self.mappingsChange)
		self.previewList = self.findChild(QListWidget, 'previewWidget')
		self.deviceList = self.findChild(QListWidget, 'deviceWidget')
		self.previewTab = self.findChild(QWidget, 'previewTab')
		self.titleList = self.findChild(QListWidget, 'titleList')
		self.titleList.currentItemChanged.connect(self.previewControls)
		self.previewList = self.findChild(QListWidget, 'previewWidget')
		self.searchText = self.findChild(QLineEdit, 'searchLineEdit')
		self.searchText.returnPressed.connect(self.searchEnter)
		self.searchButton = self.findChild(QPushButton, 'searchButton')
		self.searchButton.clicked.connect(self.searchList)
		self.deviceTab = self.findChild(QWidget, 'deviceTab')
		self.getListButton = self.findChild(QPushButton, 'getListButton')
		self.getListButton.clicked.connect(self.getDeviceList)
		self.deviceList = self.findChild(QListWidget, 'deviceWidget')
		self.fixedList = self.findChild(QListWidget, 'fixedWidget')
		self.addJoyButton = self.findChild(QPushButton, 'addJoyButton')
		self.addJoyButton.clicked.connect(self.addJoystick)
		self.addGunButton = self.findChild(QPushButton, 'addGunButton')
		self.addGunButton.clicked.connect(self.addLightgun)
		# As far as I can tell, MAME does not support multiple keyboard devices. 
		# Functionality exists but is commented out, can be re-enabled if needed. Button will be set to invisible and not linked to any functions.
		self.addKBButton = self.findChild(QPushButton, 'addKBButton')
		self.addKBButton.setVisible(False)
		# self.addKBButton.clicked.connect(self.addKeyboard)
		self.addMouseButton = self.findChild(QPushButton, 'addMouseButton')
		self.addMouseButton.clicked.connect(self.addMouse)
		self.removeInputButton = self.findChild(QPushButton, 'removeInputButton')
		self.removeInputButton.clicked.connect(self.removeInput)
		self.clearButton = self.findChild(QPushButton, 'clearButton')
		self.clearButton.clicked.connect(self.clearDevices)
		self.videoCombo = self.findChild(QComboBox, 'videoCombo')
		self.bgfxCombo = self.findChild(QComboBox, 'bgfxCombo')
		self.chainsCombo = self.findChild(QComboBox, 'chainsCombo')
		self.lcdChainsCombo = self.findChild(QComboBox, 'lcdChainsCombo')
		self.svgChainsCombo = self.findChild(QComboBox, 'svgChainsCombo')
		self.fullScreenCheck = self.findChild(QCheckBox, 'fullScreenCheck')
		self.tripleBufferCheck = self.findChild(QCheckBox, 'tripleBufferCheck')
		self.cropArtCheck = self.findChild(QCheckBox, 'cropArtCheck')
		self.autosaveCheck = self.findChild(QCheckBox, 'autosaveCheck')
		self.rewindCheck = self.findChild(QCheckBox, 'rewindCheck')
		self.applyButton = self.findChild(QPushButton, 'applyButton')
		self.applyButton.clicked.connect(self.writeINIFile)
		self.iniLoadButton = self.findChild(QPushButton, 'iniLoadButton')
		self.iniLoadButton.clicked.connect(self.loadINIFile)
		self.mixedScreensCheck = self.findChild(QCheckBox, 'mixedScreensCheck')
		self.mixedScreensCheck.toggled.connect(self.mixedScreensToggle)

	def closeApp(self, s):
		# Exit Function
		saveConfig()
		sys.exit()

	def tabChanged(self, s):
		if s == 2 and selectedController != '' and len(controllerData) == 0:
			loadControllerData()
		if s == 2 and self.titleList.count() == 0:
			if len(gameData) == 0:
				loadGameData()
			debugText('Loading preview game list...')
			listLoadProgress = QProgressDialog('Processing Game List...', None, 0, len(gameData) + 1)
			listLoadProgress.setMinimumDuration(500)
			listLoadProgress.setWindowModality(Qt.WindowModality.NonModal)
			gameCount = 0
			for game in gameData.keys():
				iconList = ''
				if 'sticks' in gameData[game].keys():
					for icon in range (0, int(getIfExists(gameData[game], 'sticks', 0))):
						iconList += controlEmoji['joystick']
				if 'dials' in gameData[game].keys():
					iconList += controlEmoji['dial']
				if 'paddles' in gameData[game].keys():
					iconList += controlEmoji['paddle']
				if 'trackball' in gameData[game].keys():
					iconList += controlEmoji['trackball']
				if 'lightgun' in gameData[game].keys():
					for icon in range (0, int(getIfExists(gameData[game], 'lightgun', 0))):
						iconList += controlEmoji['lightgun']
				if 'keyboard' in gameData[game].keys():
					iconList += controlEmoji['keyboard']
				if 'mouse' in gameData[game].keys():
					iconList += controlEmoji['mouse']
				if 'pedals' in gameData[game].keys():
					iconList += controlEmoji['pedal']
				if 'mahjong' in gameData[game].keys():
					iconList += controlEmoji['mahjong']
				if 'gambling' in gameData[game].keys():
					iconList += controlEmoji['gambling']
				if 'hanafuda' in gameData[game].keys():
					iconList += controlEmoji['hanafuda']
				if iconList == '' and int(getIfExists(gameData[game], 'buttons', 0)) > 0:
					iconList += controlEmoji['button']
				item = QListWidgetItem(f"{gameData[game]['description']}{iconList}")
				item.setToolTip(game)
				self.titleList.addItem(item)
				if not parentOnly:
					for clone in gameData[game].keys():
						if clone not in notCloneKeys:
							if 'description' in gameData[game][clone].keys():
								iconList = ''
								if 'sticks' in gameData[game][clone].keys():
									for icon in range (0, getIfExists(gameData[game][clone], 'sticks', 0)):
										iconList += controlEmoji['joystick']
								if 'dials' in gameData[game][clone].keys():
									iconList += controlEmoji['dial']
								if 'paddles' in gameData[game][clone].keys():
									iconList += controlEmoji['paddle']
								if 'trackball' in gameData[game][clone].keys():
									iconList += controlEmoji['trackball']
								if 'lightgun' in gameData[game][clone].keys():
									for icon in range (0, getIfExists(gameData[game][clone], 'lightgun', 0)):
										iconList += controlEmoji['lightgun']
								if 'keyboard' in gameData[game][clone].keys():
									iconList += controlEmoji['keyboard']
								if 'mouse' in gameData[game][clone].keys():
									iconList += controlEmoji['mouse']
								if 'pedals' in gameData[game][clone].keys():
									iconList += controlEmoji['pedal']
								if 'mahjong' in gameData[game][clone].keys():
									iconList += controlEmoji['mahjong']
								if 'gambling' in gameData[game][clone].keys():
									iconList += controlEmoji['gambling']
								if 'hanafuda' in gameData[game][clone].keys():
									iconList += controlEmoji['hanafuda']
								if iconList == '' and getIfExists(gameData[game], 'buttons', 0) > 0:
									iconList += controlEmoji['button']
								item = QListWidgetItem(f"{gameData[game][clone]['description']}{iconList}")
								item.setToolTip(clone)
								self.titleList.addItem(item)
				gameCount += 1
				listLoadProgress.setValue(gameCount)
			listLoadProgress.setValue(len(gameData) + 1)
		self.titleList.sortItems()

	def locateMAME(self, s):
		global mameDir

		# User gets the MAME path
		fileName = QFileDialog.getOpenFileName(
			self,
			"Locate MAME",
			scriptDir,
			"Executable File (*.exe)"
		)
		mameDir = os.path.dirname(fileName[0])

		# Update display, enable button if valid.
		self.pathLabel.setText(mameDir)
		self.runButton.setEnabled(canWeRun(self))
		self.previewTab.setEnabled(canWeRun(self))

	def controllerChange(self, s):
		global selectedController
		global controllerData

		# Ignore if lists are filling in.
		if isLoading:
			return

		# Set controller type
		selectedController = self.controllerType.currentText()
		if os.path.isfile(f'{scriptDir}{os.path.sep}controllers{os.path.sep}{controllerTypes[selectedController]}.json'):
			self.deleteButton.setEnabled(True)
		else:
			self.deleteButton.setEnabled(False)

		# Set preview image if it exists, uses short name, allows an override by long name for custom.
		controllerPreview = f'{scriptDir}{os.path.sep}controllers{os.path.sep}{controllerTypes[selectedController]}.png'
		customControllerPreview = f'{scriptDir}{os.path.sep}controllers{os.path.sep}{selectedController}.png'		
		if os.path.isfile(customControllerPreview):
			controllerImage = QPixmap(customControllerPreview)
			self.controllerPic.setPixmap(controllerImage)
		elif os.path.isfile(controllerPreview):
			controllerImage = QPixmap(controllerPreview)
			self.controllerPic.setPixmap(controllerImage)
		else:
			# Clear pic if missing
			self.controllerPic.clear()
		# Clear controller data so it can be reloaded when needed.
		controllerData = {}

	def loadCustom(self, s):
		global isLoading
		global controllerData
		global selectedController

		debugText('Loading custom controller dialog...')
		customEdit = customWindow()
		customEdit.exec()
		isLoading = True
		self.controllerType.clear()
		for controller in controllerTypes.keys():
			self.controllerType.addItem(controller)
		controllerData = {}
		isLoading = False
		if selectedController not in controllerTypes.keys():
			selectedController = 'Xinput (Xbox Style)'
		selectedIndex = self.controllerType.findText(selectedController)
		if selectedIndex > -1:
			self.controllerType.setCurrentIndex(selectedIndex)

	def deleteCustom(self, s):
		global isLoading
		global controllerData

		confirmation = showMessage('Confirm', 'Delete current custom controller profile?', QMessageBox.Icon.Question, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
		if confirmation == QMessageBox.StandardButton.Yes:
			controllerFile = f'{scriptDir}{os.path.sep}controllers{os.path.sep}{self.controllerType.text()}'
			if os.path.isfile(controllerFile):
				os.remove(controllerFile)
			else:
				showMessage('Missing File', f'{controllerFile} does not exist, it may have been deleted or renamed.', QMessageBox.Icon.Critical)
			loadControllerTypes()
			isLoading = True
			self.controllerType.clear()
			for controller in controllerTypes.keys():
				self.controllerType.addItem(controller)
			controllerData = {}
			isLoading = False
			if selectedController not in controllerTypes.keys():
				selectedController = 'Xinput (Xbox Style)'
				selectedIndex = self.controllerType.findText(selectedController)
			if selectedIndex > -1:
				self.controllerType.setCurrentIndex(selectedIndex)

	def pToggle(self, s):
		global playerChecks

		if isLoading:
			return

		for check in range(0, 4):
			if self.pCheck[check].isChecked():
				playerChecks[check] = 1
			else:
				playerChecks[check] = 0

		# Enable/disable various options based on selected players.
		if self.pCheck[0].isChecked():
			self.hotkeysGroup.setEnabled(True)
		else:
			self.hotkeysGroup.setEnabled(False)

		if self.pCheck[0].isEnabled() and self.pCheck[1].isChecked():
			self.rightRadio[3].setEnabled(True)
		else:
			self.rightRadio[3].setEnabled(False)

		if (self.pCheck[0].isEnabled() and self.pCheck[1].isChecked() and
			self.pCheck[2].isEnabled() and self.pCheck[3].isChecked()):
			self.leftRadio[3].setEnabled(True)
			self.remap4pCheck.setEnabled(True)
		else:
			self.leftRadio[3].setEnabled(False)
			self.remap4pCheck.setEnabled(False)

		self.runButton.setEnabled(canWeRun(self))
		self.previewTab.setEnabled(canWeRun(self))

	def layoutToggle(self, s):
		global buttonLayout

		if isLoading:
			return

		if self.layoutRadio[0].isChecked():
			buttonLayout = 'NES'
		elif self.layoutRadio[1].isChecked():
			buttonLayout = 'SNES'

	def primaryToggle(self, s):
		global swapPrimary

		if isLoading:
			return

		if self.primaryCheck.isChecked():
			swapPrimary = 1
		else:
			swapPrimary = 0

	def singleToggle(self, s):
		global singleButton

		if isLoading:
			return

		if self.singleCheck.isChecked():
			singleButton = 1
		else:
			singleButton = 0

	def hotkeyToggle(self, s):
		global hotkeyMode

		if isLoading:
			return

		if self.hotkeyCheck.isChecked():
			hotkeyMode = 1
		else:
			hotkeyMode = 0

	def leftToggle(self, s):
		global leftStickMode

		if isLoading:
			return

		for radio in range(0, 4):
			if self.leftRadio[radio].isChecked():
				leftStickMode = radio + 1

		if self.leftRadio[3].isChecked():
			self.rightStickGroup.setEnabled(False)
		else:
			self.rightStickGroup.setEnabled(True)

		self.runButton.setEnabled(canWeRun(self))
		self.previewTab.setEnabled(canWeRun(self))

	def rightToggle(self, s):
		global rightStickMode

		if isLoading:
			return

		for radio in range(0, 4):
			if self.rightRadio[radio].isChecked():
				rightStickMode = radio + 1

		self.runButton.setEnabled(canWeRun(self))
		self.previewTab.setEnabled(canWeRun(self))

	def remap4pToggle(self, s):
		global remap4p

		if isLoading:
			return

		# Note: setting ignored if all four players are not selected
		if self.remap4pCheck.isChecked():
			remap4p = 1
		else:
			remap4p = 0

	def cloneToggle(self, s):
		global parentOnly

		if isLoading:
			return

		if self.cloneCheck.isChecked():
			parentOnly = 1
		else:
			parentOnly = 0

		self.titleList.clear()

	def ctrlrToggle(self, s):
		global makeCtrlr

		if isLoading:
			return

		if self.ctrlrCheck.isChecked():
			makeCtrlr = 1
		else:
			makeCtrlr = 0

		self.mapDevicesCheck.setEnabled(makeCtrlr)
		self.iniCheck.setEnabled(makeCtrlr)

		if makeCtrlr and mapDevices:
			self.deviceTab.setEnabled(True)
		else:
			self.deviceTab.setEnabled(False)

	def iniToggle(self, s):
		global addToINI

		if isLoading:
			return

		if self.iniCheck.isChecked():
			addToINI = 1
		else:
			addToINI = 0

	def mapDevicesToggle(self, s):
		global mapDevices

		if isLoading:
			return

		if self.mapDevicesCheck.isChecked():
			mapDevices = 1
		else:
			mapDevices = 0

	def devButtonToggle(self, s):
		global devButtons

		if isLoading:
			return

		if self.devButtonCheck.isChecked():
			devButtons = 1
		else:
			devButtons = 0

	def analogToggle(self, s):
		global digitalAnalog

		if isLoading:
			return

		if self.analogCheck.isChecked():
			digitalAnalog = 1
		else:
			digitalAnalog = 0

	def saveDefaultToggle(self, s):
		global saveDefault

		if isLoading:
			return

		if self.saveDefaultCheck.isChecked():
			saveDefault = 1
		else:
			saveDefault = 0

	def mixedScreensToggle(self, s):
		global mixedScreens

		if isLoading:
			return

		if self.mixedScreensCheck.isChecked():
			mixedScreens = 1
		else:
			mixedScreens = 0

	def neogeoToggle(self, s):
		global neogeo

		if isLoading:
			return

		if self.neogeoCheck.isChecked():
			neogeo = 1
		else:
			neogeo = 0

	def mappingsChange(self, s):
		global applyMappings

		if isLoading:
			return

		applyMappings = []
		for index in range(self.mappingsList.count()):
			item = self.mappingsList.item(index)
			if item.checkState() == Qt.CheckState.Checked:
				applyMappings.append(item.text())

		if 'Neo Geo' in applyMappings:
			self.neogeoCheck.setEnabled(True)
		else:
			self.neogeoCheck.setEnabled(False)

	def previewControls(self, s):
		currentGame = self.titleList.currentItem()
		if currentGame == None:
			return
		shortName = currentGame.toolTip()
		debugText(f'Looking up {currentGame.text()} - {currentGame.toolTip()}')
		gameData = findGame(shortName)
		gameControls = mapGameControls(shortName)
		controlNames = getIfExists(gameData, 'controls')
		maxPlayers = getIfExists(gameData, 'playercount')
		if maxPlayers == None:
			maxPlayers = 4
		self.previewList.clear()
		debugText(f"{shortName} max players: {maxPlayers}, buttons: {getIfExists(gameData, 'buttons', 12)}")
		for player in range(0, maxPlayers):
			for control in gameControls[player].keys():
				if 'FACE' not in control and 'ANALOG_' not in control:
					if getIfExists(controlNames, gameControls[player][control]['mamemap']) != None:
						controlText = getIfExists(controlNames, gameControls[player][control]['mamemap'])
					elif player > 0 and getIfExists(controlNames, gameControls[0][control]['mamemap']) != None:
						controlText = getIfExists(controlNames, gameControls[0][control]['mamemap'])
					else:
						controlText = control
					if controlInGame(gameData, gameControls[player][control]):
						debugText(f"Adding {control} to the list: {gameControls[player][control]}")
						item = QListWidgetItem(f"P{player + 1} {gameControls[player][control]['friendlyname']}: {controlText.upper()}")
						item.setToolTip(gameControls[player][control]['mamemap'])
						self.previewList.addItem(item)

	def searchList(self, s):
		debugText(f'Searching for {self.searchText.text()}')
		startItem = self.titleList.currentRow()
		foundItem = False
		for item in range(startItem + 1, self.titleList.count()):
			if self.titleList.item(item).toolTip().upper() == self.searchText.text().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				foundItem = True
				break
			elif self.titleList.item(item).text().upper() == self.searchText.text().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				foundItem = True
				break
			elif self.searchText.text().upper() in self.titleList.item(item).toolTip().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				foundItem = True
				break
			elif self.searchText.text().upper() in self.titleList.item(item).text().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				foundItem = True
				break
		if foundItem:
			return
		for item in range(0, startItem):
			if self.titleList.item(item).toolTip().upper() == self.searchText.text().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				break
			elif self.titleList.item(item).text().upper() == self.searchText.text().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				break
			elif self.searchText.text().upper() in self.titleList.item(item).toolTip().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				break
			elif self.searchText.text().upper() in self.titleList.item(item).text().upper():
				self.titleList.setCurrentItem(self.titleList.item(item))
				break

	def searchEnter(self):
		self.searchList('')

	def getDeviceList(self, s):
		global inputDevices

		inputDevices = { 'joystick': {}, 'lightgun': {}, 'keyboard': {}, 'mouse': {} }
		confirmRun = showMessage('Confirm','Launch MAME to get device IDs?\nPlease close the MAME window after it opens to resume.',QMessageBox.Icon.Question,(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No))
		if confirmRun == QMessageBox.StandardButton.No:
			return
		mameExe = f'{mameDir}{os.path.sep}mame.exe'
		mameOutput = ''
		try:
			mameOutput = subprocess.check_output([mameExe, '-v', '-w', '-nomax', '-str', '5'], universal_newlines=True)
		except:
			if len(mameOutput) == 0:
				showMessage('Error', 'Problem launching MAME', QMessageBox.Icon.Critical)
				return
		for outputLine in mameOutput.splitlines():
			if outputLine.startswith('Input:'):
				idStart = outputLine.find('HID#')
				idEnd = find_nth(outputLine, '#', 3)
				deviceID = outputLine[idStart:idEnd]
				typeStart = outputLine.rfind('Adding') + 7
				typeEnd = outputLine.find('#') - 1
				if deviceID not in inputDevices[outputLine[typeStart:typeEnd]]:
					inputDevices[outputLine[typeStart:typeEnd]][deviceID] = {}
					nameStart = find_nth(outputLine, ':', 2) + 2
					nameEnd = outputLine.find('(') - 1
					inputDevices[outputLine[typeStart:typeEnd]][deviceID]['name'] = outputLine[nameStart:nameEnd]
		if platform.system() == 'Windows':
			for xinput in range(1, 5):
				inputDevices['joystick'][f'XInput Player {xinput}'] = {}
				inputDevices['joystick'][f'XInput Player {xinput}']['name'] = f'XInput Player {xinput}'
		self.deviceList.clear()
		debugText(inputDevices)
		self.fillDeviceList()

	def fillDeviceList(self):
		if len(inputDevices['joystick']) + len(inputDevices['lightgun']) + len(inputDevices['mouse']) > 0:
			for controlType in inputDevices:
				if controlType != 'keyboard':
					for inputDevice in inputDevices[controlType].keys():
						item = QListWidgetItem(inputDevices[controlType][inputDevice]['name'])
						item.setWhatsThis(inputDevice)
						item.setText(f'{controlEmoji[controlType]}{item.text()}')
						self.deviceList.addItem(item)
			self.addJoyButton.setEnabled(True)
			self.addGunButton.setEnabled(True)
			# self.addKBButton.setEnabled(True)
			self.addMouseButton.setEnabled(True)
			self.removeInputButton.setEnabled(True)
			self.clearButton.setEnabled(True)
			self.deviceList.sortItems()

	def addJoystick(self, s):
		global fixedDevices

		currentDevice = self.deviceList.currentItem()
		if currentDevice == None:
			showMessage('Unable to add','Please select a device on the left side first.')
			return
		if len(fixedDevices['joystick'].keys()) == 10:
			showMessage('Unable to add','MAME supports a maximum of 10 joysticks.', QMessageBox.Icon.Critical)
			return
		if controlEmoji['joystick'] not in currentDevice.text():
			showMessage('Unable to add','Please select a Joystick device.')
			return
		if currentDevice.whatsThis() in fixedDevices['joystick'].keys():
			showMessage('Unable to add','This device is already set as a joystick.')
			return
		controllerID = len(fixedDevices['joystick'].keys()) + 1
		for inputDevice in inputDevices['joystick'].keys():
			if inputDevice == currentDevice.whatsThis():
				fixedDevices['joystick'][inputDevice] = inputDevice
				item = QListWidgetItem(f"{controlEmoji['joystick']} #{controllerID} - {inputDevices['joystick'][inputDevice]['name']}")
				item.setWhatsThis(inputDevice)
				self.fixedList.addItem(item)
		self.fixedList.sortItems()

	def addLightgun(self, s):
		global fixedDevices

		currentDevice = self.deviceList.currentItem()
		if currentDevice == None:
			showMessage('Unable to add','Please select a device on the left side first.')
			return
		if len(fixedDevices['lightgun'].keys()) == 10:
			showMessage('Unable to add','MAME supports a maximum of 10 lightguns.', QMessageBox.Icon.Critical)
			return
		if controlEmoji['lightgun'] not in currentDevice.text():
			showMessage('Unable to add','Please select a Lightgun device.')
			return
		if currentDevice.whatsThis() in fixedDevices['lightgun'].keys():
			showMessage('Unable to add','This device is already set as a lightgun.')
			return
		controllerID = len(fixedDevices['lightgun'].keys()) + 1
		for inputDevice in inputDevices['lightgun'].keys():
			if inputDevice == currentDevice.whatsThis():
				fixedDevices['lightgun'][inputDevice] = inputDevice
				item = QListWidgetItem(f"{controlEmoji['lightgun']} #{controllerID} - {inputDevices['lightgun'][inputDevice]['name']}")
				item.setWhatsThis(inputDevice)
				self.fixedList.addItem(item)
		self.fixedList.sortItems()

	def addKeyboard(self, s):
		global fixedDevices

		currentDevice = self.deviceList.currentItem()
		if currentDevice == None:
			showMessage('Unable to add','Please select a device on the left side first.')
			return
		if len(fixedDevices['keyboard'].keys()) == 10:
			showMessage('Unable to add','MAME supports a maximum of 10 keyboards.', QMessageBox.Icon.Critical)
			return
		if controlEmoji['keyboard'] not in currentDevice.text():
			showMessage('Unable to add','Please select a Keyboard device.')
			return
		if currentDevice.whatsThis() in fixedDevices['keyboard'].keys():
			showMessage('Unable to add','This device is already set as a keyboard.')
			return
		controllerID = len(fixedDevices['keyboard'].keys()) + 1
		for inputDevice in inputDevices['keyboard'].keys():
			if inputDevice == currentDevice.whatsThis():
				fixedDevices['keyboard'][inputDevice] = inputDevice
				item = QListWidgetItem(f"{controlEmoji['keyboard']} #{controllerID} - {inputDevices['keyboard'][inputDevice]['name']}")
				item.setWhatsThis(inputDevice)
				self.fixedList.addItem(item)
		self.fixedList.sortItems()

	def addMouse(self, s):
		global fixedDevices

		currentDevice = self.deviceList.currentItem()
		if currentDevice == None:
			showMessage('Unable to add','Please select a device on the left side first.')
			return
		if len(fixedDevices['mouse'].keys()) == 10:
			showMessage('Unable to add','MAME supports a maximum of 10 mice.', QMessageBox.Icon.Critical)
			return
		if controlEmoji['mouse'] not in currentDevice.text():
			showMessage('Unable to add','Please select a Mouse device.')
			return
		if currentDevice.whatsThis() in fixedDevices['mouse'].keys():
			showMessage('Unable to add','This device is already set as a mouse.')
			return
		controllerID = len(fixedDevices['mouse'].keys()) + 1
		for inputDevice in inputDevices['mouse'].keys():
			if inputDevice == currentDevice.whatsThis():
				fixedDevices['mouse'][inputDevice] = inputDevice
				item = QListWidgetItem(f"{controlEmoji['mouse']} #{controllerID} - {inputDevices['mouse'][inputDevice]['name']}")
				item.setWhatsThis(inputDevice)
				self.fixedList.addItem(item)
		self.fixedList.sortItems()

	def removeInput(self, s):
		global fixedDevices

		currentDevice = self.fixedList.currentItem()
		if currentDevice == None:
			showMessage('Unable to remove','Please select a device on the right side first.')
			return
		if controlEmoji['joystick'] in currentDevice.text():
			del fixedDevices['joystick'][currentDevice.whatsThis()]
		if controlEmoji['lightgun'] in currentDevice.text():
			del fixedDevices['lightgun'][currentDevice.whatsThis()]
		if controlEmoji['keyboard'] in currentDevice.text():
			del fixedDevices['keyboard'][currentDevice.whatsThis()]
		if controlEmoji['mouse'] in currentDevice.text():
			del fixedDevices['mouse'][currentDevice.whatsThis()]
		self.fillFixedDeviceList()

	def fillFixedDeviceList(self):
		self.fixedList.clear()
		controllerID = 1
		for inputDevice in fixedDevices['joystick'].keys():
			item = QListWidgetItem(f"{controlEmoji['joystick']} #{controllerID} - {inputDevices['joystick'][inputDevice]['name']}")
			item.setWhatsThis(inputDevice)
			self.fixedList.addItem(item)
			controllerID += 1
		controllerID = 1
		for inputDevice in fixedDevices['lightgun'].keys():
			item = QListWidgetItem(f"{controlEmoji['lightgun']} #{controllerID} - {inputDevices['lightgun'][inputDevice]['name']}")
			item.setWhatsThis(inputDevice)
			self.fixedList.addItem(item)
			controllerID += 1
		controllerID = 1
		#for inputDevice in fixedDevices['keyboard'].keys():
		#	item = QListWidgetItem(f"{controlEmoji['keyboard']} #{controllerID} - {inputDevices['keyboard'][inputDevice]['name']}")
		#	item.setWhatsThis(inputDevice)
		#	self.fixedList.addItem(item)
		#	controllerID += 1
		controllerID = 1
		for inputDevice in fixedDevices['mouse'].keys():
			item = QListWidgetItem(f"{controlEmoji['mouse']} #{controllerID} - {inputDevices['mouse'][inputDevice]['name']}")
			item.setWhatsThis(inputDevice)
			self.fixedList.addItem(item)
			controllerID += 1
		self.fixedList.sortItems()

	def clearDevices(self, s):
		global fixedDevices

		fixedDevices = { 'joystick': {}, 'lightgun': {}, 'keyboard': {}, 'mouse': {} }
		self.fixedList.clear()

	def writeINIFile(self, s):
		foundVideo = False
		foundBackend = False
		foundChains = False
		foundTriple = False
		foundFullscreen = False
		foundWindow = False
		foundCrop = False
		foundAutosave = False
		foundRewind = False

		# BGFX Chains will be set for up to 4 windows on one monitor for CRTs, 1 each for LCD & SVG.

		debugText('Saving settings to mame.ini')
		iniFile = f'{mameDir}{os.path.sep}mame.ini'
		if os.path.isfile(iniFile):
			with fileinput.FileInput(iniFile, inplace = True, backup ='.bak') as currentINI:
				for iniLine in currentINI:
					if iniLine.startswith('video '):
						debugText('video line found in mame.ini')
						print(f'video                     {self.videoCombo.currentText()}',end ='\n')
						foundVideo = True
					elif iniLine.startswith('bgfx_backend '):
						debugText('bgfx backend line found in mame.ini')
						print(f'bgfx_backend              {self.bgfxCombo.currentText()}',end ='\n')
						foundBackend = True
					elif iniLine.startswith('bgfx_screen_chains '):
						debugText('bgfx screen chains line found in mame.ini')
						print(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.chainsCombo.currentText()},{self.chainsCombo.currentText()},{self.chainsCombo.currentText()}',end ='\n')
						foundChains = True
					elif iniLine.startswith('triplebuffer '):
						debugText('triplebuffer line found in mame.ini')
						print(f'triplebuffer              {int(self.tripleBufferCheck.isChecked() == True)}',end ='\n')
						foundTriple = True
					elif iniLine.startswith('window '):
						debugText('window line found in mame.ini')
						print(f'window                    {int(self.fullScreenCheck.isChecked() == False)}',end ='\n')
						foundFullscreen = True
					elif iniLine.startswith('artwork_crop '):
						debugText('artwork crop found in mame.ini')
						print(f'artwork_crop              {int(self.cropArtCheck.isChecked() == True)}',end ='\n')
						foundCrop = True
					elif iniLine.startswith('autosave '):
						debugText('autosave found in mame.ini')
						print(f'autosave                  {int(self.autosaveCheck.isChecked() == True)}',end ='\n')
						foundAutosave = True
					elif iniLine.startswith('rewind '):
						debugText('rewind found in mame.ini')
						print(f'rewind                    {int(self.rewindCheck.isChecked() == True)}',end ='\n')
						foundRewind = True
					else:
						print(iniLine, end ='')
			with open(iniFile, 'a') as mameINI:
				if not foundVideo:
					mameINI.write(f'video                     {self.videoCombo.currentText()}')
				if not foundBackend:
					mameINI.write(f'bgfx_backend              {self.bgfxCombo.currentText()}')
				if not foundChains:
					mameINI.write(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.chainsCombo.currentText()},{self.chainsCombo.currentText()},{self.chainsCombo.currentText()}')
				if not foundTriple:
					mameINI.write(f'triplebuffer              {int(self.tripleBufferCheck.isChecked() == True)}')
				if not foundFullscreen:
					mameINI.write(f'window                    {int(self.fullScreenCheck.isChecked() == False)}')
				if not foundCrop:
					mameINI.write(f'artwork_crop              {int(self.cropArtCheck.isChecked() == True)}')
				if not foundAutosave:
					mameINI.write(f'autosave                  {int(self.autosaveCheck.isChecked() == True)}')
				if not foundRewind:
					mameINI.write(f'rewind                    {int(self.rewindCheck.isChecked() == True)}')
				mameINI.close()
		else:
			with open(iniFile, 'w') as mameINI:
				newINI = []
				newINI.append(f'video                     {self.videoCombo.currentText()}')
				newINI.append(f'bgfx_backend              {self.bgfxCombo.currentText()}')
				newINI.append(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.chainsCombo.currentText()},{self.chainsCombo.currentText(),{self.chainsCombo.currentText()}}')
				newINI.append(f'triplebuffer              {int(self.tripleBufferCheck.isChecked() == True)}')
				newINI.append(f'window                    {int(self.fullScreenCheck.isChecked() == False)}')
				newINI.append(f'artwork_crop              {int(self.cropArtCheck.isChecked() == True)}')
				newINI.append(f'autosave                  {int(self.autosaveCheck.isChecked() == True)}')
				newINI.append(f'rewind                    {int(self.rewindCheck.isChecked() == True)}')
				mameINI.writelines(newINI)
				mameINI.close()

		iniFile = f'{mameDir}{os.path.sep}lcd.ini'
		foundChains = False
		if os.path.isfile(iniFile):
			with fileinput.FileInput(iniFile, inplace = True, backup ='.bak') as currentINI:
				for iniLine in currentINI:
					if iniLine.startswith('video '):
						if iniLine.startswith('bgfx_screen_chains '):
							debugText('bgfx screen chains line found in lcd.ini')
							print(f'bgfx_screen_chains        {self.lcdChainsCombo.currentText()}',end ='\n')
							foundChains = True
			if not foundChains:
				with open(iniFile, 'w') as mameINI:
					mameINI.write(f'bgfx_screen_chains        {self.lcdChainsCombo.currentText()}\n')
					mameINI.close()
		else:
			with open(iniFile, 'w') as mameINI:
				mameINI.write(f'bgfx_screen_chains        {self.lcdChainsCombo.currentText()}\n')

		iniFile = f'{mameDir}{os.path.sep}svg.ini'
		foundChains = False
		if os.path.isfile(iniFile):
			with fileinput.FileInput(iniFile, inplace = True, backup ='.bak') as currentINI:
				for iniLine in currentINI:
					if iniLine.startswith('video '):
						if iniLine.startswith('bgfx_screen_chains '):
							debugText('bgfx screen chains line found in svg.ini')
							print(f'bgfx_screen_chains        {self.svgChainsCombo.currentText()}',end ='\n')
							foundChains = True
			if not foundChains:
				with open(iniFile, 'w') as mameINI:
					mameINI.write(f'bgfx_screen_chains        {self.svgChainsCombo.currentText()}\n')
					mameINI.close()
		else:
			with open(iniFile, 'w') as mameINI:
				mameINI.write(f'bgfx_screen_chains        {self.svgChainsCombo.currentText()}\n')
				mameINI.close()

		if mixedScreens == 1:
			# CRT main screen, LCD subdisplay
			# All CDi games have the LCD available. The only Hornet games with 2 displays are the Silent Scope series. Condensing down to system to prevent clutter.
			mixedINIs = ['cdi', 'hornet']
			for mixed in mixedINIs:
				iniFile = f'{mameDir}{os.path.sep}{mixed}.ini'
				foundChains = False
				if os.path.isfile(iniFile):
					with fileinput.FileInput(iniFile, inplace = True, backup ='.bak') as currentINI:
						for iniLine in currentINI:
							if iniLine.startswith('video '):
								if iniLine.startswith('bgfx_screen_chains '):
									debugText(f'bgfx screen chains line found in {mixed}.ini')
									print(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.lcdChainsCombo.currentText()}',end ='\n')
									foundChains = True
					if not foundChains:
						with open(iniFile, 'w') as mameINI:
							mameINI.write(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.lcdChainsCombo.currentText()}\n')
							mameINI.close()
				else:
					with open(iniFile, 'w') as mameINI:
						mameINI.write(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.lcdChainsCombo.currentText()}\n')
						mameINI.close()

			# CRT main screen, 2xLCD subdisplay
			# Just one system for some mahjong games, most only use 1 display but some have 2 LCDs to show player hands.
			# Leaving this as a list in case more are added in the future.
			mixedINIs = ['nbmj8688']
			for mixed in mixedINIs:
				iniFile = f'{mameDir}{os.path.sep}{mixed}.ini'
				foundChains = False
				if os.path.isfile(iniFile):
					with fileinput.FileInput(iniFile, inplace = True, backup ='.bak') as currentINI:
						for iniLine in currentINI:
							if iniLine.startswith('video '):
								if iniLine.startswith('bgfx_screen_chains '):
									debugText(f'bgfx screen chains line found in {mixed}.ini')
									print(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.lcdChainsCombo.currentText()},{self.lcdChainsCombo.currentText()}',end ='\n')
									foundChains = True
					if not foundChains:
						with open(iniFile, 'w') as mameINI:
							mameINI.write(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.lcdChainsCombo.currentText()},{self.lcdChainsCombo.currentText()}\n')
							mameINI.close()
				else:
					with open(iniFile, 'w') as mameINI:
						mameINI.write(f'bgfx_screen_chains        {self.chainsCombo.currentText()},{self.lcdChainsCombo.currentText()},{self.lcdChainsCombo.currentText()}\n')
						mameINI.close()

		showMessage('Done!','Added settings to ini files.')

	def loadINIFile(self, s):
		debugText('Loading settings from mame.ini')
		iniFile = f'{mameDir}{os.path.sep}mame.ini'
		if os.path.isfile(iniFile):
			mameINI = open(iniFile, 'r')
			currentINI = mameINI.readlines()
			mameINI.close()
			for iniLine in currentINI:
				if iniLine.startswith('video '):
					for item in range(0, self.videoCombo.count()):
						if self.videoCombo.itemText(item) in iniLine:
							self.videoCombo.setCurrentIndex(item)
					debugText('video line found in mame.ini')
				elif iniLine.startswith('bgfx_backend '):
					for item in range(0, self.bgfxCombo.count()):
						if self.bgfxCombo.itemText(item) in iniLine:
							self.bgfxCombo.setCurrentIndex(item)
				elif iniLine.startswith('bgfx_screen_chains '):
					for item in range(0, self.chainsCombo.count()):
						if f'{self.chainsCombo.itemText(item)}\n' in iniLine or iniLine.endswith(self.chainsCombo.itemText(item)):
							self.chainsCombo.setCurrentIndex(item)
				elif iniLine.startswith('triplebuffer '):
					if '0' in iniLine:
						self.tripleBufferCheck.setChecked(False)
					else:
						self.tripleBufferCheck.setChecked(True)
				elif iniLine.startswith('window '):
					if '0' in iniLine:
						self.fullScreenCheck.setChecked(True)
					else:
						self.fullScreenCheck.setChecked(False)
				elif iniLine.startswith('artwork_crop '):
					if '0' in iniLine:
						self.cropArtCheck.setChecked(False)
					else:
						self.cropArtCheck.setChecked(True)
				elif iniLine.startswith('autosave '):
					if '0' in iniLine:
						self.autosaveCheck.setChecked(False)
					else:
						self.autosaveCheck.setChecked(True)
				elif iniLine.startswith('rewind '):
					if '0' in iniLine:
						self.rewindCheck.setChecked(False)
					else:
						self.rewindCheck.setChecked(True)

		debugText('Loading settings from lcd.ini')
		iniFile = f'{mameDir}{os.path.sep}lcd.ini'
		if os.path.isfile(iniFile):
			mameINI = open(iniFile, 'r')
			currentINI = mameINI.readlines()
			mameINI.close()
			for iniLine in currentINI:
				if iniLine.startswith('bgfx_screen_chains '):
					for item in range(0, self.lcdChainsCombo.count()):
						if f'{self.lcdChainsCombo.itemText(item)}\n' in iniLine or iniLine.endswith(self.lcdChainsCombo.itemText(item)):
							self.lcdChainsCombo.setCurrentIndex(item)

		debugText('Loading settings from svg.ini')
		iniFile = f'{mameDir}{os.path.sep}svg.ini'
		if os.path.isfile(iniFile):
			mameINI = open(iniFile, 'r')
			currentINI = mameINI.readlines()
			mameINI.close()
			for iniLine in currentINI:
				debugText(f'Screen chains in {iniFile}: {iniLine}')
				if iniLine.startswith('bgfx_screen_chains '):
					for item in range(0, self.svgChainsCombo.count()):
						if f'{self.svgChainsCombo.itemText(item)}\n' in iniLine or iniLine.endswith(self.svgChainsCombo.itemText(item)):
							self.svgChainsCombo.setCurrentIndex(item)

	def runGeneration(self, s):
		if makeCtrlr == 1:
			if os.path.isfile(f'{mameDir}{os.path.sep}ctrlr{os.path.sep}{controllerTypes[selectedController]}.cfg'):
				response = showMessage('Confirm',f'This will replace {mameDir}{os.path.sep}ctrlr{os.path.sep}{controllerTypes[selectedController]}.cfg, would you like to continue?', \
						QMessageBox.Icon.Question, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
				if response == QMessageBox.StandardButton.No:
					return
		else:
			response = showMessage('Confirm',f'This will replace any .cfg files in {mameDir}{os.path.sep}cfg{os.path.sep}, would you like to continue?', \
				QMessageBox.Icon.Question, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
			if response == QMessageBox.StandardButton.No:
				return
		gamesToProcess = generateRemapList()
		gamesProcessed = 0
		if makeCtrlr:
			progressText = f'Generating ctrlr file\n0/{len(gamesToProcess)} games processed.'
		else:
			progressText = f'Generating cfg file 0/{len(gamesToProcess)}'
		win.setEnabled(False)
		generationProgress = QProgressDialog(progressText, 'Cancel', 0, len(gamesToProcess) + 1)
		generationProgress.setMinimumDuration(0)
		generationProgress.setWindowModality(Qt.WindowModality.ApplicationModal)
		if makeCtrlr:
			# Open/Create CFG file
			mainXML = minidom.Document()
			cfgFile = f'{mameDir}{os.path.sep}ctrlr{os.path.sep}{controllerTypes[selectedController]}.cfg'
			xmlRoot = getRoot(mainXML, 'mameconfig')
			xmlRoot.setAttribute('version','10')
			for game in gamesToProcess:
				gameControls = mapGameControls(game)
				debugText(f'Adding {game} to ctrlr file ({gamesProcessed + 1}/{len(gamesToProcess)})...')
				xmlSystem = mainXML.createElement('system')
				xmlSystem.setAttribute('name', game)
				xmlRoot.appendChild(xmlSystem)
				removeSection(mainXML, xmlSystem, 'input')
				xmlInput = mainXML.createElement('input')
				xmlSystem.appendChild(xmlInput)
				for player in range(0, len(gameControls)):
					for control in gameControls[player].keys():
						debugText(control)
						if 'ANALOG_' in control:
							if digitalAnalog == 1:
								if 'UP' in control:
									for analogControl in ['PADDLE_V', 'POSITIONAL_V', 'DIAL_V', 'TRACKBALL_Y', 'AD_STICK_Y', 'LIGHTGUN_Y', 'MOUSE_Y']:
										xmlPort = mainXML.createElement('port')
										xmlPort.setAttribute('type', f'P{player + 1}_{analogControl}')
										xmlIncrement = mainXML.createElement('newseq')
										xmlIncrement.setAttribute('type', 'increment')
										xmlPort.appendChild(xmlIncrement)
										downData = mainXML.createTextNode(gameControls[player]['ANALOG_DOWN']['internalname'])
										xmlIncrement.appendChild(downData)
										xmlDecrement = mainXML.createElement('newseq')
										xmlDecrement.setAttribute('type', 'decrement')
										xmlPort.appendChild(xmlDecrement)
										upData = mainXML.createTextNode(gameControls[player]['ANALOG_UP']['internalname'])
										xmlDecrement.appendChild(upData)
										xmlInput.appendChild(xmlPort)
								if 'LEFT' in control:
									for analogControl in ['PADDLE', 'POSITIONAL', 'DIAL', 'TRACKBALL_X', 'AD_STICK_X', 'LIGHTGUN_X', 'MOUSE_X']:
										xmlPort = mainXML.createElement('port')
										xmlPort.setAttribute('type', f'P{player + 1}_{analogControl}')
										xmlIncrement = mainXML.createElement('newseq')
										xmlIncrement.setAttribute('type', 'increment')
										xmlPort.appendChild(xmlIncrement)
										rightData = mainXML.createTextNode(gameControls[player]['ANALOG_RIGHT']['internalname'])
										xmlIncrement.appendChild(rightData)
										xmlDecrement = mainXML.createElement('newseq')
										xmlDecrement.setAttribute('type', 'decrement')
										xmlPort.appendChild(xmlDecrement)
										leftData = mainXML.createTextNode(gameControls[player]['ANALOG_LEFT']['internalname'])
										xmlDecrement.appendChild(leftData)
										xmlInput.appendChild(xmlPort)
						elif 'FACE' not in control:
							if getIfExists(gameControls[player][control], 'mamemap') != '':
								xmlPort = mainXML.createElement('port')
								xmlPort.setAttribute('type', gameControls[player][control]['mamemap'])
								xmlNewseq = mainXML.createElement('newseq')
								xmlNewseq.setAttribute('type', 'standard')
								xmlPort.appendChild(xmlNewseq)
								inputData = mainXML.createTextNode(gameControls[player][control]['internalname'])
								xmlNewseq.appendChild(inputData)
								xmlInput.appendChild(xmlPort)
				if game == 'default' and mapDevices == 1:
					debugText('Mapping input devices.')
					if len(fixedDevices['joystick']) > 0:
						deviceNumber = 1
						for joystick in fixedDevices['joystick'].keys():
							xmlDevice = mainXML.createElement('mapdevice')
							xmlDevice.setAttribute('device', joystick)
							xmlDevice.setAttribute('controller', f'JOYCODE_{str(deviceNumber)}')
							xmlInput.appendChild(xmlDevice)
							deviceNumber += 1
					if len(fixedDevices['lightgun']) > 0:
						deviceNumber = 1
						for lightgun in fixedDevices['lightgun'].keys():
							xmlDevice = mainXML.createElement('mapdevice')
							xmlDevice.setAttribute('device', lightgun)
							xmlDevice.setAttribute('controller', f'GUNCODE_{str(deviceNumber)}')
							xmlInput.appendChild(xmlDevice)
							deviceNumber += 1
					if len(fixedDevices['mouse']) > 0:
						deviceNumber = 1
						for mouse in fixedDevices['mouse'].keys():
							xmlDevice = mainXML.createElement('mapdevice')
							xmlDevice.setAttribute('device', mouse)
							xmlDevice.setAttribute('controller', f'MOUSECODE_{str(deviceNumber)}')
							xmlInput.appendChild(xmlDevice)
							deviceNumber += 1
				gamesProcessed += 1
				generationProgress.setValue(gamesProcessed)
				generationProgress.setLabelText(f'Generating ctrlr file\n{gamesProcessed}/{len(gamesToProcess)} games processed.')
				if generationProgress.wasCanceled():
					showMessage('Cancelled','ctrlr file generation cancelled.')
					win.setEnabled(True)
					return
			finalXML = codecs.open(cfgFile, "w", "utf-8")
			cleanXML = os.linesep.join([s for s in mainXML.toprettyxml().splitlines() if s.strip()])
			finalXML.write(cleanXML)
			if addToINI == 1:
				debugText('Adding ctrlr file to mame.ini')
				iniFile = f'{mameDir}{os.path.sep}mame.ini'
				if os.path.isfile(iniFile):
					with fileinput.FileInput(iniFile, inplace = True, backup ='.bak') as currentINI:
						for iniLine in currentINI:
							if iniLine.startswith('ctrlr '):
								debugText('ctrlr line found in mame.ini')
								print(f'ctrlr                     {controllerTypes[selectedController]}',end ='\n')
							else:
								print(iniLine, end ='')
				else:
					with open(iniFile, 'w') as mameINI:
						currentINI = mameINI.write(f'ctrlr                     {controllerTypes[selectedController]}')
		else:
			for game in gamesToProcess:
				gameControls = mapGameControls(game)
				debugText(f'Creating xml for {game} ({gamesProcessed + 1}/{len(gamesToProcess)})...')
				# Open/Create CFG file
				mainXML = minidom.Document()
				cfgFile = f'{mameDir}{os.path.sep}cfg{os.path.sep}{game}.cfg'
				if os.path.isfile(cfgFile):
					try:
						mainXML = minidom.parse(configFile)
					except:
						pass
				xmlRoot = getRoot(mainXML, 'mameconfig')
				xmlRoot.setAttribute('version','10')
				xmlSystem = getSection(mainXML, xmlRoot, 'system')
				xmlSystem.setAttribute('name', game)
				removeSection(mainXML, xmlSystem, 'input')
				xmlInput = mainXML.createElement('input')
				xmlSystem.appendChild(xmlInput)
				for player in range(0, len(gameControls)):
					for control in gameControls[player].keys():
						debugText(control)
						if 'ANALOG_' in control:
							if digitalAnalog == 1:
								if 'UP' in control:
									for analogControl in ['PADDLE_V', 'POSITIONAL_V', 'DIAL_V', 'TRACKBALL_Y', 'AD_STICK_Y', 'LIGHTGUN_Y', 'MOUSE_Y']:
										xmlPort = mainXML.createElement('port')
										xmlPort.setAttribute('type', f'P{player + 1}_{analogControl}')
										xmlIncrement = mainXML.createElement('newseq')
										xmlIncrement.setAttribute('type', 'increment')
										xmlPort.appendChild(xmlIncrement)
										downData = mainXML.createTextNode(gameControls[player]['ANALOG_DOWN']['internalname'])
										xmlIncrement.appendChild(downData)
										xmlDecrement = mainXML.createElement('newseq')
										xmlDecrement.setAttribute('type', 'decrement')
										xmlPort.appendChild(xmlDecrement)
										upData = mainXML.createTextNode(gameControls[player]['ANALOG_UP']['internalname'])
										xmlDecrement.appendChild(upData)
										xmlInput.appendChild(xmlPort)
								if 'LEFT' in control:
									for analogControl in ['PADDLE', 'POSITIONAL', 'DIAL', 'TRACKBALL_X', 'AD_STICK_X', 'LIGHTGUN_X', 'MOUSE_X']:
										xmlPort = mainXML.createElement('port')
										xmlPort.setAttribute('type', f'P{player + 1}_{analogControl}')
										xmlIncrement = mainXML.createElement('newseq')
										xmlIncrement.setAttribute('type', 'increment')
										xmlPort.appendChild(xmlIncrement)
										rightData = mainXML.createTextNode(gameControls[player]['ANALOG_RIGHT']['internalname'])
										xmlIncrement.appendChild(rightData)
										xmlDecrement = mainXML.createElement('newseq')
										xmlDecrement.setAttribute('type', 'decrement')
										xmlPort.appendChild(xmlDecrement)
										leftData = mainXML.createTextNode(gameControls[player]['ANALOG_LEFT']['internalname'])
										xmlDecrement.appendChild(leftData)
										xmlInput.appendChild(xmlPort)
						elif 'FACE' not in control:
							if getIfExists(gameControls[player][control], 'mamemap', None) != None:
								xmlPort = mainXML.createElement('port')
								xmlPort.setAttribute('type', gameControls[player][control]['mamemap'])
								xmlNewseq = mainXML.createElement('newseq')
								xmlNewseq.setAttribute('type', 'standard')
								xmlPort.appendChild(xmlNewseq)
								inputData = mainXML.createTextNode(gameControls[player][control]['internalname'])
								xmlNewseq.appendChild(inputData)
								xmlInput.appendChild(xmlPort)
				finalXML = codecs.open(cfgFile, "w", "utf-8")
				cleanXML = os.linesep.join([s for s in mainXML.toprettyxml().splitlines() if s.strip()])
				finalXML.write(cleanXML)
				gamesProcessed += 1
				generationProgress.setValue(gamesProcessed)
				generationProgress.setLabelText(f'Generating cfg file {gamesProcessed}/{len(gamesToProcess)}')
				if generationProgress.wasCanceled():
					showMessage('Cancelled','Config file generation cancelled.')
					win.setEnabled(True)
					return
		generationProgress.setValue(len(gamesToProcess) + 1)
		win.setEnabled(True)
		if makeCtrlr:
			showMessage('Complete!', f'{mameDir}{os.path.sep}ctrlr{os.path.sep}{controllerTypes[selectedController]}.cfg created.')
		else:
			showMessage('Complete!', f'Config files created in {mameDir}{os.path.sep}cfg.')

def canWeRun(callingDialog):
	# Invalid option selected (and can't be ignored)
	if callingDialog.leftRadio[3].isChecked() and not callingDialog.leftRadio[3].isEnabled():
		return False
	if callingDialog.rightRadio[3].isChecked() and not callingDialog.rightRadio[3].isEnabled():
		return False

	# Bad MAME path
	if not os.path.isdir(mameDir):
		return False

	# No players selected
	if not (callingDialog.pCheck[0].isEnabled() or callingDialog.pCheck[1].isChecked() or
			callingDialog.pCheck[2].isEnabled() or callingDialog.pCheck[3].isChecked()):
		return False

	# Should be Ok otherwise
	return True

class customWindow(QDialog):
	def __init__(self):
		# Initialize GUI
		debugText('Custom file dialog launching.')
		super(customWindow, self).__init__()
		loadUi(f'{scriptDir}{os.path.sep}ui{os.path.sep}customConfig.ui', self)
		self.setWindowIcon(QIcon(f'{scriptDir}{os.path.sep}ui{os.path.sep}importicon.png'))
		self.connectSignalsSlots()
		self.okButton.setEnabled(False)

		self.controllerCombo.addItems(controllerTypes.keys())
		selectedIndex = self.controllerCombo.findText(selectedController)
		if selectedIndex > -1:
			self.controllerCombo.setCurrentIndex(selectedIndex)

	def connectSignalsSlots(self):
		self.loadButton = self.findChild(QPushButton, 'loadButton')
		self.loadButton.clicked.connect(self.loadCfg)
		self.cfgLabel = self.findChild(QLabel, 'cfgLabel')
		self.nameEdit = self.findChild(QLineEdit, 'nameEdit')
		self.nameEdit.textChanged.connect(self.checkIfReady)
		self.okButton = self.findChild(QPushButton, 'okButton')
		self.okButton.clicked.connect(self.okClicked)
		self.cancelButton = self.findChild(QPushButton, 'cancelButton')
		self.cancelButton.clicked.connect(self.cancelClicked)
		self.controllerCombo = self.controllerCombo
		debugText('Custom file signals connected.')

	def loadCfg(self, s):
		global sourceFile

		if mameDir != '':
			fileName = QFileDialog.getOpenFileName(
				self,
				"Load MAME cfg File",
				f'{mameDir}{os.path.sep}cfg{os.path.sep}',
				"Config File (*.cfg)"
			)
		else:
			fileName = QFileDialog.getOpenFileName(
				self,
				"Load MAME cfg File",
				scriptDir,
				"Config File (*.cfg)"
			)
		if os.path.isfile(fileName[0]):
			self.cfgLabel.setText(os.path.basename(fileName[0]))
			sourceFile = fileName[0]
			if len(self.nameEdit.text()) > 0 and not controllerTypeExists(self.nameEdit.text()) and not shortNameExists(self.nameEdit.text()):
				self.okButton.setEnabled(True)

	def checkIfReady(self, s):
		if len(self.nameEdit.text()) > 0 and not controllerTypeExists(self.nameEdit.text())and not shortNameExists(self.nameEdit.text()) and len(sourceFile) > 0:
			self.okButton.setEnabled(True)

	def okClicked(self, s):
		global selectedController

		controllerFile = f'{scriptDir}{os.path.sep}controllers{os.path.sep}{self.nameEdit.text()}'
		if os.path.isfile(controllerFile):
			response = showMessage('Overwrite?', f'{controllerFile} already exists, overwrite?', Qt.Icon.Question, Qt.StandardButton.Yes | Qt.StandardButton.No)
		if response == Qt.StandardButton.No:
			return
		xmlFile = open(sourceFile,'r')
		cfgData = xmltodict.parse(xmlFile.read())
		debugText(f'Loaded config file for parsing.\n{cfgData}')
		for mameInput in cfgData['mameconfig']['system']['input']['port']:
			if mameInput['@type'] == "P1_BUTTON1":
				debugText(f"Found button 1: {mameInput['newseq']}")
				if 'KEYCODE' in mameInput['newseq']['#text']:
					fileMode = 'kb'
				else:
					fileMode = 'joy'
				break
		newController = {}
		oldController = self.controllerCombo.text()
		newController['longname'] = self.nameEdit.text()
		newController['shortname'] = controllerTypes[oldController]
		newController['controls'] = {}
		debugText(f"Creating {newController['longname']} based on {newController['shortname']}...")
		# Load controls if not loaded.
		if len(controllerData) == 0:
			loadControllerData()
		for mameInput in cfgData['mameconfig']['system']['input']['port']:
			if fileMode == 'joy':
				newInput = mameInput['@type'][3:]
			else:
				newInput = mameInput['@type']
			newController['controls'][newInput] = {}
			inputList = mameInput['newseq']['#text'].split(' ')
			newInternalname = None
			for item in inputList:
				if item.startswith('JOYCODE_1_'):
					newInternalname = item[11:]
					break
				if item.startswith('KEYCODE_'):
					newInternalname = item
					break
			if newInternalname != None:
				newController['controls'][newInput]['internalname'] = newInternalname
				if newInput in oldController['controls']:
					newController['controls'][newInput]['friendlyname'] = getIfExists(newController['controls'][newInput], 'friendlyname')
		controllerJson = json.dumps(newController, indent=2)
		jsonFile = open(controllerFile,'w')
		jsonFile.write(str(controllerJson))
		jsonFile.close()
		showMessage('Done!', f'{controllerFile} created!')
		loadControllerTypes()
		selectedController = self.nameEdit.text()
		self.accept()

	def cancelClicked(self, s):
		self.reject()

def find_nth(sourceString, locateString, n):
    start = sourceString.find(locateString)
    while start >= 0 and n > 1:
        start = sourceString.find(locateString, start+len(locateString))
        n -= 1
    return start

def showMessage(title, text, icon=QMessageBox.Icon.Information, buttons=QMessageBox.StandardButton.Ok, modality=Qt.WindowModality.ApplicationModal):
	msgBox = QMessageBox()
	msgBox.setIcon(icon)
	msgBox.setText(text)
	msgBox.setWindowTitle(title)
	msgBox.setStandardButtons(buttons)
	msgBox.setWindowModality(modality)
	return msgBox.exec()

def loadControllerTypes():
	global controllerTypes

	controllerTypes = {}
	# Read all json files in the controllers folder, load the name/shortname
	controllerDir = f'{scriptDir}{os.path.sep}controllers{os.path.sep}'
	if os.path.isdir(controllerDir):
		for controllerFile in os.listdir(controllerDir):
			fullPath = os.path.join(controllerDir, controllerFile)
			if os.path.splitext(fullPath)[1] == '.json':
				with open(fullPath, 'r') as jsonFile:
					debugText(f'Loading controller data file {fullPath}...')
					controllerJson = json.loads(jsonFile.read())
				controllerTypes[controllerJson['longname']] = controllerJson['shortname']
	else:
		showMessage('Missing Folder', f'Folder {scriptDir}{os.path.sep}controllers{os.path.sep} could not be found.\nPlease reinstall MAMEMapper.', QMessageBox.Icon.Critical)
		sys.exit()

def loadGameData():
	# Load json containing a list of games, their controls, clones, and mappings.
	global gameData

	gameData = {}
	gameFile = f'{scriptDir}{os.path.sep}gamedata.json'
	if os.path.isfile(gameFile):
		lineCount = getLineCount(gameFile)
		currentLine = 0
		gameLoadProgress = QProgressDialog('Loading Game Data', None, 0, lineCount + 1)
		gameLoadProgress.setMinimumDuration(500)
		gameLoadProgress.setWindowModality(Qt.WindowModality.ApplicationModal)
		with open(gameFile, 'r') as jsonFile:
			debugText(f'Loading game data from {gameFile}...')
			gameData = json.loads(jsonFile.read())
			currentLine += 1
			gameLoadProgress.setValue(currentLine)
			debugText(f'{len(gameData)} games loaded.')
		for game in gameData.keys():
			if 'playercount' in gameData[game].keys():
				gameData[game]['playercount'] = int(gameData[game]['playercount'])
			if 'buttons' in gameData[game].keys():
				gameData[game]['buttons'] = int(gameData[game]['buttons'])
			if 'sticks' in gameData[game].keys():
				gameData[game]['sticks'] = int(gameData[game]['sticks'])
			for clone in gameData[game].keys():
				if clone not in notCloneKeys:
					if 'playercount' in gameData[game][clone].keys():
						gameData[game][clone]['playercount'] = int(gameData[game][clone]['playercount'])
					if 'buttons' in gameData[game][clone].keys():
						gameData[game][clone]['buttons'] = int(gameData[game][clone]['buttons'])
					if 'sticks' in gameData[game][clone].keys():
						gameData[game][clone]['sticks'] = int(gameData[game][clone]['sticks'])
					if 'lightgun' in gameData[game][clone].keys():
						gameData[game][clone]['lightgun'] = int(gameData[game][clone]['lightgun'])
		gameLoadProgress.setValue(lineCount + 1)
	else:
		showMessage('Missing File', f'File {gameFile} could not be found.\nPlease reinstall MAMEMapper or replace the data file.', QMessageBox.Icon.Critical)
		sys.exit()

def loadControllerData():
	global controllerData

	debugText(f'Loading controller details for {selectedController}...')
	# Load control defs from json
	if controllerTypes[selectedController].endswith('*'):
		controllerFile = f"{scriptDir}{os.path.sep}custom{os.path.sep}{selectedController}.json"
	else:
		controllerFile = f"{scriptDir}{os.path.sep}controllers{os.path.sep}{controllerTypes[selectedController]}.json"
	if not os.path.isfile(controllerFile):
		showMessage('Error loading controls',f'{controllerFile} does not exist.',QMessageBox.Icon.Critical)
		return
	controllerData = {}
	with open(controllerFile, 'r') as jsonFile:
		debugText(f'Loading custom controller data file {controllerFile}...')
		controllerData = json.loads(jsonFile.read())
	win.previewList.clear()

def loadMappingNames():
	global mappingTypes
	global applyMappings

	mappingTypes = {}
	# Read all json files in the mappings folder, load the name/shortname
	mappingDir = f'{scriptDir}{os.path.sep}mappings{os.path.sep}'
	if os.path.isdir(mappingDir):
		for mappingFile in os.listdir(mappingDir):
			fullPath = os.path.join(mappingDir, mappingFile)
			if os.path.splitext(fullPath)[1] == '.json':
				with open(fullPath, 'r') as jsonFile:
					debugText(f'Loading mapping data file {fullPath}...')
					mappingJson = json.loads(jsonFile.read())
					mappingTypes[mappingJson['longname']] = mappingJson['shortname']
		if len(applyMappings) == 0:
			for longName in mappingTypes:
				applyMappings.append(longName)
	else:
		showMessage('Missing Folder', f'Folder {scriptDir}{os.path.sep}mappings{os.path.sep} could not be found.\nPlease reinstall MAMEMapper.', QMessageBox.Icon.Critical)
		sys.exit

def loadMappingData(longName):
	global mappingData

	# Load data from a file
	shortName = mappingTypes[longName]
	if shortName in mappingData.keys():
		debugText(f'{longName} is already loaded, skipping.')
		return
	mappingFile = f'{scriptDir}{os.path.sep}mappings{os.path.sep}{shortName}.json'
	if not os.path.isfile(mappingFile):
		showMessage('Missing File', f'Mapping file {mappingFile} could not be found.\nPlease reinstall MAMEMapper.', QMessageBox.Icon.Critical)
		sys.exit
	with open(mappingFile, 'r') as jsonFile:
		debugText(f'Loading mapping data file {mappingFile}...')
		mappingData[shortName] = json.loads(jsonFile.read())

def generateRemapList():
	mappingShortNames = []
	if len(gameData) == 0:
		loadGameData()
	for mapping in applyMappings:
		mappingShortNames.append(mappingTypes[mapping])
	gameList = []
	debugText(f'Generating remap list based on: {applyMappings} ({mappingShortNames})')
	if 'Defaults' in applyMappings:
		gameList.append('default')
	for game in gameData.keys():
		if game not in gameList:
			if saveDefault == 1:
				gameList.append(game)
			else:
				debugText(f'Checking {game}...')
				if 'mappings' in gameData[game].keys():
					for mapping in gameData[game]['mappings']:
						if mapping in mappingShortNames:
							gameList.append(game)
				elif getIfExists(gameData[game], 'buttons') == 4 and neogeo and 'Neo Geo' in applyMappings:
					gameList.append(game)
				if remap4p and getIfExists(gameData[game], 'playercount') >= 3:
					gameList.append(game)
				if 'controls' in gameData[game].keys():
					if swapPrimary and getIfExists(gameData[game]['controls'], 'P1_BUTTON1') in ['Jump', 'A']:
						gameList.append(game)
				if singleButton and getIfExists(gameData[game], 'buttons') == 1:
					gameList.append(game)
			if not parentOnly:
				for clone in gameData[game].keys():
					if clone not in notCloneKeys:
						if saveDefault == 1:
							gameList.append(clone)
						else:
							debugText(f'Checking {game}/{clone}...')
							if 'mappings' in gameData[game][clone].keys():
								for mapping in gameData[game][clone]['mappings']:
									if mapping in mappingShortNames:
										gameList.append(clone)
							elif getIfExists(gameData[game][clone], 'buttons') == 4 and neogeo == 1 and 'Neo Geo' in applyMappings:
								gameList.append(clone)
							if remap4p and getIfExists(gameData[game][clone], 'playercount') >= 3:
								gameList.append(clone)
							if 'controls' in gameData[game][clone].keys():
								if swapPrimary and getIfExists(gameData[game][clone]['controls'], 'P1_BUTTON1') in ['Jump', 'A']:
									gameList.append(clone)
							if singleButton and getIfExists(gameData[game][clone], 'buttons') == 1:
								gameList.append(clone)
	# Clear duplicates if any
	gameList = list(dict.fromkeys(gameList))
	debugText(f'{len(gameList)} games found to process with current settings.')
	debugText(gameList)
	return gameList

def swapButtons(originalMapping, swapList):
	tempMapping = deepcopy(originalMapping)
	for swap in swapList:
		if swap in originalMapping.keys():
			debugText(f"Swapping {swap} to {swapList[swap]}")
			debugText(f"Before Swap: {tempMapping[swap]}")
			for key in originalMapping[swapList[swap]].keys():
				if key != 'mamemap':
					tempMapping[swap][key] = originalMapping[swapList[swap]][key]
			debugText(f"After Swap: {tempMapping[swap]}")
	return tempMapping

def mapGameControls(game):
	playerControls = []
	mappingShortNames = []
	gameDetails = findGame(game)
	hotkeyRight = {}
	debugText(gameDetails)
	# Load controls if not loaded.
	if len(controllerData) == 0:
		loadControllerData()
	# Load mapping files
	for longName in applyMappings:
		loadMappingData(longName)
		currentControls = deepcopy(controllerData['controls'])
		controllerID = controllerTypes[selectedController]
	for mapping in applyMappings:
		mappingShortNames.append(mappingTypes[mapping])
	# Default Controls
	if game == 'default' or 'mappings' not in gameDetails.keys():
		debugText('Setting default controls...')
		if controllerID in mappingData['default'].keys():
			currentControls = swapButtons(currentControls, mappingData['default'][controllerID])
		if f'{controllerID}-{buttonLayout}' in mappingData['default'].keys():
			currentControls = swapButtons(currentControls, mappingData['default'][f'{controllerID}-{buttonLayout}'])
	else:
		# Probably only one mapping per game, but leave the possibility for overlapping ones.
		for mapping in gameDetails['mappings']:
			if mapping in mappingShortNames:
				if controllerID in mappingData[mapping].keys():
					currentControls = swapButtons(currentControls, mappingData[mapping][controllerID])
				if f'{controllerID}-{buttonLayout}' in mappingData[mapping].keys():
					currentControls = swapButtons(currentControls, mappingData[mapping][f'{controllerID}-{buttonLayout}'])
		if 'mappings' not in gameDetails.keys() and neogeo == 1 and getIfExists(gameDetails, 'buttons') == 4 and 'Neo Geo' in applyMappings:
			currentControls = swapButtons(currentControls, mappingData['neogeo'][controllerID])
	# Copy controls to all selected players & add JOYCODE
	if game == 'default' or getIfExists(gameDetails, 'playercount') == None:
		maxPlayers = 4
	else:
		maxPlayers = getIfExists(gameDetails, 'playercount')
	if maxPlayers > 4:
		maxPlayers = 4
	debugText(f"Max Players for {game}: {maxPlayers}")
	for player in range(0, maxPlayers):
		if playerChecks[player]:
			debugText(f'Setting player {player + 1} controls...')
			if playerChecks[player]:
				if f'P{player + 1}_BUTTON1' in currentControls.keys():
					debugText('Keyboard or other multiplayer file found, stripping out current player only.')
					copyFrom = {}
					for control in currentControls.keys():
						if control.startswith(f'P{player+1}_'):
							copyFrom[control[3:]] = deepcopy(currentControls[control])
				else:
					playerControls.append(deepcopy(currentControls))
					copyFrom = deepcopy(currentControls)
				for control in playerControls[player].keys():
					if copyFrom[control]['internalname'].startswith('KEYCODE_'):
						debugText(f"Setting P{player + 1} {control} to {copyFrom[control]['internalname']}")
						playerControls[player][control]['internalname'] = f"{copyFrom[control]['internalname']}"
					else:
						debugText(f"Setting P{player + 1} {control} to JOYCODE_{player + 1}_{copyFrom[control]['internalname']}")
						playerControls[player][control]['internalname'] = f"JOYCODE_{player + 1}_{copyFrom[control]['internalname']}"
					if control in ['COIN', 'START']:
						playerControls[player][control]['mamemap'] = f"{control}{player + 1}"
					elif 'FACE' not in control and 'ANALOG_' not in control:
						playerControls[player][control]['mamemap'] = f"P{player + 1}_{control}"
					else:
						playerControls[player][control]['mamemap'] = ''
				if player == 0:
					if 'RIGHT' in playerControls[player].keys():
						hotkeyRight = deepcopy(playerControls[player]['RIGHT'])
					else:
						hotkeyRight = deepcopy(playerControls[player]['JOYSTICKLEFT_RIGHT'])
				debugText(f"Left stick mode = {leftStickMode}")
				match leftStickMode:
					# DPad + Left Stick
					case 1:
						for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
							lstickDir = f'JOYSTICKLEFT_{direction}'
							if direction in playerControls[player].keys() and lstickDir in playerControls[player].keys():
								combinedControl = f"{playerControls[player][direction]['internalname']} OR {playerControls[player][lstickDir]['internalname']}"
								combinedName = f"{playerControls[player][direction]['friendlyname']}/{playerControls[player][lstickDir]['friendlyname']}"
								debugText(f"Combining left stick controls: {combinedControl}, {combinedName}")
								playerControls[player][direction]['internalname'] = combinedControl
								playerControls[player][direction]['friendlyname'] = combinedName
								playerControls[player][lstickDir]['internalname'] = combinedControl
								playerControls[player][lstickDir]['friendlyname'] = combinedName
							elif direction not in playerControls[player].keys():
								playerControls[player][direction] = { 'friendlyname': playerControls[player][lstickDir]['friendlyname'], \
									'internalname': playerControls[player][lstickDir]['internalname'], 'mamemap': f"P{player + 1}_{direction}" }
							elif lstickDir not in playerControls[player].keys():
								playerControls[player][lstickDir] = { 'friendlyname': playerControls[player][direction]['friendlyname'], \
										'internalname': playerControls[player][direction]['internalname'], 'mamemap': f"P{player + 1}_{lstickDir}" }
					# DPad Only
					case 2:
						for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
							lstickDir = f'JOYSTICKLEFT_{direction}'
							# If there is no dpad defined in the controls, set directions to left stick
							if direction not in playerControls[player].keys():
								playerControls[player][direction] = { 'friendlyname': playerControls[player][lstickDir]['friendlyname'], \
									'internalname': playerControls[player][lstickDir]['internalname'], 'mamemap': f"P{player + 1}_{direction}" }
							else:
								# Otherwise, set left stick to dpad
								playerControls[player][lstickDir] = { 'friendlyname': playerControls[player][direction]['friendlyname'], \
										'internalname': playerControls[player][direction]['internalname'], 'mamemap': f"P{player + 1}_{lstickDir}" }
					# Left Analog Only
					case 3:
						for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
							lstickDir = f'JOYSTICKLEFT_{direction}'
							# If there is no left stick defined in the controls, set left stick to dpad
							if lstickDir not in playerControls[player].keys():
								playerControls[player][lstickDir] = { 'friendlyname': playerControls[player][direction]['friendlyname'], \
										'internalname': playerControls[player][direction]['internalname'], 'mamemap': f"P{player + 1}_{lstickDir}" }
							else:
								# Otherwise, set directions to left stick
								playerControls[player][direction] = { 'friendlyname': playerControls[player][lstickDir]['friendlyname'], \
									'internalname': playerControls[player][lstickDir]['internalname'], 'mamemap': f"P{player + 1}_{direction}" }
				match rightStickMode:
					# Right stick & face buttons
					case 1:
						for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
							rstickDir = f'JOYSTICKRIGHT_{direction}'
							faceDir = f'FACE{direction}'
							if faceDir in playerControls[player].keys() and rstickDir in playerControls[player].keys():
								combinedControl = f"{playerControls[player][faceDir]['internalname']} OR {playerControls[player][rstickDir]['internalname']}"
								combinedName = f"{playerControls[player][faceDir]['friendlyname']}/{playerControls[player][rstickDir]['friendlyname']}"
								debugText(f"Combining right stick controls: {combinedControl}, {combinedName}")
								playerControls[player][rstickDir]['internalname'] = combinedControl
								playerControls[player][rstickDir]['friendlyname'] = combinedName
							elif rstickDir not in playerControls[player].keys():
								playerControls[player][rstickDir] = { 'friendlyname': playerControls[player][faceDir]['friendlyname'], \
										'internalname': playerControls[player][faceDir]['internalname'], 'mamemap': f"P{player + 1}_{rstickDir}" }
					# Face buttons
					case 2:
						for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
							rstickDir = f'JOYSTICKRIGHT_{direction}'
							faceDir = f'FACE{direction}'
							if faceDir in playerControls[player].keys():
								playerControls[player][rstickDir] = { 'friendlyname': playerControls[player][faceDir]['friendlyname'], \
										'internalname': playerControls[player][faceDir]['internalname'], 'mamemap': f"P{player + 1}_{rstickDir}" }
					# Right stick
					case 3:
						for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
							rstickDir = f'JOYSTICKRIGHT_{direction}'
							faceDir = f'FACE{direction}'
							if rstickDir not in playerControls[player].keys():
								playerControls[player][rstickDir] = { 'friendlyname': playerControls[player][faceDir]['friendlyname'], \
										'internalname': playerControls[player][faceDir]['internalname'], 'mamemap': f"P{player + 1}_{rstickDir}" }
				if devButtons == 1:
					for button in range(1,11):
						playerControls[player][f'BUTTON{button}']['internalname'] = f"{playerControls[player][f'BUTTON{button}']['internalname']} OR GUNCODE{player + 1}_BUTTON{button} OR MOUSECODE{player + 1}_BUTTON{button}"
				if digitalAnalog == 1:
					for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
						if direction in copyFrom.keys():
							playerControls[player][f'ANALOG_{direction}'] = {}
							if 'KEYCODE_' not in copyFrom[direction]['internalname']:
								playerControls[player][f'ANALOG_{direction}']['internalname'] = f"JOYCODE_{player + 1}_{copyFrom[direction]['internalname']}"
							else:
								playerControls[player][f'ANALOG_{direction}']['internalname'] = copyFrom[direction]['internalname']
			else:
				playerControls.append({})

	# Map diagonals only
	if game != 'default' and 'mappings' in gameDetails.keys() and 'qbert' in gameDetails['mappings']:
		digitalDir = {}
		analogDir = {}
		for direction in [ 'UP', 'DOWN', 'LEFT', 'RIGHT']:
			if direction in copyFrom.keys():
				digitalDir[direction] = deepcopy(copyFrom[direction])
				if not digitalDir[direction]['internalname'].startswith('KEYCODE_'):
					digitalDir[direction]['internalname'] = f"JOYCODE_{player + 1}_{digitalDir[direction]['internalname']}"
			if f'JOYSTICKLEFT_{direction}' in copyFrom.keys():
				analogDir[direction] = deepcopy(copyFrom[f'JOYSTICKLEFT_{direction}'])
				if not analogDir[direction]['internalname'].startswith('KEYCODE_'):
					analogDir[direction]['internalname'] = f"JOYCODE_{player + 1}_{analogDir[direction]['internalname']}"
		if len(digitalDir) == 4 and len(analogDir) == 4:
			playerControls[player]['UP']['internalname'] = f"{digitalDir['UP']['internalname']} {digitalDir['RIGHT']['internalname']} OR {analogDir['UP']['internalname']} {analogDir['RIGHT']['internalname']}"
			playerControls[player]['RIGHT']['internalname'] = f"{digitalDir['DOWN']['internalname']} {digitalDir['RIGHT']['internalname']} OR {analogDir['DOWN']['internalname']} {analogDir['RIGHT']['internalname']}"
			playerControls[player]['DOWN']['internalname'] = f"{digitalDir['DOWN']['internalname']} {digitalDir['LEFT']['internalname']} OR {analogDir['DOWN']['internalname']} {analogDir['LEFT']['internalname']}"
			playerControls[player]['LEFT']['internalname'] = f"{digitalDir['UP']['internalname']} {digitalDir['LEFT']['internalname']} OR {analogDir['UP']['internalname']} {analogDir['LEFT']['internalname']}"
			playerControls[player]['UP']['friendlyname'] = f"{digitalDir['UP']['friendlyname']}&{digitalDir['RIGHT']['friendlyname']}/{analogDir['UP']['friendlyname']}&{analogDir['RIGHT']['friendlyname']}"
			playerControls[player]['RIGHT']['friendlyname'] = f"{digitalDir['DOWN']['friendlyname']}&{digitalDir['RIGHT']['friendlyname']}/{analogDir['DOWN']['friendlyname']}&{analogDir['RIGHT']['friendlyname']}"
			playerControls[player]['DOWN']['friendlyname'] = f"{digitalDir['DOWN']['friendlyname']}&{digitalDir['LEFT']['friendlyname']}/{analogDir['DOWN']['friendlyname']}&{analogDir['LEFT']['friendlyname']}"
			playerControls[player]['LEFT']['friendlyname'] = f"{digitalDir['UP']['friendlyname']}&{digitalDir['LEFT']['friendlyname']}/{analogDir['UP']['friendlyname']}&{analogDir['LEFT']['friendlyname']}"
		elif len(digitalDir) == 4:
			playerControls[player]['UP']['internalname'] = f"{digitalDir['UP']['internalname']} {digitalDir['RIGHT']['internalname']}"
			playerControls[player]['RIGHT']['internalname'] = f"{digitalDir['DOWN']['internalname']} {digitalDir['RIGHT']['internalname']}"
			playerControls[player]['DOWN']['internalname'] = f"{digitalDir['DOWN']['internalname']} {digitalDir['LEFT']['internalname']}"
			playerControls[player]['LEFT']['internalname'] = f"{digitalDir['UP']['internalname']} {digitalDir['LEFT']['internalname']}"
			playerControls[player]['UP']['friendlyname'] = f"{digitalDir['UP']['friendlyname']}&{digitalDir['RIGHT']['friendlyname']}"
			playerControls[player]['RIGHT']['friendlyname'] = f"{digitalDir['DOWN']['friendlyname']}&{digitalDir['RIGHT']['friendlyname']}"
			playerControls[player]['DOWN']['friendlyname'] = f"{digitalDir['DOWN']['friendlyname']}&{digitalDir['LEFT']['friendlyname']}"
			playerControls[player]['LEFT']['friendlyname'] = f"{digitalDir['UP']['friendlyname']}&{digitalDir['LEFT']['friendlyname']}"
		elif len(analogDir) == 4:
			playerControls[player]['UP']['internalname'] = f"{analogDir['UP']['internalname']} {analogDir['RIGHT']['internalname']}"
			playerControls[player]['RIGHT']['internalname'] = f"{analogDir['DOWN']['internalname']} {analogDir['RIGHT']['internalname']}"
			playerControls[player]['DOWN']['internalname'] = f"{analogDir['DOWN']['internalname']} {analogDir['LEFT']['internalname']}"
			playerControls[player]['LEFT']['internalname'] = f"{analogDir['UP']['internalname']} {analogDir['LEFT']['internalname']}"
			playerControls[player]['UP']['friendlyname'] = f"{analogDir['UP']['friendlyname']}&{analogDir['RIGHT']['friendlyname']}"
			playerControls[player]['RIGHT']['friendlyname'] = f"{analogDir['DOWN']['friendlyname']}&{analogDir['RIGHT']['friendlyname']}"
			playerControls[player]['DOWN']['friendlyname'] = f"{analogDir['DOWN']['friendlyname']}&{analogDir['LEFT']['friendlyname']}"
			playerControls[player]['LEFT']['friendlyname'] = f"{analogDir['UP']['friendlyname']}&{analogDir['LEFT']['friendlyname']}"

	# Cross-player left/right sticks - requires all controls to be set first.
	if sum(playerChecks) == 4 and leftStickMode == 4:
		stickSwap = deepcopy(playerControls)
		for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
			# P1: Left stick = P3 left stick, Right stick = P1 left stick
			stickSwap[0][f'JOYSTICKLEFT_{direction}'] = playerControls[2][f'JOYSTICKLEFT_{direction}']
			stickSwap[0][f'JOYSTICKRIGHT_{direction}'] = playerControls[0][f'JOYSTICKLEFT_{direction}']
			# P2: Left stick unchanged, right stick = P4 right stick
			stickSwap[1][f'JOYSTICKRIGHT_{direction}'] = playerControls[3][f'JOYSTICKLEFT_{direction}']
		for player in range (0, 4):
			playerControls[player] = stickSwap[player]
	if playerChecks[0] and playerChecks[1] and rightStickMode == 4:
		stickSwap = deepcopy(playerControls)
		for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
			# P1: right stick = P2 left stick
			stickSwap[0][f'JOYSTICKRIGHT_{direction}'] = playerControls[1][f'JOYSTICKLEFT_{direction}']
		for player in range (0, 4):
			playerControls[player] = stickSwap[player]

	# Map hotkeys (if checked and player 1 controls are selected)
	# Keep keyboard keys as alternates
	# Select + South = Menu
	# South = UI Select
	# Left stick controls = UI navigation
	# Select + Start = Cancel/Exit
	# Select + East = Reset
	# Select + West = Save State
	# Select + North = Load State
	# Select + L1 = Screenshot
	# Select + R1 = UI Toggle
	# Select + L2 = Toggle shaders
	# Select + R2 = Service button
	# Select + Right = Fast Forward
	if playerChecks[0] and hotkeyMode:
		# Make sure to use un-remapped controls for this.
		if 'P1_BUTTON1' in currentControls.keys():
			debugText('Keyboard or other multiplayer file found, stripping out current player only.')
			copyFrom = {}
			for control in currentControls.keys():
				if control.startswith(f'P1_'):
					hotkeyControls[control[3:]] = deepcopy(currentControls[control])
		else:
			hotkeyControls = deepcopy(controllerData['controls'])
		for control in hotkeyControls.keys():
			if 'KEYCODE_' not in hotkeyControls[control]['internalname']:
				hotkeyControls[control]['internalname'] = f"JOYCODE_1_{currentControls[control]['internalname']}"
			if control in ['COIN', 'START']:
				hotkeyControls[control]['mamemap'] = f"{control}1"
			elif 'FACE' not in control:
				hotkeyControls[control]['mamemap'] = f"P1_{control}"
			else:
				hotkeyControls[control]['mamemap'] = ''
		hotkeyButton = hotkeyControls['COIN']
		playerControls[0]['MENU'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON1']['internalname']} OR KEYCODE_TAB", \
			'mamemap': 'UI_CONFIGURE', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON1']['friendlyname']}"}
		playerControls[0]['UI SELECT'] = deepcopy(hotkeyControls['BUTTON1'])
		playerControls[0]['UI SELECT']['mamemap'] = 'UI_SELECT'
		playerControls[0]['UI SELECT']['internalname'] = f"{hotkeyControls['BUTTON1']['internalname']} OR KEYCODE_ENTER"
		playerControls[0]['CANCEL'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['START']['internalname']} OR KEYCODE_ESC", \
			'mamemap': 'UI_CANCEL', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['START']['friendlyname']}"}
		for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
			playerControls[0][f'UI {direction}'] = deepcopy(hotkeyControls[direction])
			playerControls[0][f'UI {direction}']['mamemap'] = f'UI_{direction}'
			playerControls[0][f'UI {direction}']['internalname'] = f"{hotkeyControls[direction]['internalname']} OR KEYCODE_{direction}"
		playerControls[0]['RESET'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON2']['internalname']} OR KEYCODE_F3", \
			'mamemap': 'UI_RESET_MACHINE', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON2']['friendlyname']}"}
		playerControls[0]['SCREENSHOT'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON5']['internalname']} OR KEYCODE_F12", \
			'mamemap': 'UI_RENDER_SNAP', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON5']['friendlyname']}"}
		playerControls[0]['TOGGLE UI'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON6']['internalname']} OR KEYCODE_SCRLOCK", \
			'mamemap': 'UI_TOGGLE_UI', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON6']['friendlyname']}"}
		playerControls[0]['TOGGLE SHADERS'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON7']['internalname']} OR KEYCODE_LALT KEYCODE_LCONTROL KEYCODE_F5", \
			'mamemap': 'POST_PROCESS', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON7']['friendlyname']}"}
		playerControls[0]['SERVICE BUTTON'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON8']['internalname']} OR KEYCODE_F2", \
			'mamemap': 'SERVICE', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON8']['friendlyname']}"}
		playerControls[0]['FAST FORWARD'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyRight['internalname']}", \
			'mamemap': 'UI_FAST_FORWARD', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyRight['friendlyname']}"}
		playerControls[0]['SAVE STATE'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON3']['internalname']} OR KEYCODE_LSHIFT KEYCODE_F7", \
			'mamemap': 'UI_SAVE_STATE', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON3']['friendlyname']}"}
		playerControls[0]['LOAD STATE'] = {'internalname': f"{hotkeyButton['internalname']} {hotkeyControls['BUTTON4']['internalname']} OR KEYCODE_F7", \
			'mamemap': 'UI_LOAD_STATE', 'friendlyname': f"{hotkeyButton['friendlyname']} + {hotkeyControls['BUTTON4']['friendlyname']}"}

	if game != 'default':
		if getIfExists(gameDetails, 'buttons') == 1 and singleButton  and controllerID in ['x360', 'sony']:
			# Duplicate Button 1 for single-button games
			for player in range(0, len(playerControls)):
				playerControls[player]['BUTTON1']['internalname'] = f"{playerControls[player]['BUTTON1']['internalname']} OR {playerControls[player]['BUTTON2']['internalname']}"
				playerControls[player]['BUTTON1']['friendlyname'] = f"{playerControls[player]['BUTTON1']['friendlyname']}/{playerControls[player]['BUTTON2']['friendlyname']}"
				playerControls[player]['BUTTON2'] = {}
		try:
			if getIfExists(gameDetails, 'buttons') >= 2 and swapPrimary and getIfExists(gameDetails['controls'], 'P1_BUTTON1') in ['Jump', 'A']:
				# Swap button 1 & button 2 for games with jump on button 2 and more than one button (ie TMNT).
				for player in range(0, len(playerControls)):
					debugText(f'Swapping jump button for player {player + 1}')
					playerControls[player] = swapButtons(playerControls[player], {'BUTTON1':'BUTTON2', 'BUTTON2':'BUTTON1'})
		except:
			debugText('No buttons in game data')
		try:
			if getIfExists(gameDetails, 'playercount') >= 3 and remap4p and sum(playerChecks) == 4:
				# Rearrange player locations for 1/2/3 (4 is the same for both cp layouts)
				swapControls = deepcopy(playerControls)
				swapControls[0] = swapPlayerNumbers(playerControls[2], 2, 0)
				swapControls[1] = swapPlayerNumbers(playerControls[0], 0, 1)
				swapControls[2] = swapPlayerNumbers(playerControls[1], 1, 2)
				playerControls = deepcopy(swapControls)
		except:
			debugText('No player number in game data or less than 4 players.')
	debugText(f'Controls after mapping:\n{playerControls}')
	return playerControls

def swapPlayerNumbers(controlDict, oldPlayer, newPlayer):
	for control in controlDict.keys():
		if getIfExists[controlDict[control], 'mamemap'] != None:
			controlDict[control]['mamemap'] = controlDict[control]['mamemap'].replace(f"P{oldPlayer + 1}", f"P{newPlayer + 1}")
			controlDict[control]['mamemap'] = controlDict[control]['mamemap'].replace(f"COIN{oldPlayer + 1}", f"COIN{newPlayer + 1}")
			controlDict[control]['mamemap'] = controlDict[control]['mamemap'].replace(f"START{oldPlayer + 1}", f"START{newPlayer + 1}")
	return controlDict

def findGame(romName):
	global cancelPressed

	if romName in gameData.keys():
		return gameData[romName]
	elif romName == 'default':
		return None
	else:
		for game in gameData.keys():
			if romName in gameData[game].keys():
				return gameData[game][romName]
	print(f'Error: Could not find {romName} in game DB!')
	cancelPressed = True
	return None

def controllerTypeExists(nameCheck):
	for controller in controllerTypes.keys():
		if nameCheck.casefold() == controller.casefold():
			return True
	return False

def shortNameExists(shortName):
	for controller in controllerTypes:
		if controller['shortname'].casefold() == shortName.casefold():
			return True
	return False

def controlInGame(gameData, control):
	debugText(f"Checking {gameData['description']} for {control}")
	if fnmatch.fnmatch(control['mamemap'], f'P?_*') and int(control['mamemap'][1]) > int(getIfExists(gameData, 'playercount', 4)):
		return False
	if (control['mamemap'].startswith('COIN') or control['mamemap'].startswith('START')) and int(control['mamemap'][-1]) > int(getIfExists(gameData, 'playercount', 4)):
		return False
	for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
		if fnmatch.fnmatch(control['mamemap'], f'P?_{direction}') and getIfExists(gameData, 'sticks', 1) != 1:
			return False
	if ('JOYSTICKLEFT_' in control['mamemap'] or 'JOYSTICKRIGHT_' in control['mamemap']) and getIfExists(gameData, 'sticks', 1) != 2:
		return False
	if 'BUTTON' in control['mamemap']:
		buttonCount = getIfExists(gameData, 'buttons', 12)
		if control['mamemap'].endswith('10'):
			buttonNum = 10
		else:
			buttonNum = int(control['mamemap'][-1])
		if buttonNum > buttonCount:
			return False
	if control['mamemap'] == '':
		return False
	return True

def getRoot(config, name):
    xml_section = config.getElementsByTagName(name)

    if len(xml_section) == 0:
        xml_section = config.createElement(name)
        config.appendChild(xml_section)
    else:
        xml_section = xml_section[0]

    return xml_section

def getSection(config, xml_root, name):
    xml_section = xml_root.getElementsByTagName(name)

    if len(xml_section) == 0:
        xml_section = config.createElement(name)
        xml_root.appendChild(xml_section)
    else:
        xml_section = xml_section[0]

    return xml_section

def removeSection(config, xml_root, name):
    xml_section = xml_root.getElementsByTagName(name)

    for i in range(0, len(xml_section)):
        old = xml_root.removeChild(xml_section[i])
        old.unlink()

def _count_generator(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)

def getLineCount(fileName):
	with open(fileName, 'rb') as fp:
	    c_generator = _count_generator(fp.raw.read)
	    # count each \n
	    count = sum(buffer.count(b'\n') for buffer in c_generator)
	    return count + 1

def saveConfig():
	config = configparser.ConfigParser()
	if mameDir != '' and os.path.isdir(mameDir):
		config['Paths'] = {}
		config['Paths']['MAME'] = mameDir
	config['Input'] = {}
	config['Input']['Controller'] = str(selectedController)
	config['Player'] = {}
	config['Player']['P1'] = str(playerChecks[0])
	config['Player']['P2'] = str(playerChecks[1])
	config['Player']['P3'] = str(playerChecks[2])
	config['Player']['P4'] = str(playerChecks[3])
	config['Advanced'] = {}
	config['Advanced']['buttonLayout'] = buttonLayout
	config['Advanced']['swapPrimary'] = str(swapPrimary)
	config['Advanced']['hotkeyMode'] = str(hotkeyMode)
	config['Advanced']['leftStickMode'] = str(leftStickMode)
	config['Advanced']['rightStickMode'] = str(rightStickMode)
	config['Advanced']['remap3124'] = str(remap4p)
	config['Advanced']['parentOnly'] = str(parentOnly)
	config['Advanced']['DoubleSingle'] = str(singleButton)
	config['Advanced']['applyMappings'] = json.dumps(applyMappings)
	config['Advanced']['makeCtrlr'] = str(makeCtrlr)
	config['Advanced']['saveDefault'] = str(saveDefault)
	config['Advanced']['mapDevices'] = str(mapDevices)
	config['Advanced']['addToINI'] = str(addToINI)
	config['Advanced']['devButtons'] = str(devButtons)
	config['Advanced']['digitalAnalog'] = str(digitalAnalog)
	config['Advanced']['neogeo'] = str(neogeo)
	config['INIGeneration'] = {}
	config['INIGeneration']['mixedScreens'] = str(mixedScreens)

	config['Devices'] = {}
	if len(inputDevices['joystick']) > 0:
		config['Devices']['Joystick'] = json.dumps(inputDevices['joystick'])
	if len(inputDevices['lightgun']) > 0:
		config['Devices']['Lightgun'] = json.dumps(inputDevices['lightgun'])
	if len(inputDevices['mouse']) > 0:
		config['Devices']['Mouse'] = json.dumps(inputDevices['mouse'])
	if len(inputDevices['keyboard']) > 0:
		config['Devices']['Keyboard'] = json.dumps(inputDevices['keyboard'])
	config['Fixed'] = {}
	if len(fixedDevices['joystick']) > 0:
		config['Fixed']['Joystick'] = json.dumps(fixedDevices['joystick'])
	if len(fixedDevices['lightgun']) > 0:
		config['Fixed']['Lightgun'] = json.dumps(fixedDevices['lightgun'])
	if len(fixedDevices['mouse']) > 0:
		config['Fixed']['Mouse'] = json.dumps(fixedDevices['mouse'])
	if len(fixedDevices['keyboard']) > 0:
		config['Fixed']['Keyboard'] = json.dumps(fixedDevices['keyboard'])

	with open(configFile, 'w') as writeConfig:
		config.write(writeConfig)

def getIfExists(checkDict, key, default=None):
	try:
		return checkDict[key]
	except:
		return default

def debugText(text):
	if printDebugMessages:
		print(text)
	with open(logFile, 'a', encoding='utf-8') as log:
	    log.write(f'{datetime.now().strftime("%H:%M:%S")} - {text}\n')

def usage():
	print('<MAMEMapper.py> -v verbose | -h help')

if __name__ == '__main__':
	global version
	global printDebugMessages
	global controllerTypes
	global mappingTypes
	global scriptDir
	global configFile
	global logFile
	global mameDir
	global sourceFile
	global selectedController
	global playerChecks
	global buttonLayout
	global swapPrimary
	global singleButton
	global hotkeyMode
	global leftStickMode
	global rightStickMode
	global remap4p
	global applyMappings
	global parentOnly
	global inputDevices
	global makeCtrlr
	global saveDefault
	global mapDevices
	global addToINI
	global devButtons
	global digitalAnalog
	global mixedScreens
	global neogeo

	global gameData
	global controllerData
	global mappingData
	global fixedDevices
	global controlEmoji
	global notCloneKeys

	version = 0.01
	printDebugMessages = False
	scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))

	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon(f'{scriptDir}{os.path.sep}ui{os.path.sep}icon.png'))

	try:
		opts, args = getopt.getopt(sys.argv[1:],'vh', ['verbose', 'help'])
	except getopt.GetoptError as err:
		print(err)
		usage()
		sys.exit(2)

	for o, a in opts:
		if o in ('-v', '--verbose'):
			printDebugMessages = True
		elif o in ['-h', '--help']:
			usage()
			sys.exit()

	sourceFile = ''
	controllerTypes = {}
	selectedController = ''
	mappingTypes = {}
	playerChecks = [1, 1, 1, 1]
	buttonLayout = 'SNES'
	swapPrimary = 1
	singleButton = 1
	hotkeyMode = 1
	leftStickMode = 1
	rightStickMode = 1
	remap4p = 0
	parentOnly = 0
	applyMappings = []
	gameData = {}
	controllerData = {}
	mappingData = {}
	makeCtrlr = 0
	saveDefault = 0
	mapDevices = 0
	addToINI = 0
	devButtons = 1
	digitalAnalog = 1
	mixedScreens = 1
	neogeo = 0
	inputDevices = { 'joystick': {}, 'lightgun': {}, 'keyboard': {}, 'mouse': {} }
	fixedDevices = { 'joystick': {}, 'lightgun': {}, 'keyboard': {}, 'mouse': {} }
	controlEmoji = { 'joystick': '\U0001F579', 'lightgun': '\U0001F52B', 'keyboard': '\U00002328', 'mouse': '\U0001F5B1', 'trackball': '\U0001F5B2', 'paddle': '\U0001F3D3', \
		'dial': '\U0001F55B', 'pedal': '\U0001F3CE', 'hanafuda': '\U0001F3B4', 'gambling': '\U0001F0CF', 'mahjong': '\U0001F004', 'button': '\U0001F534', 'unknown': '\U00002753' }
	notCloneKeys = ['description', 'playercount', 'buttons', 'sticks', 'pedals', 'dials', 'paddles', 'trackball', 'lightgun', 'mouse', 'mahjong', 'gambling', 'hanafuda', \
		'keyboard', 'mappings', 'unknown', 'controls']

	mameDir = ''
	configFile = f'{scriptDir}{os.path.sep}MAMEMapper.ini'
	logFile = f'{scriptDir}{os.path.sep}MAMEMapper.log'

	with open(logFile, 'w') as log:
	    log.write(f'MAMEMapper v{version} Log: Started {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}\n')

	if os.path.isfile(configFile):
		config = configparser.ConfigParser()
		config.sections()
		config.read(configFile)
		if 'Paths' in config:
			if os.path.isdir(config['Paths']['MAME']):
				mameDir = config['Paths']['MAME']
		if 'Input' in config:
			selectedController = config['Input']['Controller']
		if 'Player' in config:
			playerChecks[0] = int(config['Player']['P1'])
			playerChecks[1] = int(config['Player']['P2'])
			playerChecks[2] = int(config['Player']['P3'])
			playerChecks[3] = int(config['Player']['P4'])
		if 'Advanced' in config:
			if 'buttonLayout' in config['Advanced']:
				buttonLayout = config['Advanced']['buttonLayout']
			if 'swapPrimary' in config['Advanced']:
				swapPrimary = int(config['Advanced']['swapPrimary'])
			if 'hotkeyMode' in config['Advanced']:
				hotkeyMode = int(config['Advanced']['hotkeyMode'])
			if 'leftStickMode' in config['Advanced']:
				leftStickMode = int(config['Advanced']['leftStickMode'])
			if 'rightStickMode' in config['Advanced']:
				rightStickMode = int(config['Advanced']['rightStickMode'])
			if 'remap3124' in config['Advanced']:
				remap4p = int(config['Advanced']['remap3124'])
			if 'parentOnly' in config['Advanced']:
				parentOnly = int(config['Advanced']['parentOnly'])
			if 'applyMappings' in config['Advanced']:
				applyMappings = json.loads(config.get('Advanced','applyMappings'))
			if 'makeCtrlr' in config['Advanced']:
				makeCtrlr = int(config.get('Advanced','makeCtrlr'))
			if 'saveDefault' in config['Advanced']:
				saveDefault = int(config.get('Advanced','saveDefault'))
			if 'addToINI' in config['Advanced']:
				addToINI = int(config.get('Advanced','addToINI'))
			if 'mapDevices' in config['Advanced']:
				mapDevices = int(config.get('Advanced','mapDevices'))
			if 'devButtons' in config['Advanced']:
				devButtons = int(config.get('Advanced','devButtons'))
			if 'digitalAnalog' in config['Advanced']:
				digitalAnalog = int(config.get('Advanced','digitalAnalog'))
			if 'neogeo' in config['Advanced']:
				neogeo = int(config.get('Advanced','neogeo'))
		if 'INIGeneration' in config:
			if 'mixedScreens' in config['INIGeneration']:
				mixedScreens = int(config.get('INIGeneration','mixedScreens'))
		if 'Joystick' in config['Devices']:
			inputDevices['joystick'] = json.loads(config.get('Devices','Joystick'))
		elif platform.system() == 'Windows':
			for xinput in range(1, 5):
				inputDevices['joystick'][f'XInput Player {xinput}'] = {}
				inputDevices['joystick'][f'XInput Player {xinput}']['name'] = f'XInput Player {xinput}'
		if 'Lightgun' in config['Devices']:
			inputDevices['lightgun'] = json.loads(config.get('Devices','Lightgun'))
		if 'Mouse' in config['Devices']:
			inputDevices['mouse'] = json.loads(config.get('Devices','Mouse'))
		if 'Keyboard' in config['Devices']:
			inputDevices['keyboard'] = json.loads(config.get('Devices','Keyboard'))
		if 'Joystick' in config['Fixed']:
			fixedDevices['joystick'] = json.loads(config.get('Fixed','Joystick'))
		if 'Lightgun' in config['Fixed']:
			fixedDevices['lightgun'] = json.loads(config.get('Fixed','Lightgun'))
		if 'Mouse' in config['Fixed']:
			fixedDevices['mouse'] = json.loads(config.get('Fixed','Mouse'))
		if 'Keyboard' in config['Fixed']:
			fixedDevices['keyboard'] = json.loads(config.get('Fixed','Keyboard'))

	loadControllerTypes()
	loadMappingNames()

	win = mainWindow()
	win.show()
	saveConfig()
	sys.exit(app.exec())