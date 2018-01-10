
import xbmc, xbmcgui
import sys
import helper, util, launcher
from util import *
from gamedatabase import *



ACTION_CANCEL_DIALOG = (9, 10, 51, 92, 110)
ACTION_MOVEMENT_LEFT = (1,)
ACTION_MOVEMENT_RIGHT = (2,)
ACTION_MOVEMENT_UP = (3,)
ACTION_MOVEMENT_DOWN = (4,)
ACTION_MOVEMENT = (1, 2, 3, 4,)

CONTROL_BUTTON_PLAYGAME = 3000
CONTROL_BUTTON_PLAYVIDEO = 3001

CONTROL_GAME_LIST_GROUP = 1000
CONTROL_GAME_LIST = 59

CONTROL_LABEL_MSG = 4000

RCBHOME = util.getAddonInstallPath()


class UIGameInfoView(xbmcgui.WindowXMLDialog):

	__useRefactoredView = False

	def __init__(self, *args, **kwargs):
		xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

		Logutil.log("Init GameInfoView", util.LOG_LEVEL_INFO)

		self.gdb = kwargs[ "gdb" ]
		self.selectedGameId = kwargs[ "gameId" ]
		self.selectedGame = kwargs[ "listItem" ]
		self.config = kwargs["config"]
		self.settings = kwargs["settings"]
		self.selectedConsoleId = kwargs[ "consoleId" ]
		self.selectedGenreId = kwargs[ "genreId" ]
		self.selectedYearId = kwargs[ "yearId" ]
		self.selectedPublisherId = kwargs[ "publisherId" ]
		self.selectedConsoleIndex = kwargs[ "consoleIndex" ]
		self.selectedGenreIndex = kwargs[ "genreIndex" ]
		self.selectedYearIndex = kwargs[ "yearIndex" ]
		self.selectedPublisherIndex = kwargs[ "publisherIndex" ]
		self.selectedCharacter = kwargs[ "selectedCharacter" ]
		self.selectedCharacterIndex = kwargs[ "selectedCharacterIndex" ]
		self.selectedGameIndex = kwargs[ "selectedGameIndex" ]
		self.selectedControlIdMainView = kwargs["controlIdMainView"]
		self.fileDict = kwargs["fileDict"]
		self.fileTypeGameplay = kwargs["fileTypeGameplay"]

		self.doModal()


	def onInit(self):

		Logutil.log("Begin OnInit", util.LOG_LEVEL_INFO)

		self.showGameList()

		control = self.getControlById(CONTROL_BUTTON_PLAYVIDEO)
		if(control != None and xbmc.getCondVisibility("Control.IsVisible(%i)" % CONTROL_BUTTON_PLAYVIDEO)):
			xbmc.sleep(util.WAITTIME_UPDATECONTROLS)
			self.setFocus(control)
		else:
			control = self.getControlById(CONTROL_BUTTON_PLAYGAME)
			if(control != None):
				self.setFocus(control)

		xbmc.sleep(util.WAITTIME_UPDATECONTROLS)
		self.showGameInfo()

		Logutil.log("End OnInit", util.LOG_LEVEL_INFO)


	def onClick(self, controlId):
		Logutil.log("Begin onClick", util.LOG_LEVEL_DEBUG)

		if (controlId == CONTROL_BUTTON_PLAYGAME):
			self.launchEmu()

		Logutil.log("End onClick", util.LOG_LEVEL_DEBUG)


	def onFocus(self, controlId):
		Logutil.log("onFocus", util.LOG_LEVEL_DEBUG)
		self.selectedControlId = controlId

	def onAction(self, action):

		if(action.getId() in ACTION_CANCEL_DIALOG):
			Logutil.log("onAction exit", util.LOG_LEVEL_DEBUG)

			#stop Player (if playing)
			if(xbmc.Player().isPlayingVideo()):
				xbmc.Player().stop()

			self.close()


	def showGameList(self):

		Logutil.log("Begin showGameList", util.LOG_LEVEL_INFO)

		#likeStatement = helper.buildLikeStatement(self.selectedCharacter)
		#games = Game(self.gdb).getFilteredGames(self.selectedConsoleId, self.selectedGenreId, self.selectedYearId, self.selectedPublisherId, likeStatement)

		self.writeMsg(util.localize(32121))

		self.clearList()

		gameRow = Game(self.gdb).getObjectById(self.selectedGameId)

		fileDict = self.getFileDictByGameRow(self.gdb, gameRow)

		romCollection = None
		try:
			romCollection = self.config.romCollections[str(gameRow[util.GAME_romCollectionId])]
		except:
			Logutil.log(util.localize(32023) % str(gameRow[util.GAME_romCollectionId]), util.LOG_LEVEL_ERROR)

		imageGameList = self.getFileForControl(romCollection.imagePlacingInfo.fileTypesForGameList, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict)
		imageGameListSelected = self.getFileForControl(romCollection.imagePlacingInfo.fileTypesForGameListSelected, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict)

		item = xbmcgui.ListItem(gameRow[util.ROW_NAME], str(gameRow[util.ROW_ID]), imageGameList, imageGameListSelected)
		item.setProperty('gameId', str(gameRow[util.ROW_ID]))

		#check if we should use autoplay video
		if(romCollection.autoplayVideoInfo):
			item.setProperty('autoplayvideoinfo', 'true')
		else:
			item.setProperty('autoplayvideoinfo', '')

		#get video window size
		if (romCollection.imagePlacingInfo.name.startswith('gameinfosmall')):
			item.setProperty('videosizesmall', 'small')
			item.setProperty('videosizebig', '')
		else:
			item.setProperty('videosizebig', 'big')
			item.setProperty('videosizesmall', '')

		videos = helper.getFilesByControl_Cached(self.gdb, (self.fileTypeGameplay,), gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict)
		if(videos != None and len(videos) != 0):
			video = videos[0]
			item.setProperty('gameplayinfo', video)

		self.addItem(item)

		xbmc.executebuiltin("Container.SortDirection")
		self.writeMsg("")

		Logutil.log("End showGameList", util.LOG_LEVEL_INFO)

	def showGameInfoNew(self):
		Logutil.log("Begin showGameInfoNew", util.LOG_LEVEL_INFO)

		# Stop Player (if playing)
		if xbmc.Player().isPlayingVideo():
			xbmc.Player().stop()

		pos = self.getCurrentListPosition()
		if pos == -1:
			pos = 0

		selectedGame = self.getListItem(pos)

		if selectedGame is None:
			Logutil.log("selectedGame == None in showGameInfo", util.LOG_LEVEL_WARNING)
			return

		thegame = Game(self.gdb).getGameById(self.selectedGameId)
		if thegame is None:
			self.writeMsg(util.localize(32024))
			return

		# Properties from the game object
		for var in ['maxplayers', 'rating', 'votes', 'url', 'region', 'media', 'perspective', 'controllertype',
					'originaltitle', 'alternatetitle', 'translatedby', 'version', 'playcount', 'plot']:
			try:
				selectedGame.setProperty(var, getattr(thegame, var))
			except AttributeError as e:
				Logutil.log('Error retrieving property ' + var + ': ' + str(e), util.LOG_LEVEL_WARNING)
				selectedGame.setProperty(var, '')

		# Properties available through ID on the game
		selectedGame.setProperty('year', Year(self.gdb).getYear(thegame.yearId))
		selectedGame.setProperty('genre', Genre(self.gdb).getGenresForGame(thegame.gameId))
		selectedGame.setProperty('publisher', Publisher(self.gdb).getPublisher(thegame.publisherId))
		selectedGame.setProperty('developer', Developer(self.gdb).getDeveloper(thegame.developerId))

		try:
			romCollection = self.config.romCollections[str(thegame.romCollectionId)]
		except KeyError as e:
			Logutil.log('Cannot get rom collection with id: ' + str(thegame.romCollectionId), util.LOG_LEVEL_ERROR)
			return

		# Rom Collection properties
		selectedGame.setProperty('romcollection', romCollection.name)
		selectedGame.setProperty('console', romCollection.name)

		# Associated artwork properties
		images = romCollection.getImagesForGameInfoView()
		f = File(self.gdb)
		for k, v in images.items():
			try:
				imagepath = f.getFilenameByGameIdAndTypeId(thegame.gameId, v.id)
				Logutil.log('Looking for {0}, imagetype {1}, found {2}'.format(k, v.name, imagepath), util.LOG_LEVEL_DEBUG)
				selectedGame.setArt({k: imagepath})

			except Exception as err:
				Logutil.log('Unable to set art: ' + repr(err), util.LOG_LEVEL_WARNING)

		Logutil.log("End showGameInfoNew", util.LOG_LEVEL_INFO)

	def showGameInfo(self):

		if self.__useRefactoredView:
			self.showGameInfoNew()
			return

		Logutil.log("Begin showGameInfo", util.LOG_LEVEL_INFO)

		#stop Player (if playing)
		if(xbmc.Player().isPlayingVideo()):
			xbmc.Player().stop()

		pos = self.getCurrentListPosition()
		if(pos == -1):
			pos = 0

		selectedGame = self.getListItem(pos)

		if(selectedGame == None):
			Logutil.log("selectedGame == None in showGameInfo", util.LOG_LEVEL_WARNING)
			return

		gameRow = Game(self.gdb).getObjectById(self.selectedGameId)
		if(gameRow == None):
			self.writeMsg(util.localize(32024))
			return

		genreString = ""
		genres = Genre(self.gdb).getGenresByGameId(gameRow[0])
		if (genres != None):
			for i in range(0, len(genres)):
				genre = genres[i]
				genreString += genre[util.ROW_NAME]
				if(i < len(genres) - 1):
					genreString += ", "

		year = self.getItemName(Year(self.gdb), gameRow[util.GAME_yearId])
		publisher = self.getItemName(Publisher(self.gdb), gameRow[util.GAME_publisherId])
		developer = self.getItemName(Developer(self.gdb), gameRow[util.GAME_developerId])


		selectedGame.setProperty('year', year)
		selectedGame.setProperty('publisher', publisher)
		selectedGame.setProperty('developer', developer)
		selectedGame.setProperty('genre', genreString)

		selectedGame.setProperty('maxplayers', self.getGameProperty(gameRow[util.GAME_maxPlayers]))
		selectedGame.setProperty('rating', self.getGameProperty(gameRow[util.GAME_rating]))
		selectedGame.setProperty('votes', self.getGameProperty(gameRow[util.GAME_numVotes]))
		selectedGame.setProperty('url', self.getGameProperty(gameRow[util.GAME_url]))
		selectedGame.setProperty('region', self.getGameProperty(gameRow[util.GAME_region]))
		selectedGame.setProperty('media', self.getGameProperty(gameRow[util.GAME_media]))
		selectedGame.setProperty('perspective', self.getGameProperty(gameRow[util.GAME_perspective]))
		selectedGame.setProperty('controllertype', self.getGameProperty(gameRow[util.GAME_controllerType]))
		selectedGame.setProperty('originaltitle', self.getGameProperty(gameRow[util.GAME_originalTitle]))
		selectedGame.setProperty('alternatetitle', self.getGameProperty(gameRow[util.GAME_alternateTitle]))
		selectedGame.setProperty('translatedby', self.getGameProperty(gameRow[util.GAME_translatedBy]))
		selectedGame.setProperty('version', self.getGameProperty(gameRow[util.GAME_version]))

		selectedGame.setProperty('playcount', self.getGameProperty(gameRow[util.GAME_launchCount]))

		isFavorite = self.getGameProperty(gameRow[util.GAME_isFavorite])
		if(isFavorite == '1'):
			selectedGame.setProperty('isfavorite', '1')
		else:
			selectedGame.setProperty('isfavorite', '')

		description = gameRow[util.GAME_description]
		if(description == None):
			description = ""
		selectedGame.setProperty('plot', description)

		fileDict = self.getFileDictByGameRow(self.gdb, gameRow)

		romCollection = None
		try:
			romCollection = self.config.romCollections[str(gameRow[util.GAME_romCollectionId])]
		except:
			Logutil.log('Cannot get rom collection with id: ' + str(gameRow[util.GAME_romCollectionId]), util.LOG_LEVEL_ERROR)

		try:
			selectedGame.setProperty('romcollection', romCollection.name)
			selectedGame.setProperty('console', romCollection.name)
		except:
			pass

		selectedGame.setArt({
			IMAGE_CONTROL_BACKGROUND: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewBackground, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_GAMEINFO_BIG: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoBig, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),

			IMAGE_CONTROL_GAMEINFO_UPPERLEFT: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoUpperLeft, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_GAMEINFO_UPPERRIGHT: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoUpperRight, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_GAMEINFO_LOWERLEFT: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoLowerLeft, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_GAMEINFO_LOWERRIGHT: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoLowerRight, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),

			IMAGE_CONTROL_GAMEINFO_UPPER: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoUpper, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_GAMEINFO_LOWER: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoLower, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_GAMEINFO_LEFT: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoLeft, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_GAMEINFO_RIGHT: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainViewGameInfoRight, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),

			IMAGE_CONTROL_1: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainView1, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_2: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainView2, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),
			IMAGE_CONTROL_3: self.getFileForControl(romCollection.imagePlacingMain.fileTypesForMainView3, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict),

		})

		Logutil.log("End showGameInfo", util.LOG_LEVEL_INFO)

	# FIXME TODO This is only used when self._useRefactoredView = False
	def getItemName(self, object, itemId):

		Logutil.log("Begin getItemName", util.LOG_LEVEL_DEBUG)

		itemRow = object.getObjectById(itemId)
		if(itemRow == None):
			Logutil.log("End getItemName", util.LOG_LEVEL_DEBUG)
			return ""
		else:
			Logutil.log("End getItemName", util.LOG_LEVEL_DEBUG)
			return itemRow[1]

	# FIXME TODO This is only used when self._useRefactoredView = False
	def getGameProperty(self, property):

		if(property == None):
			return ""

		try:
			result = str(property)
		except:
			result = ""

		return result


	def getFileDictByGameRow(self, gdb, gameRow):

		files = File(gdb).getFilesByParentIds(gameRow[util.ROW_ID], gameRow[util.GAME_romCollectionId], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId])

		fileDict = self.cacheFiles(files)

		return fileDict


	def cacheFiles(self, fileRows):

		Logutil.log("Begin cacheFiles" , util.LOG_LEVEL_DEBUG)

		fileDict = {}
		for fileRow in fileRows:
			key = '%i;%i' % (fileRow[util.FILE_parentId] , fileRow[util.FILE_fileTypeId])
			item = None
			try:
				item = fileDict[key]
			except:
				pass
			if(item == None):
				fileRowList = []
				fileRowList.append(fileRow)
				fileDict[key] = fileRowList
			else:
				fileRowList = fileDict[key]
				fileRowList.append(fileRow)
				fileDict[key] = fileRowList

		Logutil.log("End cacheFiles" , util.LOG_LEVEL_DEBUG)
		return fileDict


	def getFileForControl(self, controlName, gameId, publisherId, developerId, romCollectionId, fileDict):
		files = helper.getFilesByControl_Cached(self.gdb, controlName, gameId, publisherId, developerId, romCollectionId, fileDict)
		if(files != None and len(files) != 0):
			file = files[0]
		else:
			file = ""

		return file

	def launchEmu(self):

		Logutil.log("Begin launchEmu", util.LOG_LEVEL_INFO)

		launcher.launchEmu(self.gdb, self, self.selectedGameId, self.config, self.settings, self.selectedGame)
		Logutil.log("End launchEmu", util.LOG_LEVEL_INFO)


	def saveViewState(self, isOnExit):

		Logutil.log("Begin saveViewState", util.LOG_LEVEL_INFO)

		#TODO: save selectedGameIndex from main view
		selectedGameIndex = 0

		helper.saveViewState(self.gdb, isOnExit, 'gameInfoView', selectedGameIndex, self.selectedConsoleIndex, self.selectedGenreIndex, self.selectedPublisherIndex,
			self.selectedYearIndex, self.selectedCharacterIndex, self.selectedControlIdMainView, self.selectedControlId, self.settings)

		Logutil.log("End saveViewState", util.LOG_LEVEL_INFO)


	def getControlById(self, controlId):
		try:
			control = self.getControl(controlId)
		except:
			Logutil.log("Control with id: %s could not be found. Check WindowXML file." % str(controlId), util.LOG_LEVEL_ERROR)
			self.writeMsg(util.localize(32025) % str(controlId))
			return None

		return control


	def writeMsg(self, msg):
		control = self.getControlById(CONTROL_LABEL_MSG)
		if(control == None):
			return

		control.setLabel(msg)
