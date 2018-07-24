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
from gui import guiHelper
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

	def onVocabularySettingsDialog(self, evt):
		gui.mainFrame._popupSettingsDialog(vocabularySettingsDialog)

	def script_vocabularySettings(self, gesture):
		wx.CallAfter(self.onVocabularySettingsDialog, None)
	# Translators: Input help mode message for go to Vocabulary  dialog.
	script_vocabularySettings.__doc__ = _("Shows the list of available vocabularies")

	__gestures = {
		"kb:NVDA+shift+f7": "findMeaning",
		"kb:NVDA+shift+f8": "vocabularySettings",
	}


class vocabularySettingsDialog(gui.SettingsDialog):
	# Translators: Title of the vocabulary settings dialog.
	title = _("Vocabulary Settings")
	def makeSettings(self, settingsSizer):
		vocabularySettingsGuiHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: The label for  list in the vocabulary settings dialog.
		self._myvocabularyChoice = vocabularySettingsGuiHelper.addLabeledControl(_("Select your Vocabulary:"), wx.Choice, choices=LIST_VOCS)
		self._myvocabularyChoice.SetStringSelection(config.conf["vocabulary"]["myvocabulary"])

	def postInit(self):
		self._myvocabularyChoice.SetFocus()

	def onOk(self, evt):
		config.conf["vocabulary"]["myvocabulary"]=self._myvocabularyChoice.GetStringSelection()
		super(vocabularySettingsDialog, self).onOk(evt)

