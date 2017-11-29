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
#from vocabulary.es_voc import lemmas
from vocabulary.ita_voc import lemmas

addonHandler.initTranslation()

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
			if lemmas.has_key(kwrd):
				ui.message("%s" %lemmas.get(kwrd))
			else:
				# Translator: message when the searched word is not present in the dictionary.
				ui.message(_("no match found for this word! "))
	# Translators: message presented in input mode, when a keystroke of an addon script is pressed.
	script_findMeaning.__doc__ = _("Announces the meaning of selected word.")

	__gestures = {
	"kb:NVDA+shift+j": "findMeaning",
}
