# -*- coding: UTF-8 -*-

# Quickly Reach Vocabulary v. 0.5.5 add-on for NVDA SCREEN READER.
# Copyright (C)2017-2019 by Chris Leo <llajta2012ATgmail.com>
# Released under GPL 2
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import api
import cPickle
import config
import configobj
import glob
import globalPluginHandler
import globalVars
from globalCommands import SCRCAT_TOOLS, SCRCAT_CONFIG
import gui
from gui import SettingsPanel, NVDASettingsDialog, guiHelper
from logHandler import log
import NVDAObjects
import os
import scriptHandler
from scriptHandler import script
import textInfos
import threading
import tones
import ui
import wx
# Development code   for download and instal the vocabularies.
from . import downloader


addonHandler.initTranslation()
# paths:
ADDON_DIR = os.path.dirname(__file__)
VOCS_DIR = os.path.join(ADDON_DIR, "vocabulary")
LIST_VOCS = [os.path.split(path)[-1] for path in glob.glob(os.path.join(VOCS_DIR, '*.pkl'))]
# configuration:
confspec = {
	'myvocabulary': 'integer(default=0)',
}
config.conf.spec["vocabulary"] = confspec
# Dictionaries for vocabulary names, iteritems using "six" library.
vocabularies = {
_("Spanish Vocabulary"): "esp.pkl",
_("Italian Vocabulary"): "ita.pkl",
"default": "_temp.dat"
}
import six
tVocabularies = {v : k for k, v in six.iteritems(vocabularies)}

# To remember the last results found.
memo = ""

def getVocsFile():
	return [os.path.split(path)[-1] for path in glob.glob(os.path.join(VOCS_DIR, '*.pkl'))]

def getVocsName():
	vocsfiles = getVocsFile()
	vf = tVocabularies.keys()
	return [tVocabularies[vf] for vf in vocsfiles]

# *lemmas* is the pikled dict   name for each vocabulary
def loadVocabulary():
	vocsfiles = getVocsFile()
	vocName = vocsfiles[config.conf["vocabulary"]["myvocabulary"]]
	try:
		output = open(os.path.join(VOCS_DIR, vocName), "rb")
		lemmas = cPickle.load(output)
	except(EOFError, OSError, IOError):
		pass
	return lemmas

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()

	# Development menu for download and instal the vocabularies.
		self.toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
		self.vocabulary = self.toolsMenu.Append(wx.ID_ANY, _("Download Vocabularies."), _("Download Vocabularies..."))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, downloader.toDownloader, self.vocabulary)


		NVDASettingsDialog.categoryClasses.append(vocabularySettingsPanel)

	def terminate(self):
		NVDASettingsDialog.categoryClasses.remove(vocabularySettingsPanel)

		""" Development menu:
		try:
			self.toolsMenu.Remove(self.vocabulary)
		except: #(RuntimeError, AttributeError, wx.PyDeadObjectError):
			pass
		"""

# script to announce the meaning of selected word:
	@script(
		# Translators: Message presented in input help mode.
		description=_("Announces the meaning of selected word found in the vocabulary."),
		category = SCRCAT_TOOLS,
		gesture="kb:NVDA+shift+f7"
	)

	def script_fromWordSelected(self, gesture):
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
			kwrd = str.lower().strip('\'\"-,.:;!? ')
			threading.Thread(target=self.findMeaning, args=(kwrd,)).start()

	# script for clipboard searching
	@script(
		# Translators: Message presented in input help mode.
		description=_("Search in the vocabulary the meaning of the word on clipboard."),
		category = SCRCAT_TOOLS,
		gesture="kb:NVDA+shift+f8"
	)
	def script_fromClip(self, gesture):
		try:
			text = api.getClipData()
		except TypeError:
			text = None
		if not text or not isinstance(text,basestring):
			#translators: message spoken when the clipboard is empty
			ui.message(_("There is no text on the clipboard"))
		else:
			str = text
			w = str.split()
			ws=len(w)
			if ws > 1:
				tones.beep(330, 120, 30, 30)
				# Translators: message when there is more than one word on clipboard.
				ui.message(_("Too much text on clipboard. Invalid keyword."))
			else:
				kwrd = str.lower().strip('\'\"-,.:;!? ')
				threading.Thread(target=self.findMeaning, args=(kwrd,)).start()

	# Script to retrieve the last result .
	@script(
		# Translators: Message presented in input help mode.
		description=_("Retrieves the last result found in the vocabulary."),
		gesture="kb:NVDA+shift+f9",
		category = SCRCAT_TOOLS
	)
	def script_lastResult(self, gesture):
		if memo:
			if scriptHandler.getLastScriptRepeatCount() == 0:
				ui.message(memo)
			elif scriptHandler.getLastScriptRepeatCount() == 1:
				# Translators: title of browseable message box.
				ui.browseableMessage(".\n".join(memo.split(". ")), _("From {vocs}").format(vocs=getVocsName()[config.conf["vocabulary"]["myvocabulary"]]))
		else:
			#translators: message when  there are no recent searches in the vocabulary
			ui.message(_("There is no recent research in the vocabulary."))

	def findMeaning(self, kwrd):
		global memo
		if not os.path.exists(VOCS_DIR):
			#from . import warning
			#wx.CallLater(10, warning.notice)
			ui.message(_("No vocabularies Installed!"))
		else:
			lemmas =loadVocabulary() 
			if kwrd in lemmas.keys():
				memo=(_('Found "{thisword}":\n %s').format(thisword = kwrd) %lemmas.get(kwrd))
				ui.message(memo)
			else:
				# Translator: message when the searched word is not present in the dictionary.
				ui.message(_("Sorry, no match found for {thisword}. Selected vocabulary: {vocs}.").format(thisword = kwrd, vocs = getVocsName()[config.conf["vocabulary"]["myvocabulary"]]))

	def onSettings(self, evt):
		gui.mainFrame._popupSettingsDialog(NVDASettingsDialog, vocabularySettingsPanel)

	# Script to open settings dialog.
	@script(
		# Translators: Message presented in input help mode.
		description=_("Shows settings for available vocabularies."),
		category = SCRCAT_CONFIG
	)
	def script_settings(self, gesture):
		wx.CallAfter(self.onSettings, None)

class vocabularySettingsPanel(SettingsPanel):
	# Translators: Title of the vocabulary settings dialog.
	title = _("Vocabulary Settings")
	def makeSettings(self, settingsSizer):
		# Translators: The label for  list in the vocabulary settings dialog.
		self._myvocabulary = _("Select your vocabulary:")

		dialogSizer = wx.BoxSizer (wx.VERTICAL)
		myvocabularyLabel = wx.StaticText (self, label = self._myvocabulary)
		dialogSizer.Add (myvocabularyLabel)
		self._myvocabularyChoice = wx.Choice (self, choices=getVocsName())
		dialogSizer.Add (self._myvocabularyChoice)
		self._myvocabularyChoice.SetSelection(config.conf["vocabulary"]["myvocabulary"])

	def postInit(self):
		self._myvocabularyChoice.SetFocus()

	def onSave(self):
		config.conf["vocabulary"]["myvocabulary"]=self._myvocabularyChoice.GetSelection()
