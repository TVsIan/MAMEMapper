import sys
import os
import json
import csv
import subprocess
import time
import xmltodict
from copy import deepcopy as deepcopy
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import (
	QApplication, QDialog, QMessageBox, QPushButton, QFileDialog, QGroupBox, QProgressDialog
)
from PyQt6.uic import loadUi

try:
	from subprocess import DEVNULL
except ImportError:
	DEVNULL = open(os.devnull, 'wb')

class toolWindow(QDialog):
	def __init__(self):
		# Initialize GUI
		super(toolWindow, self).__init__()
		loadUi(f'{scriptDir}{os.path.sep}ui{os.path.sep}tools.ui', self)
		self.setWindowIcon(QIcon(f'{scriptDir}{os.path.sep}ui{os.path.sep}toolicon.png'))
		self.connectSignalsSlots()

	def connectSignalsSlots(self):
		# Connect button signals
		self.dumpXMLButton = self.findChild(QPushButton, 'dumpXMLButton')
		self.dumpXMLButton.clicked.connect(self.dumpMAMEXML)
		self.xmlButton = self.findChild(QPushButton, 'xmlButton')
		self.xmlButton.clicked.connect(self.loadXML)
		self.cloneButton = self.findChild(QPushButton, 'cloneButton')
		self.cloneButton.clicked.connect(self.loadClones)
		self.alternatingButton = self.findChild(QPushButton, 'alternatingButton')
		self.alternatingButton.clicked.connect(self.loadAlternating)
		self.controlButton = self.findChild(QPushButton, 'controlButton')
		self.controlButton.clicked.connect(self.loadControls)
		self.mappingButton = self.findChild(QPushButton, 'mappingButton')
		self.mappingButton.clicked.connect(self.addMappings)
		self.portsButton = self.findChild(QPushButton, 'portsButton')
		self.portsButton.clicked.connect(self.dumpPorts)
		self.validateButton = self.findChild(QPushButton, 'validateButton')
		self.validateButton.clicked.connect(self.validateData)
		self.mergeButton = self.findChild(QPushButton, 'mergeButton')
		self.mergeButton.clicked.connect(self.mergeData)
		self.buttonStatus()

	def dumpMAMEXML(self, s):
		# Create a mame.xml file
		# First select a mame.exe
		fileName = QFileDialog.getOpenFileName(
			self,
			"Locate MAME",
			scriptDir,
			"Executable File (*.exe)"
		)
		if not os.path.isfile(fileName[0]):
			showMessage('Error', 'You must select a MAME executable.', QMessageBox.Icon.Critical)
			return
		mameEXE = fileName[0]
		mameDir = os.path.dirname(mameEXE)
		dumpFile = f'{mameDir}{os.path.sep}mame.xml'
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		# Run the selected exe to dump the xml file to mame.xml in the same directory as the exe
		with open(dumpFile, 'w') as xmlDump:
			print(f'Dumping {mameEXE} to {dumpFile}...')
			subprocess.run([mameEXE, '-listxml'], stdout=xmlDump)
			print('Complete!')
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'MAME game data dumped to {dumpFile}')
		self.buttonStatus()

	def loadXML(self, s):
		# Load a mame.xml, create game list
		# Select the xml, can be a full or filtered xml
		fileName = QFileDialog.getOpenFileName(
			self,
			"Load mame.xml",
			scriptDir,
			"XML File (*.xml)"
		)
		if not os.path.isfile(fileName[0]):
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		# Start loading
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		cloneDB = {}
		# Max is temporary, will be overwritten once we know how many games are in the xml
		listLoadProgress = QProgressDialog('Loading Game Lists...', None, 0, 100)
		listLoadProgress.setMinimumDuration(0)
		listLoadProgress.setWindowTitle('Loading from XML')
		listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
		# Load existing game list if it exists - multiple mame.xmls can be merged in this way
		if os.path.isfile(cloneFile):
			with open(cloneFile) as savedClones:
				cloneDB = json.load(savedClones)
		if os.path.isfile(fileName[0]):
			xmlFile = open(fileName[0],'r')
			mameXML = xmltodict.parse(xmlFile.read())
			listLoadProgress.setMaximum(len(mameXML['mame']['machine']) + 1)
			# Load relevant parts of game data from the xml into a json
			for gameData in mameXML['mame']['machine']:
				print(f"Processing {gameData['@name']}")
				if '@runnable' not in gameData.keys() or gameData['@runnable'] != 'no':
					if '@cloneof' not in gameData.keys():
						currentGame = {}
						if 'description' not in currentGame.keys():
							currentGame['description'] = gameData['description']
							print(f"Adding description {gameData['description']}")
						if 'playercount' not in currentGame.keys():
							currentGame['playercount'] = gameData['input']['@players']
							print(f"Adding player count {gameData['input']['@players']}")
						# Checking controls, this will show icons in the MAMEMapper game list
						if 'control' in gameData['input'].keys():
							stickCount = 0
							pedalCount = 0
							paddleCount = 0
							dialCount = 0
							trackballCount = 0
							gunCount = 0
							mouseCount = 0
							mjCount = 0
							gamblingCount = 0
							hanafudaCount = 0
							keyboardCount = 0
							buttonCount = 0
							controlType = ''
							if type(gameData['input']['control']) == dict:
								if int(getIfExists(gameData['input']['control'], '@player', 1)) == 1:
									controlType = getIfExists(gameData['input']['control'], '@type', 'unknown')
									if int(getIfExists(gameData['input']['control'], '@buttons', 0)) > buttonCount:
										buttonCount = int(getIfExists(gameData['input']['control'], '@buttons', 0))
							elif type(gameData['input']['control']) == list:
								for controlData in gameData['input']['control']:
									if int(getIfExists(controlData, '@player', 1)) == 1:
										controlType = getIfExists(controlData, '@type')
										if int(getIfExists(controlData, '@buttons', 0)) > buttonCount:
											buttonCount = int(getIfExists(controlData, '@buttons', 0))
							match controlType:
								case 'only_buttons':
									stickCount = 0
								case 'joy' | 'stick':
									stickCount += 1
								case 'doublejoy':
									stickCount += 2
								case 'pedal':
									pedalCount =+ 1
								case 'paddle':
									paddleCount =+ 1
								case 'dial':
									dialCount =+ 1
								case 'trackball':
									trackballCount += 1
								case 'lightgun':
									gunCount += 1
								case 'positional' | 'mouse':
									mouseCount += 1
								case 'mahjong':
									mjCount += 1
								case 'gambling':
									gamblingCount += 1
								case 'hanafuda':
									hanafudaCount += 1
								case 'keyboard' | 'keypad':
									keyboardCount += 1
								case _:
									print(f"Unhandled control type: {controlData['@type']}")
									currentGame['unknown'] = '1'
							if buttonCount > 0:
								currentGame['buttons'] = str(buttonCount)
							if stickCount > 0:
								currentGame['sticks'] = str(stickCount)
							if paddleCount > 0:
								currentGame['paddles'] = str(paddleCount)
							if dialCount > 0:
								currentGame['dials'] = str(dialCount)
							if pedalCount > 0:
								currentGame['pedals'] = str(pedalCount)
							if trackballCount > 0:
								currentGame['trackball'] = str(trackballCount)
							if gunCount > 0:
								currentGame['lightgun'] = str(gunCount)
							if mouseCount > 0:
								currentGame['mouse'] = str(mouseCount)
							if mjCount > 0:
								currentGame['mahjong'] = str(mjCount)
							if gamblingCount > 0:
								currentGame['gambling'] = str(gamblingCount)
							if hanafudaCount > 0:
								currentGame['hanafuda'] = str(hanafudaCount)
							if keyboardCount > 0:
								currentGame['keyboard'] = str(keyboardCount)
						else:
							print(f"Controls not found for {gameData['@name']}, keys are: {gameData['input'].keys()}")
							currentGame['unknown'] = '1'
						# If it's new, add it. If it already exists, update data
						if gameData['@name'] not in cloneDB.keys():
							print(f"Adding {gameData['@name']} to parent list.")
							cloneDB[gameData['@name']] = currentGame
						else:
							cloneDB[gameData['@name']].update(currentGame)
					else:
						# Game is tagged as a clone, similar routine
						currentClone = {}
						if 'description' not in currentClone.keys():
							currentClone['description'] = gameData['description']
						if 'playercount' not in currentClone.keys():
							currentClone['playercount'] = gameData['input']['@players']
						if 'control' in gameData['input'].keys():
							stickCount = 0
							pedalCount = 0
							paddleCount = 0
							dialCount = 0
							trackballCount = 0
							gunCount = 0
							mouseCount = 0
							mjCount = 0
							gamblingCount = 0
							hanafudaCount = 0
							keyboardCount = 0
							buttonCount = 0
							controlType = ''
							if type(gameData['input']['control']) == dict:
								if int(getIfExists(gameData['input']['control'], '@player', 1)) == 1:
									controlType = getIfExists(gameData['input']['control'], '@type', 'unknown')
									if int(getIfExists(gameData['input']['control'], '@buttons', 0)) > buttonCount:
										buttonCount = int(getIfExists(gameData['input']['control'], '@buttons', 0))
							elif type(gameData['input']['control']) == list:
								for controlData in gameData['input']['control']:
									if int(getIfExists(controlData, '@player', 1)) == 1:
										controlType = getIfExists(controlData, '@type')
										if int(getIfExists(controlData, '@buttons', 0)) > buttonCount:
											buttonCount = int(getIfExists(controlData, '@buttons', 0))
							match controlType:
								case 'only_buttons':
									stickCount = 0
								case 'joy' | 'stick':
									stickCount += 1
								case 'doublejoy':
									stickCount += 2
								case 'pedal':
									pedalCount =+ 1
								case 'paddle':
									paddleCount =+ 1
								case 'dial':
									dialCount =+ 1
								case 'trackball':
									trackballCount += 1
								case 'lightgun':
									gunCount += 1
								case 'positional' | 'mouse':
									mouseCount += 1
								case 'mahjong':
									mjCount += 1
								case 'gambling':
									gamblingCount += 1
								case 'hanafuda':
									hanafudaCount += 1
								case 'keyboard' | 'keypad':
									keyboardCount += 1
								case _:
									print(f"Unhandled control type: {controlData['@type']}")
									currentClone['unknown'] = '1'
							if buttonCount > 0:
								currentClone['buttons'] = str(buttonCount)
							if stickCount > 0:
								currentClone['sticks'] = str(stickCount)
							if paddleCount > 0:
								currentClone['paddles'] = str(paddleCount)
							if dialCount > 0:
								currentClone['dials'] = str(dialCount)
							if pedalCount > 0:
								currentClone['pedals'] = str(pedalCount)
							if trackballCount > 0:
								currentClone['trackball'] = str(trackballCount)
							if gunCount > 0:
								currentClone['lightgun'] = str(gunCount)
							if mouseCount > 0:
								currentClone['mouse'] = str(mouseCount)
							if mjCount > 0:
								currentClone['mahjong'] = str(mjCount)
							if gamblingCount > 0:
								currentClone['gambling'] = str(gamblingCount)
							if hanafudaCount > 0:
								currentClone['hanafuda'] = str(hanafudaCount)
							if keyboardCount > 0:
								currentClone['keyboard'] = str(keyboardCount)
						else:
							print(f"Controls not found for {gameData['@name']}, keys are: {gameData['input'].keys()}")
							currentClone['unknown'] = '1'
						# If the parent game hasn't already been loaded, add a blank placeholder
						if gameData['@cloneof'] not in cloneDB.keys():
							print(f"Clone loaded before parent: Adding {gameData['@cloneof']} to parent list.")
							cloneDB[gameData['@cloneof']] = {}
						# Add a tag for the list of clones & their data
						if 'clones' not in cloneDB[gameData['@cloneof']].keys():
							cloneDB[gameData['@cloneof']]['clones'] = {}
						# Finally add or update the clone's entry
						if gameData['@name'] not in cloneDB[gameData['@cloneof']]['clones'].keys():
							print(f"Adding {gameData['@name']} as a clone of {gameData['@cloneof']}.")
							cloneDB[gameData['@cloneof']]['clones'][gameData['@name']] = currentClone
						else:
							cloneDB[gameData['@cloneof']]['clones'][gameData['@name']].update(currentClone)
				else:
					print("Not runnable!")
				listLoadProgress.setValue(listLoadProgress.value() + 1)
				listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {listLoadProgress.maximum()} Complete')
			# Save to file
			cloneJson = json.dumps(cloneDB, indent=2)
			if not os.path.isdir(f'{scriptDir}{os.path.sep}data{os.path.sep}'):
				os.makedirs(f'{scriptDir}{os.path.sep}data{os.path.sep}')
			jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
			jsonFile.write(str(cloneJson))
			jsonFile.close()
			listLoadProgress.cancel()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Parents and clones from {fileName} were added to gamedb.json')
		self.buttonStatus()

	def loadClones(self, s):
		# Load from a csv file, this can be instead of or in addition to the mame.xml, data will not be complete
		fileName = QFileDialog.getOpenFileName(
			self,
			"Load Arcade-Italia csv export",
			scriptDir,
			"Config File (*.csv)"
		)
		if not os.path.isfile(fileName[0]):
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		cloneDB = {}
		if os.path.isfile(cloneFile):
			with open(cloneFile) as savedClones:
				cloneDB = json.load(savedClones)
		if os.path.isfile(fileName[0]):
			with open(fileName[0], "rb") as file:
				lineCount = sum(1 for _ in file)
			listLoadProgress = QProgressDialog(f'0 / {lineCount} Complete', None, 0, lineCount)
			listLoadProgress.setMinimumDuration(0)
			listLoadProgress.setWindowTitle('Loading from csv')
			listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
			with open(fileName[0]) as dataFile:
				dataReader = csv.DictReader(dataFile, delimiter=';')
				for dataRow in dataReader:
					if 'cloneof' in dataRow.keys():
						if dataRow['cloneof'] == '-':
							if dataRow['name'] not in cloneDB.keys():
								print(f"Adding {dataRow['name']} to parent list.")
								cloneDB[dataRow['name']] = {}
							if 'description' not in cloneDB[dataRow['name']].keys():
								cloneDB[dataRow['name']]['description'] = dataRow['description']
						else:
							if dataRow['cloneof'] not in cloneDB.keys():
								cloneDB[dataRow['cloneof']] = {}
								cloneDB[dataRow['cloneof']]['clones'] = {}
								print(f"Adding {dataRow['cloneof']} to parent list.")
							if 'clones' not in cloneDB[dataRow['cloneof']].keys():
								cloneDB[dataRow['cloneof']]['clones'] = {}
							if dataRow['name'] not in cloneDB[dataRow['cloneof']]['clones'].keys():
								print(f"Adding {dataRow['name']} to clone list for {dataRow['cloneof']}.")
								cloneDB[dataRow['cloneof']]['clones'][dataRow['name']] = {}
								cloneDB[dataRow['cloneof']]['clones'][dataRow['name']]['description'] = dataRow['description']
								if 'players' in dataRow.keys():
									cloneDB[dataRow['cloneof']]['clones'][dataRow['name']]['playercount'] = dataRow['players']
								else:
									cloneDB[dataRow['cloneof']]['clones'][dataRow['name']]['playercount'] = cloneDB[dataRow['cloneof']]['playercount']
								if 'buttons' in dataRow.keys():
									cloneDB[dataRow['cloneof']]['clones'][dataRow['name']]['playercount'] = dataRow['buttons']
								else:
									cloneDB[dataRow['cloneof']]['clones'][dataRow['name']]['buttoncount'] = cloneDB[dataRow['cloneof']]['buttoncount']
				listLoadProgress.setValue(listLoadProgress.value() + 1)
				listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {listLoadProgress.maximum()} Complete')
			cloneJson = json.dumps(cloneDB, indent=2)
			if not os.path.isdir(f'{scriptDir}{os.path.sep}data{os.path.sep}'):
				os.makedirs(f'{scriptDir}{os.path.sep}data{os.path.sep}')
			jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
			jsonFile.write(str(cloneJson))
			jsonFile.close()
		listLoadProgress.cancel()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Parents and clones from {fileName} were added to gamedb.json')
		self.buttonStatus()

	def loadAlternating(self, s):
		altFileName = QFileDialog.getOpenFileName(
			self,
			"Load alternating games.xml",
			scriptDir,
			"XML File (*.xml)"
		)
		if not os.path.isfile(altFileName[0]):
			return
		conFileName = QFileDialog.getOpenFileName(
			self,
			"Load concurrent games.xml",
			scriptDir,
			"XML File (*.xml)"
		)
		if not os.path.isfile(conFileName[0]):
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		# Start loading
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		cloneDB = {}
		if os.path.isfile(cloneFile):
			with open(cloneFile) as savedClones:
				cloneDB = json.load(savedClones)
		# Max isn't fully accurate, not all games support multiplayer. Will jump ahead at the end.
		listLoadProgress = QProgressDialog('Loading Game Lists...', None, 0, len(cloneDB))
		listLoadProgress.setMinimumDuration(0)
		listLoadProgress.setWindowTitle('Loading from XML')
		listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
		altDB = {}
		conDB = []
		# Get info for games with ALTERNATING players
		if os.path.isfile(altFileName[0]):
			altXMLFile = open(altFileName[0],'r')
			altXML = xmltodict.parse(altXMLFile.read())
			# Load relevant parts of game data from the xml into a json
			for gameData in altXML['mame']['machine']:
				print(f"Processing {gameData['@name']}")
				if '@runnable' not in gameData.keys() or gameData['@runnable'] != 'no':
					if '@cloneof' not in gameData.keys():
						altDB[gameData['@name']] = gameData['@name']
					else:
						altDB[gameData['@name']] = gameData['@cloneof']
		else:
			return
		# Get info for games with CONCURRENT players
		if os.path.isfile(conFileName[0]):
			conXMLFile = open(conFileName[0],'r')
			conXML = xmltodict.parse(conXMLFile.read())
			# Load relevant parts of game data from the xml into a json
			for gameData in conXML['mame']['machine']:
				print(f"Processing {gameData['@name']}")
				if '@runnable' not in gameData.keys() or gameData['@runnable'] != 'no':
					conDB.append(gameData['@name'])
		else:
			return
		# Remove games that appear in BOTH lists, this will flag alternating-only games (generally a dip switch setting for play mode)
		# Some alternating games have P2 controls for cocktail tables that are unused for upright
		removeAlts = []
		for game in altDB.keys():
			if game in conDB:
				removeAlts.append(game)
		for game in removeAlts:
			altDB.pop(game)
		for game in altDB.keys():
			if altDB[game] == game and game in cloneDB.keys():
				cloneDB[game]['alternating'] = True
			elif altDB[game] in cloneDB.keys():
				if 'clones' not in cloneDB[altDB[game]].keys():
					cloneDB[altDB[game]]['clones'] = {}
				if game not in cloneDB[altDB[game]]['clones'].keys():
					cloneDB[altDB[game]]['clones'][game] = {}
				cloneDB[altDB[game]]['clones'][game]['alternating'] = True
			listLoadProgress.setValue(listLoadProgress.value() + 1)
			listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {listLoadProgress.maximum()} Complete')

		cloneJson = json.dumps(cloneDB, indent=2)
		if not os.path.isdir(f'{scriptDir}{os.path.sep}data{os.path.sep}'):
			os.makedirs(f'{scriptDir}{os.path.sep}data{os.path.sep}')
		jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
		jsonFile.write(str(cloneJson))
		jsonFile.close()
		listLoadProgress.cancel()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'{len(altDB)} alternating play-only games set in gamedb.json')
		self.buttonStatus()

	def loadControls(self, s):
		# Load controls.json - this is just control labels, it is used for the jump button standardization
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		cloneDB = {}
		controlDB = {}
		if not os.path.isfile(cloneFile):
			showMessage('Error', 'gamedb.json does not exist, please load games first.', QMessageBox.Icon.Critical)
			return
		fileName = QFileDialog.getOpenFileName(
			self,
			"Load controls.json file",
			scriptDir,
			"json file (*.json)"
		)
		if not os.path.isfile(fileName[0]):
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		with open(cloneFile) as savedClones:
			cloneDB = json.load(savedClones)
		with open(fileName[0], 'r') as controlFile:
			controlData = json.load(controlFile)
		listLoadProgress = QProgressDialog(f'0 / {len(controlData['games'])} Complete', None, 0, len(controlData['games']))
		listLoadProgress.setMinimumDuration(0)
		listLoadProgress.setWindowTitle('Loading from controls.json')
		listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
		for gameData in controlData['games']:
			currentGame = gameData['romname']
			controlDB[currentGame] = {}
			for playerData in gameData['players']:
				for labelData in playerData['labels']:
					controlDB[currentGame][labelData['name'].replace('_JOYSTICK_', '_')] = labelData['value']
			if currentGame not in cloneDB.keys():
				foundClone = recursiveFind(cloneDB, currentGame)
				if foundClone == None:
					foundGame = False
					for parentData in cloneDB.keys():
						if foundGame:
							break
						if cloneDB[parentData]['description'] == currentGame:
							print(f"Found {currentGame} as {gameData['gamename']}")
							controlDB[parentData] = controlDB.pop(currentGame)
							currentGame = parentData
							foundGame = True
							break
						else:
							if 'clones' in cloneDB[parentData].keys():
								for cloneData in cloneDB[parentData]['clones'].keys():
									if cloneDB[parentData]['clones'][cloneData]['description'] == gameData['gamename']:
										foundClone = cloneData
										parent = breadcrumb(cloneDB, foundClone)[0]
										print(f"Found {gameData['romname']} as a clone of {parent}, reassigning controls to parent.")
										controlDB[parent] = controlDB.pop(gameData['romname'])
										currentGame = parent
										foundGame = True
										break
					if not foundGame:
						print(f"Warning: {gameData['romname']} not found in clonedb, adding.")
						cloneDB[gameData['romname']] = {}
						cloneDB[gameData['romname']]['description'] = gameData['gamename']
				else:
					parent = breadcrumb(cloneDB, foundClone)[0]
					print(f"Found {gameData['romname']} as a clone of {parent}, reassigning controls to parent.")
					controlDB[parent] = controlDB.pop(gameData['romname'])
					currentGame = parent
			removeExts = {}
			for control in controlDB[currentGame].keys():
				if '_EXT' in control:
					if control[:-4] in controlDB[currentGame].keys():
						controlDB[currentGame][control[:-4]] = f'{controlDB[currentGame][control[:-4]]}/{controlDB[currentGame][control]}'
						if currentGame not in removeExts.keys():
							removeExts[currentGame] = []
						removeExts[currentGame].append(control)
					controlDB[currentGame][control] = controlDB[currentGame][control].title()
			if len(removeExts) > 0:
				for game in removeExts.keys():
					for control in removeExts[game]:
						controlDB[game].pop(control)
			listLoadProgress.setValue(listLoadProgress.value() + 1)
			listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {listLoadProgress.maximum()} Complete')
		controlJson = json.dumps(controlDB, indent=2)
		jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}controldb.json','w')
		jsonFile.write(str(controlJson))
		jsonFile.close()
		cloneJson = json.dumps(cloneDB, indent=2)
		jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
		jsonFile.write(str(cloneJson))
		jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		listLoadProgress.cancel()
		showMessage('Complete', f'Control data from {fileName} was converted to controldb.xml')
		self.buttonStatus()

	def addMappings(self, s):
		# Loads the list of custom mapping files.
		# Reads the json files that determine the final buttom mapping, loads a matching csv file from the datasources folder, and creates lists of applicable mappings.
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		mappingDir = f'{scriptDir}{os.path.sep}mappings{os.path.sep}'
		csvDir = f'{scriptDir}{os.path.sep}datasources{os.path.sep}'
		cloneDB = {}
		controlDB = {}
		if not os.path.isfile(cloneFile):
			showMessage('Error', 'gamedb.json does not exist, please load games first.', QMessageBox.Icon.Critical)
			return
		if not os.path.isdir(mappingDir):
			showMessage('Error', f'{mappingDir} does not exist, please create and add json files.', QMessageBox.Icon.Critical)
			return
		if not os.path.isdir(csvDir):
			showMessage('Error', f'{csvDir} does not exist, please create and add csv files.', QMessageBox.Icon.Critical)
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		with open(cloneFile) as savedClones:
			cloneDB = json.load(savedClones)
			mappingTypes = {}
		listLoadProgress = QProgressDialog(f'0 / {len(os.listdir(mappingDir))} Complete', None, 0, len(os.listdir(mappingDir)))
		listLoadProgress.setMinimumDuration(0)
		listLoadProgress.setWindowTitle('Loading mapping definitions from jsons')
		listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
		for mappingFile in os.listdir(mappingDir):
			fullPath = os.path.join(mappingDir, mappingFile)
			if os.path.splitext(fullPath)[1] == '.json':
				with open(fullPath, 'r') as jsonFile:
					print(f'Loading mapping data file {fullPath}...')
					mappingJson = json.loads(jsonFile.read())
					if len(mappingJson['shortname']) > 0 and mappingJson['shortname'] != 'default':
						csvFile = f"{csvDir}{mappingJson['shortname']}.csv"
						print(f'Loading csv data file {csvFile}...')
						if os.path.isfile(csvFile):
							with open(csvFile) as dataFile:
								dataReader = csv.DictReader(dataFile, delimiter=';')
								for dataRow in dataReader:
									if dataRow['name'] != 'name':
										if dataRow['cloneof'] == '-':
											if dataRow['name'] not in cloneDB.keys():
												print(f"Adding {dataRow['name']} to parent list.")
												cloneDB[dataRow['name']] = {}
											if 'description' not in cloneDB[dataRow['name']].keys():
												cloneDB[dataRow['name']]['description'] = dataRow['description']
											if 'mappings' not in cloneDB[dataRow['name']].keys():
												cloneDB[dataRow['name']]['mappings'] = []
											if mappingJson['shortname'] not in cloneDB[dataRow['name']]['mappings']:
												cloneDB[dataRow['name']]['mappings'].append(mappingJson['shortname'])
										else:
											if dataRow['cloneof'] not in cloneDB.keys():
												cloneDB[dataRow['cloneof']] = {}
												print(f"Adding {dataRow['cloneof']} to parent list.")
											if dataRow['name'] not in cloneDB[dataRow['cloneof']]['clones'].keys():
												print(f"Adding {dataRow['name']} to clone list for {dataRow['cloneof']}.")
												cloneDB[dataRow['cloneof']]['clone'][dataRow['name']] = {}
											if 'description' not in cloneDB[dataRow['cloneof']]['clones'][dataRow['name']].keys():
												cloneDB[dataRow['cloneof']][dataRow['name']]['clones']['description'] = dataRow['description']
											if 'mappings' not in cloneDB[dataRow['cloneof']]['clones'][dataRow['name']].keys():
												cloneDB[dataRow['cloneof']][dataRow['name']]['clones']['mappings'] = []
											if mappingJson['shortname'] not in cloneDB[dataRow['cloneof']]['clones'][dataRow['name']]['mappings']:
												cloneDB[dataRow['cloneof']]['clones'][dataRow['name']]['mappings'].append(mappingJson['shortname'])
			listLoadProgress.setValue(listLoadProgress.value() + 1)
			listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {listLoadProgress.maximum()} Complete')
		cloneJson = json.dumps(cloneDB, indent=2)
		if not os.path.isdir(f'{scriptDir}{os.path.sep}data{os.path.sep}'):
			os.makedirs(f'{scriptDir}{os.path.sep}data{os.path.sep}')
		jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
		jsonFile.write(str(cloneJson))
		jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Mappings for parents and clones were added to gamedb.json')
		self.buttonStatus()

	def dumpPorts(self, s):
		fileName = QFileDialog.getOpenFileName(
			self,
			"Locate MAME",
			scriptDir,
			"Executable File (*.exe)"
		)
		if not os.path.isfile(fileName[0]):
			showMessage('Error', 'You must select a MAME executable.', QMessageBox.Icon.Critical)
			return
		mameEXE = fileName[0]
		mameDir = os.path.dirname(mameEXE)
		dumpScript = f'{scriptDir}{os.path.sep}datasources{os.path.sep}portdumper.lua'
		dumpedAlready = f'{scriptDir}{os.path.sep}data{os.path.sep}portdb.json'
		dumpFile = f'{mameDir}{os.path.sep}ports.json'
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		dumpLog = f'{scriptDir}{os.path.sep}dump.log'
		portDB = {}
		cloneDB = {}
		if not os.path.isfile(cloneFile):
			showMessage('Error', 'gamedb.json does not exist, please load games first.', QMessageBox.Icon.Critical)
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		with open(cloneFile) as savedClones:
			cloneDB = json.load(savedClones)
		if os.path.isfile(dumpedAlready):
			with open(dumpedAlready) as dumpedPorts:
				print(f'Loading {dumpedAlready}...')
				portDB = json.load(dumpedPorts)
		dumpSize = len(cloneDB) + cloneCount(cloneDB) - len(portDB)
		listLoadProgress = QProgressDialog(f'0 / {dumpSize} Complete', 'Cancel & Save Progress', 0, dumpSize + 1)
		print(f'Total to dump: {dumpSize}: {len(cloneDB)} Parents, {cloneCount(cloneDB)} Clones, {len(portDB)} already dumped.')
		listLoadProgress.setMinimumDuration(0)
		listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
		listLoadProgress.setWindowTitle('Dumping Progress')
		listLoadProgress.forceShow()
		os.chdir(mameDir)
		for system in cloneDB.keys():
			if system not in portDB.keys():
				print(f'Preparing to dump {system}...')
				if os.path.isfile(dumpFile):
					os.remove(dumpFile)
				args = [mameEXE, system, '-autoboot_script', dumpScript, '-window', '-nomaximize', '-str', '120']
				subprocess.call(args, stdout=DEVNULL)
				if os.path.isfile(dumpFile):
					latestPort = {}
					with open(dumpFile) as lastDump:
						latestPort = json.load(lastDump)
					if system in latestPort.keys():
						portDB[system] = latestPort[system]
						with open(dumpedAlready, 'w') as dumpedPorts:
							dumpedPorts.write(str(json.dumps(portDB, indent=2)))
							print(f'Ports for {system} saved.')
					else:
						with open(dumpLog, "a") as logFile:
							logFile.write(f'Unable to dump {system} (not found in file)')
							print(f'Unable to dump {system} (not found in file)')
				else:
					with open(dumpLog, "a") as logFile:
						logFile.write(f'Unable to dump {system} (no dump file)')
						print(f'Unable to dump {system} (no dump file)')
				listLoadProgress.setValue(listLoadProgress.value() + 1)
				listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {dumpSize} Complete')
			if 'clones' in cloneDB[system].keys():
				for clone in cloneDB[system]['clones'].keys():
					if clone not in portDB.keys():
						if os.path.isfile(dumpFile):
							os.remove(dumpFile)
						if clone not in ['description', 'playercount', 'buttons', 'sticks', 'pedals', 'dials', 'paddles', 'trackball', \
							'lightgun', 'mouse', 'mahjong', 'gambling', 'hanafuda', 'keyboard', 'mappings', 'unknown', 'controls']:
							print(f'Preparing to dump {clone}...')
							if os.path.isfile(dumpFile):
								os.remove(dumpFile)
							args = [mameEXE, clone, '-autoboot_script', dumpScript, '-window', '-nomaximize', '-str', '120']
							subprocess.call(args, stdout=DEVNULL)
							if os.path.isfile(dumpFile):
								latestPort = {}
								with open(dumpFile) as lastDump:
									latestPort = json.load(lastDump)
								if clone in latestPort.keys():
									portDB[clone] = latestPort[clone]
									with open(dumpedAlready, 'w') as dumpedPorts:
										dumpedPorts.write(str(json.dumps(portDB, indent=2)))
										print(f'Ports for {clone} saved.')
								else:
									with open(dumpLog, "a") as logFile:
										logFile.write(f'Unable to dump {clone} (not found in file)')
										print(f'Unable to dump {clone} (not found in file)')
							else:
								with open(dumpLog, "a") as logFile:
									logFile.write(f'Unable to dump {clone} (no dump file')
									print(f'Unable to dump {clone} (no dump file')
						listLoadProgress.setValue(listLoadProgress.value() + 1)
						listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {dumpSize} Complete')
			# Brief delay to allow the cancel button to work, it is nonresponsive during the MAME process.
			loopTime = time.perf_counter_ns() + 2500
			while time.perf_counter_ns() < loopTime:
				app.processEvents()
				if listLoadProgress.wasCanceled():
					os.chdir(scriptDir)
					self.setCursor(Qt.CursorShape.ArrowCursor)
					showMessage('Cancelled', f'Partial ports were dumped to portdb.json.')
					self.buttonStatus()
					return
		os.chdir(scriptDir)
		self.setCursor(Qt.CursorShape.ArrowCursor)
		listLoadProgress.cancel()
		showMessage('Complete', f'Ports were dumped to portdb.json.')
		self.buttonStatus()

	def validateData(self, s):
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		controlFile = f'{scriptDir}{os.path.sep}data{os.path.sep}controldb.json'
		portsFile = f'{scriptDir}{os.path.sep}data{os.path.sep}portdb.json'
		cloneDB = {}
		controlDB = {}
		portDB = {}
		if not os.path.isfile(cloneFile):
			showMessage('Error', 'gamedb.json does not exist, please load games first.', QMessageBox.Icon.Critical)
			return
		if not os.path.isfile(controlFile):
			showMessage('Error', 'controldb.json does not exist, please load controls first.', QMessageBox.Icon.Critical)
			return
		if not os.path.isfile(portsFile):
			showMessage('Error', 'portdb.json does not exist, please dump ports first.', QMessageBox.Icon.Critical)
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		with open(cloneFile) as savedClones:
			cloneDB = json.load(savedClones)
		with open(controlFile) as savedControls:
			controlDB = json.load(savedControls)
		with open(portsFile) as savedPorts:
			portDB = json.load(savedPorts)
		listLoadProgress = QProgressDialog(f'0 / {len(cloneDB)} Complete', 'Cancel', 0, len(cloneDB) + 1)
		listLoadProgress.setMinimumDuration(0)
		listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
		listLoadProgress.setWindowTitle('Validation Progress')
		listLoadProgress.forceShow()
		missingPorts = []
		fixPorts = []
		missingLabels = []
		fixLabels = []
		for parent in cloneDB.keys():
			if parent not in portDB.keys():
				fixable = False
				if 'clones' in cloneDB[parent].keys():
					for portCheck in cloneDB[parent]['clones'].keys():
						if portCheck in portDB.keys():
							portDB[parent] = deepcopy(portDB[portCheck])
							fixable = True
							break
				if fixable:
					fixPorts.append(parent)
				else:
					missingPorts.append(parent)
			if parent not in controlDB.keys():
				fixable = False
				if 'clones' in cloneDB[parent].keys():
					for labelCheck in cloneDB[parent]['clones'].keys():
						if labelCheck in controlDB.keys():
							controlDB[parent] = deepcopy(controlDB[labelCheck])
							fixable = True
							break
				if fixable:
					fixLabels.append(parent)
				else:
					missingLabels.append(parent)
			listLoadProgress.setValue(listLoadProgress.value() + 1)
			listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {len(cloneDB)} Complete')
		print(f'Missing Port Data (unmappable, will use defaults): {", ".join(missingPorts)}')
		print(f'Corrected Port Data (Copied from clone, may be inaccurate): {", ".join(fixPorts)}')
		print(f'Missing Control Labels (mappable, jump swap will not work): {", ".join(missingLabels)}')
		print(f'Corrected Label Data (Copied from clone, may be inaccurate): {", ".join(fixLabels)}')
		if len(fixPorts) > 0:
			portsJson = json.dumps(portDB, indent=2)
			jsonFile = open(portsFile,'w')
			jsonFile.write(str(portJson))
			jsonFile.close()
		if len(fixLabels) > 0:
			controlJson = json.dumps(controlDB, indent=2)
			jsonFile = open(controlFile,'w')
			jsonFile.write(str(controlJson))
			jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		listLoadProgress.cancel()
		showMessage('Complete', f'See console for details.\nUnmappable games will not be added during merge.')
		self.buttonStatus()
		return

	def mergeData(self, s):
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		controlFile = f'{scriptDir}{os.path.sep}data{os.path.sep}controldb.json'
		portsFile = f'{scriptDir}{os.path.sep}data{os.path.sep}portdb.json'
		mergedFile = f'{scriptDir}{os.path.sep}gamedata.json'
		cloneDB = {}
		controlDB = {}
		if not os.path.isfile(controlFile):
			showMessage('Error', 'controldb.json does not exist, please load controls first.', QMessageBox.Icon.Critical)
			return
		if not os.path.isfile(cloneFile):
			showMessage('Error', 'gamedb.json does not exist, please load games first.', QMessageBox.Icon.Critical)
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		if not os.path.isfile(cloneFile):
			showMessage('Error', 'gamedb.json does not exist, please load games first.', QMessageBox.Icon.Critical)
			return
		if not os.path.isfile(controlFile):
			showMessage('Error', 'controldb.json does not exist, please load controls first.', QMessageBox.Icon.Critical)
			return
		if not os.path.isfile(portsFile):
			showMessage('Error', 'portdb.json does not exist, please dump ports first.', QMessageBox.Icon.Critical)
			return
		self.setCursor(Qt.CursorShape.WaitCursor)
		self.update()
		with open(cloneFile) as savedClones:
			cloneDB = json.load(savedClones)
		with open(controlFile) as savedControls:
			controlDB = json.load(savedControls)
		with open(portsFile) as savedPorts:
			portDB = json.load(savedPorts)
		totalRuns = len(cloneDB) + len(controlDB) + len(portDB)
		listLoadProgress = QProgressDialog(f'0 / {totalRuns} Complete', 'Cancel', 0, totalRuns + 2)
		listLoadProgress.setMinimumDuration(0)
		listLoadProgress.setWindowModality(Qt.WindowModality.WindowModal)
		listLoadProgress.setWindowTitle('Merge Progress')
		listLoadProgress.forceShow()
		removeWhenDone = []
		# Add Controls
		for controlEntry in controlDB.keys():
			if controlEntry in cloneDB.keys():
				if 'controls' not in cloneDB[controlEntry].keys():
					cloneDB[controlEntry]['controls'] = {}
				for inputData in controlDB[controlEntry]:
					if inputData not in cloneDB[controlEntry]['controls'].keys():
						cloneDB[controlEntry]['controls'][inputData] = {}
					cloneDB[controlEntry]['controls'][inputData]['name'] = controlDB[controlEntry][inputData]
			else:
				if recursiveFind(cloneDB, controlEntry) != None:
					parent = breadcrumb(cloneDB, controlEntry)[0]
					if 'controls' not in cloneDB[parent].keys():
						cloneDB[parent]['controls'] = {}
					for inputData in controlDB[controlEntry]:
						if inputData not in cloneDB[controlEntry]['controls'].keys():
							cloneDB[parent]['controls'][inputData] = {}
						cloneDB[parent]['controls'][inputData]['name'] = controlDB[controlEntry][inputData]
			listLoadProgress.setValue(listLoadProgress.value() + 1)
			listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {totalRuns} Complete')
			if listLoadProgress.wasCanceled():
				os.chdir(scriptDir)
				self.setCursor(Qt.CursorShape.ArrowCursor)
				showMessage('Cancelled', 'Data not merged.')
				self.buttonStatus()
				return
		for portEntry in portDB.keys():
			if portEntry in cloneDB.keys():
				if 'controls' not in cloneDB[portEntry].keys():
					cloneDB[portEntry]['controls'] = {}
				for portData in portDB[portEntry].keys():
					if portData not in cloneDB[portEntry]['controls'].keys():
						cloneDB[portEntry]['controls'][portData] = {}
					cloneDB[portEntry]['controls'][portData]['tag'] = portDB[portEntry][portData]['tag']
					cloneDB[portEntry]['controls'][portData]['mask'] = portDB[portEntry][portData]['mask']
			else:
				if recursiveFind(cloneDB, portEntry) != None:
					parent = breadcrumb(cloneDB, portEntry)[0]
					if 'controls' not in cloneDB[parent].keys():
						cloneDB[parent]['controls'] = {}
					for portData in portDB[parent].keys():
						if portData not in cloneDB[parent]['controls']:
							cloneDB[parent]['controls'][portData] = {}
						cloneDB[parent]['controls'][portData]['tag'] = portDB[parent][portData]['tag']
						cloneDB[parent]['controls'][portData]['mask'] = portDB[parent][portData]['mask']
					if 'controls' not in cloneDB[parent]['clones'][portEntry].keys():
						cloneDB[parent]['clones'][portEntry]['controls'] = {}
					for portData in portDB[portEntry].keys():
						if portData not in cloneDB[parent]['clones'][portEntry]['controls'].keys():
							cloneDB[parent]['clones'][portEntry]['controls'][portData] = {}
						cloneDB[parent]['clones'][portEntry]['controls'][portData]['tag'] = portDB[portEntry][portData]['tag']
						cloneDB[parent]['clones'][portEntry]['controls'][portData]['mask'] = portDB[portEntry][portData]['mask']
			listLoadProgress.setValue(listLoadProgress.value() + 1)
			listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {totalRuns} Complete')
			if listLoadProgress.wasCanceled():
				os.chdir(scriptDir)
				self.setCursor(Qt.CursorShape.ArrowCursor)
				showMessage('Cancelled', 'Data not merged.')
				self.buttonStatus()
				return
		removeGames = []
		removeControls = {}
		for parent in cloneDB.keys():
			removeControls[parent] = []
			# Make sure port data exists for all controls
			if 'controls' not in cloneDB[parent].keys() or len(cloneDB[parent]['controls'].keys()) == 0:
				removeGames.append(parent)
			else:
				for control in cloneDB[parent]['controls'].keys():
					if 'tag' not in cloneDB[parent]['controls'][control].keys() or 'mask'not in cloneDB[parent]['controls'][control].keys():
						removeControls[parent].append(control)
				# Copy missing entries from parent to clones if they don't exist.
				if 'clones' in cloneDB[parent].keys():
					for clone in cloneDB[parent]['clones'].keys():
						for key in cloneDB[parent].keys():
							if key not in cloneDB[parent]['clones'][clone].keys() and key != 'clones':
								cloneDB[parent]['clones'][clone][key] = deepcopy(cloneDB[parent][key])
						for control in cloneDB[parent]['controls'].keys():
							if control not in cloneDB[parent]['clones'][clone]['controls'].keys():
								cloneDB[parent]['clones'][clone]['controls'][control] = deepcopy(cloneDB[parent]['controls'][control])
							if 'name' not in cloneDB[parent]['clones'][clone]['controls'][control].keys() and 'name' in cloneDB[parent]['controls'][control].keys():
								cloneDB[parent]['clones'][clone]['controls'][control]['name'] = cloneDB[parent]['controls'][control]['name']
			listLoadProgress.setValue(listLoadProgress.value() + 1)
			listLoadProgress.setLabelText(f'{listLoadProgress.value()} / {totalRuns} Complete')
			if listLoadProgress.wasCanceled():
				os.chdir(scriptDir)
				self.setCursor(Qt.CursorShape.ArrowCursor)
				showMessage('Cancelled', 'Data not merged.')
				self.buttonStatus()
				return
		for noControls in removeGames:
			cloneDB.pop(noControls)
		for noPorts in removeControls.keys():
			if noPorts not in removeGames:
				for control in removeControls[noPorts]:
					cloneDB[noPorts]['controls'].pop(control)
				if len(cloneDB[noPorts]['controls']) == 0:
					cloneDB.pop(noPorts)

		cloneJson = json.dumps(cloneDB, indent=2)
		jsonFile = open(mergedFile,'w')
		jsonFile.write(str(cloneJson))
		jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		listLoadProgress.cancel()
		showMessage('Complete', f'Game data & control data merged to {mergedFile}')

	def buttonStatus(self):
		gameDB = os.path.isfile(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json')
		controlDB = os.path.isfile(f'{scriptDir}{os.path.sep}data{os.path.sep}controldb.json')
		portDB = os.path.isfile(f'{scriptDir}{os.path.sep}data{os.path.sep}portdb.json')
		if not gameDB:
			self.mappingButton.setEnabled(False)
			self.alternatingButton.setEnabled(False)
			self.controlButton.setEnabled(False)
			self.portsButton.setEnabled(False)
			self.validateButton.setEnabled(False)
			self.mergeButton.setEnabled(False)
		elif gameDB and controlDB and portDB:
			self.mappingButton.setEnabled(True)
			self.alternatingButton.setEnabled(True)
			self.controlButton.setEnabled(True)
			self.portsButton.setEnabled(True)
			self.validateButton.setEnabled(True)
			self.mergeButton.setEnabled(True)
		else:
			self.mappingButton.setEnabled(True)
			self.alternatingButton.setEnabled(True)
			self.controlButton.setEnabled(True)
			self.portsButton.setEnabled(True)
			self.validateButton.setEnabled(False)
			self.mergeButton.setEnabled(False)

def recursiveFind(search_dict, field):
    if isinstance(search_dict, dict):
        if field in search_dict:
            return search_dict[field]
        for key in search_dict:
            item = recursiveFind(search_dict[key], field)
            if item is not None:
                return item
    elif isinstance(search_dict, list):
        for element in search_dict:
            item = recursiveFind(element, field)
            if item is not None:
                return item
    return None

def breadcrumb(nested_dict, value):
    if nested_dict == value:
        return [nested_dict]
    elif isinstance(nested_dict, dict):
        for k, v in nested_dict.items():
            if k == value:
                return [k]
            p = breadcrumb(v, value)
            if p:
                return [k] + p
    elif isinstance(nested_dict, list):
        lst = nested_dict
        for i in range(len(lst)):
            p = breadcrumb(lst[i], value)
            if p:
                return p

def showMessage(title, text, icon=QMessageBox.Icon.Information, buttons=QMessageBox.StandardButton.Ok):
	msgBox = QMessageBox()
	msgBox.setIcon(icon)
	msgBox.setText(text)
	msgBox.setWindowTitle(title)
	msgBox.setStandardButtons(buttons)
	return msgBox.exec()

def getIfExists(checkDict, key, default=None):
	try:
		return checkDict[key]
	except:
		return default

def cloneCount(gameDB):
	total = 0
	for game in gameDB.keys():
		if 'clones' in gameDB[game].keys():
			total += len(gameDB[game]['clones'].keys())
	return total

if __name__ == '__main__':
	global scriptDir

	scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon(f'{scriptDir}{os.path.sep}ui{os.path.sep}toolicon.png'))
	win = toolWindow()
	win.show()
	sys.exit(app.exec())