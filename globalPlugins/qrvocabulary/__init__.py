
import globalPluginHandler
import textInfos
import NVDAObjects
import api
import ui
import os
import xml.etree.cElementTree as ET

tree = ET.ElementTree(file=os.path.join("globalPlugins", "qrvocabulary", "ejemplo.xml"))

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def script_finder(self, gesture):
		obj=api.getFocusObject()
		treeInterceptor=obj.treeInterceptor
		if hasattr(treeInterceptor,'TextInfo') and not treeInterceptor.passThrough:
			obj=treeInterceptor
		try:
			info=obj.makeTextInfo(textInfos.POSITION_SELECTION)
		except (RuntimeError, NotImplementedError):
			info=None
		if not info or info.isCollapsed:
			ui.message(_("no selection"))
		else:
			ui.message(_("searching  the meaning of %s")%info.text)
			#str.split(info.text)
			kwrd = info.text

			tree.getroot()
			root = tree.getroot()
			root.tag, root.attrib, root.text
			for lemma in root.iter("lemma"):
				name = lemma.get("name")
				if kwrd in name:
					ui.message("%s" % lemma.text )

	__gestures = {
	"kb:NVDA+j": "finder",
}
