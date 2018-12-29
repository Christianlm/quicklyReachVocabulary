# -*- coding: UTF-8 -*-

#Copyright (C)2017-2018
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
from gui import SettingsPanel, NVDASettingsDialog, guiHelper
from logHandler import log
import scriptHandler
import configobj
#from cStringIO import StringIO
import glob
from globalCommands import SCRCAT_TOOLS
from scriptHandler import script

addonHandler.initTranslation()

ADDON_DIR = os.path.dirname(__file__)
VOCS_DIR = os.path.join(ADDON_DIR, "vocabulary")
LIST_VOCS = [os.path.split(path)[-1] for path in glob.glob(os.path.join(VOCS_DIR, '*.pkl'))]

confspec = {
	'myvocabulary': 'string(default="esp.pkl")',
}
config.conf.spec["vocabulary"] = confspec


def loadVocabulary():
	vocName = config.conf["vocabulary"]["myvocabulary"]
	try:
		output = open(os.path.join(VOCS_DIR, vocName), "rb")
		lemmas = cPickle.load(output)
	except(EOFError, OSError, IOError):
		pass
	return lemmas

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		NVDASettingsDialog.categoryClasses.append(vocabularySettingsPanel)

	def terminate(self):
		NVDASettingsDialog.categoryClasses.remove(vocabularySettingsPanel)


	@script(
		# Translators: Message presented in input help mode.
		description=_("Announces the meaning of selected word."),
		category = SCRCAT_TOOLS,
		gesture="kb:NVDA+shift+f7"
	)

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

	def onVocabularySettingsPanel(self, evt):
		gui.mainFrame._popupSettingsDialog(NVDASettingsDialog, VocabularySettingsPanel)

class vocabularySettingsPanel(SettingsPanel):
	# Translators: Title of the vocabulary settings dialog.
	title = _("Vocabulary Settings")
	def makeSettings(self, settingsSizer):
		# Translators: The label for  list in the vocabulary settings dialog.
		self._myvocabulary = _("Select your vocabulary:")

		dialogSizer = wx.BoxSizer (wx.VERTICAL)
		myvocabularyLabel = wx.StaticText (self, label = self._myvocabulary)
		dialogSizer.Add (myvocabularyLabel)
		self._myvocabularyChoice = wx.Choice (self, choices=LIST_VOCS)
		dialogSizer.Add (self._myvocabularyChoice)
		self._myvocabularyChoice.SetStringSelection(config.conf["vocabulary"]["myvocabulary"])

	def postInit(self):
		self._myvocabularyChoice.SetFocus()



	def onSave(self):
		config.conf["vocabulary"]["myvocabulary"]=self._myvocabularyChoice.GetStringSelection()

