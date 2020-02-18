# -*- coding: UTF-8 -*-

# Quickly Reach Vocabulary v. 0.6.0 add-on for NVDA SCREEN READER.
# Copyright (C)2017-2019 by Chris Leo <llajta2012ATgmail.com>
# Released under GPL 2
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import fnmatch
import globalVars
import gui
from gui import guiHelper
import os
import re
import shutil
import ui
try:
	from urllib import urlopen
except:
	from urllib.request import urlopen
import wx
# import zipfile
from zipfile import ZipFile

addonHandler.initTranslation()

URL_DOWNLOAD = "https://github.com/Christianlm/quicklyReachVocabulary/raw/master/vocabulary20190308.zip"
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
PLUGIN_DIR = os.path.join(ROOT_DIR)
VOCS_DIR = os.path.join(ROOT_DIR, "vocabulary")
DL_VOC_DIR = os.path.join(globalVars.appArgs.configPath)
dest = os.path.join(DL_VOC_DIR, "vocabulary20190308.zip")
vocsFiles = set()
VOCS_FILES = ["ita.pkl", "esp.pkl"]

class downloadDialog(wx.Dialog):

	def __init__(self, parent):
		super(downloadDialog,self).__init__(parent,title=_("Get Vocabularies"))
		mainSizer=wx.BoxSizer(wx.VERTICAL)
		sizerHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		sizerHelper.addItem(wx.StaticText(self, label=_("""The available vocabularies are:\n
        Spanish vocabulary;\n
        Italian vocabulary.\n
        Press Ok button to download and install teh vocabularies.""")))

		bHelper = sizerHelper.addDialogDismissButtons(guiHelper.ButtonHelper(wx.HORIZONTAL))
		self.okButton = bHelper.addButton(self, label=_("&Ok"))
		self.okButton.Bind(wx.EVT_BUTTON, self.onOk)

		buttonHelper = guiHelper.ButtonHelper(orientation=wx.HORIZONTAL)
		cancelButton = buttonHelper.addButton(
			parent=self,
			id=wx.ID_CANCEL
		)
		cancelButton.SetFocus()

		mainSizer.Add(sizerHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.Center(wx.BOTH | wx.CENTER_ON_SCREEN)
		wx.CallAfter(self.Show)

	def onOk(self, evt):
		self.downloadVocs()
		self.installVocs()
		self.Destroy()

	def downloadVocs(self):
		urls = [URL_DOWNLOAD]
		for url in urls:
			fn = os.path.basename(url)
			localPath = os.path.join(DL_VOC_DIR, fn)
			vocsFiles.add(localPath)
			if os.path.isfile(localPath):
				gui.messageBox(_(" Already downloaded! %s, press Ok to install.") % fn,
				_("Warning"),
				wx.OK)
			else:
				#Translators: title of progres bar dialog.
				dlg = wx.ProgressDialog(_("Downloading vocabularies"),
					#Translators: message on progres dialog.
					_("Please wait... "),
					style=wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE, parent=self)
				dlg.Update( 0)
				fURL = urlopen( url)
				header = fURL.info()
				size = None
				max = 100
				outFile = open(dest, 'wb')
				keepGoing = True
				if "Content-Length" in header :
					size = int( header["Content-Length"] )
					kBytes = int( size/1024 )
					downloadBytes = int( size/max )
					count = 0
					while keepGoing:
						count += 1
						if count >= max:
							count  = 99
						#wx.MilliSleep(100)
						wx.Yield()
						(keepGoing, skip) = dlg.Update( count,
						_("Downloaded ") + str(count*downloadBytes/1024) +
						_(" of ") + str( kBytes ) + "KB" )
						b = fURL.read(downloadBytes)
						if b:
							outFile.write(b)
						else:
							break
				else:
					while keepGoing:
						(keepGoing, skip) = dlg.UpdatePulse()
						b = fURL.read(1024*8)
						if b:
							outFile.write(b)
						else:
							break
				outFile.close()
				fURL.close()
				dlg.Update( 99, _("Downloaded ") + str(os.path.getsize(dest)/1024)+"KB" )
				dlg.Hide()
				dlg.Destroy()
				return keepGoing

	def installVocs(self):
		with ZipFile(dest,"r") as zip_ref:
			zip_ref.extractall(os.path.join(PLUGIN_DIR, "vocabulary"))
		# Translators: installation  message
		gui.messageBox(_("Setup was completed successfully!"),
		# Translators: Title of warning dialog.
		_("Vocabularies setup: "),
		wx.OK)


def toDownloader(evt):
	gui.mainFrame.prePopup()
	#wx.Bell()
	downloadDialog(gui.mainFrame).Show()
	gui.mainFrame.postPopup()
