# -*- coding: UTF-8 -*-

#Copyright (C)2017
# Released under GPL 2
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import globalPluginHandler
import textInfos
import NVDAObjects
import api
import ui
import os
import cPickle
import config
import wx
import gui
from gui.settingsDialogs import SettingsDialog
from logHandler import log
import scriptHandler
import configobj
import validate
from cStringIO import StringIO
import glob
addonHandler.initTranslation()

ADDON_DIR = os.path.dirname(__file__)
VOCS_DIR = os.path.join(ADDON_DIR, "vocabulary")
LIST_VOCS = [os.path.split(path)[-1] for path in glob.glob(os.path.join(VOCS_DIR, '*.pkl'))]

def loadVocabulary():
	vocName = getVocabularies()
	try:
		output = open(os.path.join(VOCS_DIR, vocName), "rb")
		lemmas = cPickle.load(output)
	except(EOFError, OSError, IOError):
		pass
	return lemmas

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def script_findMeaning(self, gesture):
		obj=api.getFocusObject()
		treeInterceptor=obj.treeInterceptor
		if hasattr(treeInterceptor,'TextInfo') and not treeInterceptor.passThrough:
			obj=treeInterceptor
		try:
			info=obj.makeTextInfo(textInfos.POSITION_SELECTION)
		except (RuntimeError, NotImplementedError):
			info=None
		if not info or info.isCollapsed:
			# Translator: message when no  word has been selected.
			ui.message(_("Please, select a word!"))
		else:
			str = info.text
			kwrd = str.lower().strip()
			lemmas =loadVocabulary() 
			if lemmas.has_key(kwrd):
				ui.message("%s" %lemmas.get(kwrd))
			else:
				# Translator: message when the searched word is not present in the dictionary.
				ui.message(_("no match found for this word... "))
	# Translators: message presented in input mode, when a keystroke of this addon script is pressed.
	script_findMeaning.__doc__ = _("Announces the meaning of selected word.")

	def onVocabularyDialog(self,evt):
		gui.mainFrame._popupSettingsDialog(vocabularySettingsDialog)

	def script_vocabularySettingsDialog(self, gesture):
		wx.CallAfter(self.onVocabularyDialog, None)
	# Translators: Input help mode message for go to Vocabulary  dialog.
	script_vocabularySettingsDialog.__doc__ = _("Shows the list of available vocabularies")

	__gestures = {
		"kb:NVDA+shift+f7": "findMeaning",
		"kb:NVDA+shift+f8": "vocabularySettingsDialog",
	}



# vocabularies = {"esp.pkl": "Diccionario de la lengua Española", "ita.pkl": "Dizionario Italiano",}

class vocabularySettingsDialog(gui.SettingsDialog):
	# Translators: Title of the vocabulary setting dialog.
	title = _("Vocabulary Settings")

	def __init__(self, parent):
		super(vocabularySettingsDialog, self).__init__(parent)

	def makeSettings(self, sizer):
		myVocabularySizer = wx.BoxSizer(wx.VERTICAL)
		# Translators: The label for  list in the vocabulary setting dialog.
		myVocabularyLabel = wx.StaticText(self, label=_("Select your Vocabulary:"))
		myVocabularySizer.Add(myVocabularyLabel)
		self._myVocabularyChoice = wx.Choice(self, choices=LIST_VOCS)
		self._myVocabularyChoice.SetStringSelection("myVocabulary")
		myVocabularySizer.Add(self._myVocabularyChoice)
		sizer.Add(myVocabularySizer)

	def postInit(self):
		self._myVocabularyChoice.SetFocus()

	def onOk(self, event):
		super(vocabularySettingsDialog, self).onOk(event)
		getConfig()["vocabulary"]["myVocabulary"] = self._myVocabularyChoice.GetStringSelection()
		try:
			getConfig().write()
		except IOError:
			log.error("Error writing  configuration", exc_info=True)
		loadUpSetting()

_config = None
configspec = StringIO("""
[vocabulary]
myVocabulary=string(default="esp.pkl")
""")

def getConfig():
	global _config
	if not _config:
		path = os.path.join(config.getUserDefaultConfigPath(), "vocabulary.ini")
		_config = configobj.ConfigObj(path, configspec=configspec)
		val = validate.Validator()
		_config.validate(val)
	return _config

myVocabulary = None
def getVocabularies():
	return getConfig()["vocabulary"]["myVocabulary"]

def setVocabularies():
	global myVocabulary
	myVocabulary = getVocabularies()

def loadUpSetting():
	setVocabularies()


