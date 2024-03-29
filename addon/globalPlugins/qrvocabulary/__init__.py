# -*- coding: UTF-8 -*-

# Quickly Reach Vocabulary v. 1.1.1-dev add-on for NVDA SCREEN READER.
# Last update 23 feb 2023
# Copyright (C)2017-2023 by Chris Leo <llajta2012ATgmail.com>
# Released under GPL 2
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import api
try:
	import cPickle as pickle
except ImportError:
	import pickle
import config
import configobj
import glob
import globalPluginHandler
import globalVars
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
from .skipTranslation import translate
import re
from urllib.request import urlopen, Request
import json

addonHandler.initTranslation()

# paths:
ADDON_DIR = os.path.dirname(__file__)
VOCS_DIR = os.path.join(ADDON_DIR, "vocabulary")
LIST_VOCS = [os.path.split(path)[-1] for path in glob.glob(os.path.join(VOCS_DIR, '*.pkl'))]
# configuration:
confspec = {
	'myvocabulary': 'integer(default=1)',
}
config.conf.spec["vocabulary"] = confspec

ADDON_SUMMARY = addonHandler.getCodeAddon().manifest["summary"]

# Dictionaries for vocabulary names, iteritems using "six" library.
vocabularies = {
_("Spanish Vocabulary"): "esp.pkl",
_("Italian Vocabulary"): "ita.pkl"
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
		lemmas = pickle.load(output)
	except(EOFError, OSError, IOError):
		pass
	return lemmas

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	scriptCategory = ADDON_SUMMARY

	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()

	# menu to  upgrade.
		self.menu = gui.mainFrame.sysTrayIcon.toolsMenu
		self.qrVocabularyMenu = wx.Menu()
		# Translators: name of a submenu.
		self.mainItem = self.menu.AppendSubMenu(self.qrVocabularyMenu, _("Qr Vocabulary"))
		# Translators: the name of a menu item.
		self.vocabularyItem = self.qrVocabularyMenu.Append(wx.ID_ANY, _("&Search in the vocabulary."))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onVocSearchDialog, self.vocabularyItem)
		# Translators: the name of a menu item.
		self.upgradeItem = self.qrVocabularyMenu.Append(wx.ID_ANY, _("&Check updates"))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.toGetUpdate, self.upgradeItem)


		NVDASettingsDialog.categoryClasses.append(vocabularySettingsPanel)

	def terminate(self):
		try:
			self.menu.Remove(self.mainItem)
			NVDASettingsDialog.categoryClasses.remove(vocabularySettingsPanel)
		except: #(RuntimeError, AttributeError, wx.PyDeadObjectError):
			pass

# script to announce the meaning of selected word:
	@script(
		# Translators: Message presented in input help mode.
		description=_("Announces the meaning of selected or typed word found in the vocabulary."),
		gesture="kb:NVDA+alt+f7"
	)

	def script_fromWordSelected(self, gesture):
		if not os.path.exists(VOCS_DIR):
			# Translators: message when any vocabulary is installed:
			ui.message(_("No vocabularies Installed. You can download vocabularies from tools menu."))
		else:
			obj=api.getFocusObject()
			treeInterceptor=obj.treeInterceptor
			if hasattr(treeInterceptor,'TextInfo') and not treeInterceptor.passThrough:
				obj=treeInterceptor
			try:
				info=obj.makeTextInfo(textInfos.POSITION_SELECTION)
			except (RuntimeError, NotImplementedError):
				info=None
			if not info or info.isCollapsed:
				wx.CallAfter(self.onVocSearchDialog, None)
			else:
				str = info.text
				kwrd = str.lower().strip('\'\"-,.:;!? ')
				threading.Thread(target=self.findMeaning, args=(kwrd,)).start()

	# script for clipboard searching
	@script(
		# Translators: Message presented in input help mode.
		description=_("Search in the vocabulary the meaning of the word on clipboard.")
	)
	def script_fromClip(self, gesture):
		try:
			text = api.getClipData()
		except:
			text = None
		if not text or not isinstance(text, str):
			#translators: message spoken when the clipboard is empty
			ui.message(_("There is no text on the clipboard"))
		else:
			s = text
			w = s.split()
			ws=len(w)
			if ws > 1:
				tones.beep(330, 120, 30, 30)
				# Translators: message when there is more than one word on clipboard.
				ui.message(_("Too much text on clipboard. Invalid keyword."))
			else:
				kwrd = s.lower().strip('\'\"-,.:;!? ')
				threading.Thread(target=self.findMeaning, args=(kwrd,)).start()

	# Script to retrieve the last result .
	@script(
		# Translators: Message presented in input help mode.
		description=_("Retrieves the last result found in the vocabulary."),
		gesture="kb:NVDA+alt+f8",
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

		lemmas =loadVocabulary() 
		if kwrd in lemmas.keys():
			memo=(_('Found "{thisword}":\n %s').format(thisword = kwrd) %lemmas.get(kwrd))
			ui.message(memo)
		else:
			# Translator: message when the searched word is not present in the dictionary.
			ui.message(_("Sorry, no match found for {thisword}. Selected vocabulary: {vocs}.").format(thisword = kwrd, vocs = getVocsName()[config.conf["vocabulary"]["myvocabulary"]]))

	def onVocSearchDialog(self, evt):
		gui.mainFrame._popupSettingsDialog(vocSearchDialog)

	def onCheckUpdatesDialog(self, evt):
		gui.mainFrame._popupSettingsDialog(checkUpdatesDialog)


	def onSettings(self, evt):
		gui.mainFrame._popupSettingsDialog(NVDASettingsDialog, vocabularySettingsPanel)

	# Script to open settings dialog.
	@script(
		# Translators: Message presented in input help mode.
		description=_("Shows settings for available vocabularies."),
	)
	def script_settings(self, gesture):
		wx.CallAfter(self.onSettings, None)

	# Script to switch between vocabularies.
	@script(
		description=_(
			# Translators: input help to switch between vocabularies.
			"switches between vocabularies"
		)
	)
	def script_toggleVocabularies(tself,gesture):
		usedVocabulary=config.conf["vocabulary"]["myvocabulary"]
		if usedVocabulary==1:
			usedVocabulary=0
			# Translators: message when switch to Spanish vocabulary.
			ui.message(_("Spanish vocabulary"))
		else:
			usedVocabulary=1
			# Translators: message when switch to Italian vocabulary.
			ui.message(_("Italian vocabulary"))
		config.conf["vocabulary"]["myvocabulary"]=usedVocabulary

	def toGetUpdate(self, evt):
		version = addonHandler.getCodeAddon().manifest["version"]
		h = "iuuqt;00bqj/hjuivc/dpn0sfqpt0Disjtujbomn0rvjdlmzSfbdiWpdbcvmbsz0sfmfbtft0mbuftu"
		req = Request("".join(map(lambda x: chr(ord(x) - 1), h)))
		res = urlopen(req)
		results = {}
		results.update(json.load(res))
		res.close()
		ASSETS = results.get("assets")
		browserDownloadUrl = ASSETS[0].get("browser_download_url")
		remoteVersion = re.search("(?P<name>)-(?P<version>.*).nvda-addon", browserDownloadUrl.split("/")[-1]).groupdict()["version"]
		if remoteVersion != version:
			wx.CallAfter(self.onCheckUpdatesDialog, None)
		else:
			ui.browseableMessage(_("The current version {ver} is the latest.").format(ver=version), _("qrVocabulary is up to date!"))

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

class vocSearchDialog(wx.Dialog):

	def __init__(self, parent):
		# Translators: The title of the dialog.
		super(vocSearchDialog, self).__init__(parent, title=_("Search on {vocs}.").format(vocs = getVocsName()[config.conf["vocabulary"]["myvocabulary"]]))
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: The label of an edit box in the  Search dialog.
		searchWordLabel = _("&Type a word:")
		self.searchWordEdit = sHelper.addLabeledControl(searchWordLabel, wx.TextCtrl)

		sHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK|wx.CANCEL))
		self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)
		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.searchWordEdit.SetFocus()
		self.CentreOnScreen()

	def onOk(self, evt):
		global memo
		tx = self.searchWordEdit.GetValue()
		kwrd = tx.lower().strip('\'\"-,.:;!? ')


		lemmas =loadVocabulary() 
		if kwrd in lemmas.keys():
			memo=(_('Found "{thisword}":\n %s').format(thisword = kwrd) %lemmas.get(kwrd))
			# Translators: title of browseable message box.
			ui.browseableMessage(".\n".join(memo.split(". ")), _("From {vocs}").format(vocs=getVocsName()[config.conf["vocabulary"]["myvocabulary"]]))
			self.Destroy()
		else:
			# Translator: message when the searched word is not present in the vocabulary.
			gui.messageBox(_("Sorry, no match found for {thisword}. Selected vocabulary: {vocs}.").format(thisword = kwrd, vocs = getVocsName()[config.conf["vocabulary"]["myvocabulary"]]),
			# Translators: Title of warning dialog.
			_("NotFound!"),
			wx.OK)

# New Version Notification.
class checkUpdatesDialog(wx.Dialog):

	def __init__(self, parent):

		CHANGES = self.changesLog()

		# Translators: The title of the check  updates dialog.
		super(checkUpdatesDialog,self).__init__(parent,title=_("New Version Notification"))
		mainSizer=wx.BoxSizer(wx.VERTICAL)
		sizerHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: Message displayed when updates are available.
		sizerHelper.addItem(wx.StaticText(self, label=CHANGES))
		bHelper = sizerHelper.addDialogDismissButtons(guiHelper.ButtonHelper(wx.HORIZONTAL))
		# Translators: The label of a button.
		label = _("Proceed to &download page")
		self.upgradeButton = bHelper.addButton(self, label=label)
		self.upgradeButton.Bind(wx.EVT_BUTTON, self.onUpgrade)

		closeButton = bHelper.addButton(self, wx.ID_CLOSE, label=translate("&Close"))
		closeButton.Bind(wx.EVT_BUTTON, self.onClose)
		self.Bind(wx.EVT_CLOSE, lambda evt: self.onClose)
		self.EscapeId = wx.ID_CLOSE

		mainSizer.Add(sizerHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.CentreOnScreen()
		wx.CallAfter(self.Show)

	def changesLog(self):
		h = "iuuqt;00bqj/hjuivc/dpn0sfqpt0Disjtujbomn0rvjdlmzSfbdiWpdbcvmbsz0sfmfbtft0mbuftu"
		req = Request("".join(map(lambda x: chr(ord(x) - 1), h)))
		res = urlopen(req)
		results = {}
		results.update(json.load(res))
		res.close()
		CHANGES = results.get("body")
		return CHANGES

	def onUpgrade(self, evt):
		downloadPage = "https://christianlm.github.io/qrVocabulary/"
		os.startfile(downloadPage)
		self.Destroy()

	def onClose(self, evt):
		self.Destroy()

