import sys
import os
import json
import csv

import xmltodict
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import (
	QApplication, QDialog, QMessageBox, QPushButton, QFileDialog, QGroupBox
)
from PyQt6.uic import loadUi

class toolWindow(QDialog):
	def __init__(self):
		# Initialize GUI
		super(toolWindow, self).__init__()
		loadUi(f'{scriptDir}{os.path.sep}ui{os.path.sep}tools.ui', self)
		self.setWindowIcon(QIcon(f'{scriptDir}{os.path.sep}ui{os.path.sep}toolicon.png'))
		self.connectSignalsSlots()

	def connectSignalsSlots(self):
		self.xmlButton = self.findChild(QPushButton, 'xmlButton')
		self.xmlButton.clicked.connect(self.loadXML)
		self.cloneButton = self.findChild(QPushButton, 'cloneButton')
		self.cloneButton.clicked.connect(self.loadClones)
		self.controlButton = self.findChild(QPushButton, 'controlButton')
		self.controlButton.clicked.connect(self.loadControls)
		self.mappingButton = self.findChild(QPushButton, 'mappingButton')
		self.mappingButton.clicked.connect(self.addMappings)
		self.mergeButton = self.findChild(QPushButton, 'mergeButton')
		self.mergeButton.clicked.connect(self.mergeData)

	def loadXML(self, s):
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
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		cloneDB = {}
		if os.path.isfile(cloneFile):
			with open(cloneFile) as savedClones:
				cloneDB = json.load(savedClones)
		if os.path.isfile(fileName[0]):
			xmlFile = open(fileName[0],'r')
			mameXML = xmltodict.parse(xmlFile.read())
			for gameData in mameXML['mame']['machine']:
				print(f"Processing {gameData['@name']}")
				if '@runnable' not in gameData.keys() or gameData['@runnable'] != 'no':
					if '@cloneof' not in gameData.keys():
						if gameData['@name'] not in cloneDB.keys():
							print(f"Adding {gameData['@name']} to parent list.")
							cloneDB[gameData['@name']] = {}
						if 'description' not in cloneDB[gameData['@name']].keys():
							cloneDB[gameData['@name']]['description'] = gameData['description']
							print(f"Adding description {gameData['description']}")
						if 'playercount' not in cloneDB[gameData['@name']].keys():
							cloneDB[gameData['@name']]['playercount'] = gameData['input']['@players']
							print(f"Adding player count {gameData['input']['@players']}")
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
									cloneDB[gameData['@name']]['unknown'] = '1'
							if buttonCount > 0:
								cloneDB[gameData['@name']]['buttons'] = str(buttonCount)
							if stickCount > 0:
								cloneDB[gameData['@name']]['sticks'] = str(stickCount)
							if paddleCount > 0:
								cloneDB[gameData['@name']]['paddles'] = str(paddleCount)
							if dialCount > 0:
								cloneDB[gameData['@name']]['dials'] = str(dialCount)
							if pedalCount > 0:
								cloneDB[gameData['@name']]['pedals'] = str(pedalCount)
							if trackballCount > 0:
								cloneDB[gameData['@name']]['trackball'] = str(trackballCount)
							if gunCount > 0:
								cloneDB[gameData['@name']]['lightgun'] = str(gunCount)
							if mouseCount > 0:
								cloneDB[gameData['@name']]['mouse'] = str(mouseCount)
							if mjCount > 0:
								cloneDB[gameData['@name']]['mahjong'] = str(mjCount)
							if gamblingCount > 0:
								cloneDB[gameData['@name']]['gambling'] = str(gamblingCount)
							if hanafudaCount > 0:
								cloneDB[gameData['@name']]['hanafuda'] = str(hanafudaCount)
							if keyboardCount > 0:
								cloneDB[gameData['@name']]['keyboard'] = str(keyboardCount)
						else:
							print(f"Controls not found for {gameData['@name']}, keys are: {gameData['input'].keys()}")
							cloneDB[gameData['@name']]['unknown'] = '1'
					else:
						if gameData['@cloneof'] not in cloneDB.keys():
							print(f"Clone loaded before parent: Adding {gameData['@cloneof']} to parent list.")
							cloneDB[gameData['@cloneof']] = {}
						if gameData['@name'] not in cloneDB[gameData['@cloneof']].keys():
							print(f"Adding {gameData['@name']} as a clone of {gameData['@cloneof']}.")
							cloneDB[gameData['@cloneof']][gameData['@name']] = {}
						if 'description' not in cloneDB[gameData['@cloneof']][gameData['@name']].keys():
							cloneDB[gameData['@cloneof']][gameData['@name']]['description'] = gameData['description']
						if 'playercount' not in cloneDB[gameData['@cloneof']][gameData['@name']].keys():
							cloneDB[gameData['@cloneof']][gameData['@name']]['playercount'] = gameData['input']['@players']
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
									cloneDB[gameData['@cloneof']][gameData['@name']]['unknown'] = '1'
							if buttonCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['buttons'] = str(buttonCount)
							if stickCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['sticks'] = str(stickCount)
							if paddleCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['paddles'] = str(paddleCount)
							if dialCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['dials'] = str(dialCount)
							if pedalCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['pedals'] = str(pedalCount)
							if trackballCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['trackball'] = str(trackballCount)
							if gunCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['lightgun'] = str(gunCount)
							if mouseCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['mouse'] = str(mouseCount)
							if mjCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['mahjong'] = str(mjCount)
							if gamblingCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['gambling'] = str(gamblingCount)
							if hanafudaCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['hanafuda'] = str(hanafudaCount)
							if keyboardCount > 0:
								cloneDB[gameData['@cloneof']][gameData['@name']]['keyboard'] = str(keyboardCount)
						else:
							print(f"Controls not found for {gameData['@name']}, keys are: {gameData['input'].keys()}")
							cloneDB[gameData['@cloneof']][gameData['@name']]['unknown'] = '1'
				else:
					print("Not runnable!")
			cloneJson = json.dumps(cloneDB, indent=2)
			if not os.path.isdir(f'{scriptDir}{os.path.sep}data{os.path.sep}'):
				os.makedirs(f'{scriptDir}{os.path.sep}data{os.path.sep}')
			jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
			jsonFile.write(str(cloneJson))
			jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Parents and clones from {fileName} were added to gamedb.json')

	def loadClones(self, s):
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
								print(f"Adding {dataRow['cloneof']} to parent list.")
							elif dataRow['name'] not in cloneDB[dataRow['cloneof']].keys():
								print(f"Adding {dataRow['name']} to clone list for {dataRow['cloneof']}.")
								cloneDB[dataRow['cloneof']][dataRow['name']] = {}
								cloneDB[dataRow['cloneof']][dataRow['name']]['description'] = dataRow['description']
								if 'players' in dataRow.keys():
									cloneDB[dataRow['cloneof']][dataRow['name']]['playercount'] = dataRow['players']
								else:
									cloneDB[dataRow['cloneof']][dataRow['name']]['playercount'] = cloneDB[dataRow['cloneof']]['playercount']
								if 'buttons' in dataRow.keys():
									cloneDB[dataRow['cloneof']][dataRow['name']]['playercount'] = dataRow['buttons']
								else:
									cloneDB[dataRow['cloneof']][dataRow['name']]['buttoncount'] = cloneDB[dataRow['cloneof']]['buttoncount']
			cloneJson = json.dumps(cloneDB, indent=2)
			if not os.path.isdir(f'{scriptDir}{os.path.sep}data{os.path.sep}'):
				os.makedirs(f'{scriptDir}{os.path.sep}data{os.path.sep}')
			jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
			jsonFile.write(str(cloneJson))
			jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Parents and clones from {fileName} were added to gamedb.json')

	def loadControls(self, s):
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
		for gameData in controlData['games']:
			controlDB[gameData['romname']] = {}
			for playerData in gameData['players']:
				for labelData in playerData['labels']:
					controlDB[gameData['romname']][labelData['name'].replace('_JOYSTICK_', '_')] = labelData['value']
			if gameData['romname'] not in cloneDB.keys():
				foundClone = recursiveFind(cloneDB, gameData['romname'])
				if foundClone == None:
					foundGame = False
					for parentData in cloneDB:
						if foundGame:
							break
						if cloneDB[parentData]['description'] == gameData['gamename']:
							print(f"Found {gameData['romname']} as {gameData['gamename']}")
							controlDB[parentData] = controlDB.pop(gameData['romname'])
							foundGame = True
							break
						else:
							for cloneData in cloneDB[parentData].keys():
								if cloneData not in ['description', 'playercount', 'buttons', 'sticks', 'pedals', 'dials', 'paddles', 'trackball', \
									'lightgun', 'mouse', 'mahjong', 'gambling', 'hanafuda', 'keyboard', 'mappings', 'unknown']:
									print(f'Looking for {cloneData} in tags.')
									if cloneDB[parentData][cloneData]['description'] == gameData['gamename']:
										foundClone = cloneData
										parent = breadcrumb(cloneDB, foundClone)[0]
										print(f"Found {gameData['romname']} as a clone of {parent}, reassigning controls to parent.")
										controlDB[parent] = controlDB.pop(gameData['romname'])
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
					controlDB[gameData['gamename']] = controlDB.pop(parent)
		controlJson = json.dumps(controlDB, indent=2)
		jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}controldb.json','w')
		jsonFile.write(str(controlJson))
		jsonFile.close()
		cloneJson = json.dumps(cloneDB, indent=2)
		jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
		jsonFile.write(str(cloneJson))
		jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Control data from {fileName} was converted to controldb.xml')

	def addMappings(self, s):
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
											if dataRow['name'] not in cloneDB[dataRow['cloneof']].keys():
												print(f"Adding {dataRow['name']} to clone list for {dataRow['cloneof']}.")
												cloneDB[dataRow['cloneof']][dataRow['name']] = {}
											if 'description' not in cloneDB[dataRow['cloneof']][dataRow['name']].keys():
												cloneDB[dataRow['cloneof']][dataRow['name']]['description'] = dataRow['description']
											if dataRow['name'] not in cloneDB[dataRow['cloneof']].keys():
												showMessage('Error', f"{dataRow['cloneof']}/{dataRow['name']} is not in the game list, please add a csv that contains it.", QMessageBox.Icon.Critical)
												self.setCursor(Qt.CursorShape.ArrowCursor)
												return
											if 'mappings' not in cloneDB[dataRow['cloneof']][dataRow['name']].keys():
												cloneDB[dataRow['cloneof']][dataRow['name']]['mappings'] = []
											if mappingJson['shortname'] not in cloneDB[dataRow['cloneof']][dataRow['name']]['mappings']:
												cloneDB[dataRow['cloneof']][dataRow['name']]['mappings'].append(mappingJson['shortname'])
		cloneJson = json.dumps(cloneDB, indent=2)
		if not os.path.isdir(f'{scriptDir}{os.path.sep}data{os.path.sep}'):
			os.makedirs(f'{scriptDir}{os.path.sep}data{os.path.sep}')
		jsonFile = open(f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json','w')
		jsonFile.write(str(cloneJson))
		jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Mappings for parents and clones were added to gamedb.json')

	def mergeData(self, s):
		cloneFile = f'{scriptDir}{os.path.sep}data{os.path.sep}gamedb.json'
		controlFile = f'{scriptDir}{os.path.sep}data{os.path.sep}controldb.json'
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
		with open(cloneFile) as savedClones:
			cloneDB = json.load(savedClones)
		with open(controlFile) as controlFile:
			controlDB = json.load(controlFile)
		for controlEntry in controlDB:
			if controlEntry in cloneDB.keys():
				if 'controls' not in cloneDB[controlEntry].keys():
					cloneDB[controlEntry]['controls'] = {}
				for inputData in controlDB[controlEntry]:
					cloneDB[controlEntry]['controls'][inputData] = controlDB[controlEntry][inputData]
			else:
				if recursiveFind(cloneDB, controlEntry) != None:
					parent = breadcrumb(cloneDB, controlEntry)[0]
					if 'controls' not in cloneDB[parent].keys():
						cloneDB[parent]['controls'] = {}
					for inputData in controlDB[controlEntry]:
						cloneDB[parent]['controls'][inputData] = controlDB[controlEntry][inputData]
		for parent in cloneDB.keys():
			for clone in cloneDB[parent].keys():
				if clone not in ['description', 'playercount', 'buttons', 'sticks', 'pedals', 'dials', 'paddles', 'trackball', \
					'lightgun', 'mouse', 'mahjong', 'gambling', 'hanafuda', 'keyboard', 'mappings', 'unknown', 'controls']:
						for key in ['playercount', 'buttons', 'sticks', 'pedals', 'dials', 'paddles', 'trackball', 'lightgun', \
							'mouse', 'mahjong', 'gambling', 'hanafuda', 'keyboard', 'unknown', 'controls']:
							if key in cloneDB[parent].keys() and key not in cloneDB[parent][clone].keys():
								cloneDB[parent][clone][key] = cloneDB[parent][key]
		cloneJson = json.dumps(cloneDB, indent=2)
		jsonFile = open(mergedFile,'w')
		jsonFile.write(str(cloneJson))
		jsonFile.close()
		self.setCursor(Qt.CursorShape.ArrowCursor)
		showMessage('Complete', f'Game data & control data merged to {mergedFile}')

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

if __name__ == '__main__':
	global scriptDir

	scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon(f'{scriptDir}{os.path.sep}ui{os.path.sep}toolicon.png'))
	win = toolWindow()
	win.show()
	sys.exit(app.exec())