from panda3d.core import *
from panda3d.otp import *
from direct.gui.DirectGui import *
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from toontown.safezone import TreasureCollectionGlobals
from toontown.toonbase.TTLocalizer import HoodIdToName, TreasureTrackerTitle
from toontown.hood.ZoneUtil import getCanonicalHoodId, getWhereName


class TreasureTracker(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory("TreasureTracker")

    def __init__(self):
        DirectFrame.__init__(self, relief=None, sortOrder=DGG.BACKGROUND_SORT_INDEX)
        self.notify.debug("__init__()")
        self.hide()
        self.isOpen = False

    def load(self):
        self.notify.debug("load()")
        frameModel = loader.loadModel("phase_3.5/models/gui/frame") # This is used on the sos-toon gui, but works really well here
        self["image"] = frameModel
        self["image_scale"] = (0.1, 0.1, 0.1)
        self.setPos(0.95, 0, -0.3) # Right-hand side, a bit above shticker book
        self.resetFrameSize()

        buttonModel = loader.loadModel("phase_3.5/models/gui/friendslist_gui.bam") # Utilising friends list GUI for our arrows to open/close the gui
        buttonUp = buttonModel.find("**/FndsLst_ScrollUp")
        buttonDown = buttonModel.find("**/FndsLst_ScrollDN")
        buttonRollover = buttonModel.find("**/FndsLst_ScrollUp_Rllvr")

        self.closeButton = DirectButton(image=(buttonUp, buttonDown, buttonRollover), relief=None,
                                        command=self.close, pos=(1.3, 0, -0.3), scale=0.7)
        self.closeButton.setHpr(0, 0, 90)
        self.closeButton.hide()

        self.openButton = DirectButton(image=(buttonUp, buttonDown, buttonRollover), relief=None,
                                       command=self.open, pos=(1.3, 0, -0.3), scale=0.7)
        self.openButton.setHpr(0, 0, 270)
        self.openButton.hide()

        self.title = OnscreenText(text=TreasureTrackerTitle, style=1, fg=(1, 1, 1, 1), pos=(0.95, -0.15), scale=0.07)
        self.title.hide()

        self.stats = []

        position = -0.2
        for i in range(len(TreasureCollectionGlobals.safezones)):
            self.stats.append(OnscreenText(text="", style=1, fg=(1, 1, 1, 1), pos=(0.95, position), scale=0.055))
            self.stats[i].hide()
            position -= 0.05

        self.updateStats(base.localAvatar.getCollectedTreasures())
        self.accept("hideTreasureTracker", self.hideAll, [])
        self.accept("showTreasureTracker", self.reshowOpenButton, [])
        self.accept("localToonUpdatedTreasures", self.updateStats, [])

    def unload(self):
        self.notify.debug("unload()")
        self.ignore("hideTreasureTracker")
        self.ignore("showTreasureTracker")
        self.ignore("localToonUpdatedTreasures")
        loader.unloadModel("phase_3.5/models/gui/frame")
        self.destroy()
        self.openButton.destroy()
        del self.openButton
        self.closeButton.destroy()
        del self.closeButton
        self.title.destroy()
        del self.title
        for stat in self.stats:
            stat.destroy()
            del stat
        del self.stats

    def updateStats(self, collectedTreasures):
        self.notify.debug("updateStats() collectedTreasures: %s" % (collectedTreasures))

        # This function is called every time our local toon has their treasure collecting stats updated

        index = 0
        for hood in TreasureCollectionGlobals.safezones:
            if index+1 > len(collectedTreasures):
                break
            self.stats[index].setText("%s: %s" % (HoodIdToName[hood], collectedTreasures[index]))
            if collectedTreasures[index] > TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
                self.stats[index].node().setTextColor(1.0, 0.0, 0.0, 1.0) # Red (Invalid, avatar needs repairing, done automatically when they run into a treasure in that hood)
            elif collectedTreasures[index] == TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
                self.stats[index].node().setTextColor(0.0, 1.0, 0.0, 1.0) # Green (Maxed in that hood)
            else:
                self.stats[index].node().setTextColor(1.0, 1.0, 0.0, 1.0) # Yellow (Not maxed in that hood)
            index += 1

    def open(self):
        self.notify.debug("open()")
        if self.isOpen:
            return
        self.isOpen = True
        self.show()
        self.title.show()
        self.openButton.hide()
        self.closeButton.show()
        for stat in self.stats:
            stat.show()

    def close(self):
        self.notify.debug("close()")
        if not self.isOpen:
            return
        self.isOpen = False
        self.hide()
        self.title.hide()
        self.openButton.show()
        self.closeButton.hide()
        for stat in self.stats:
            stat.hide()

    def hideAll(self):
        
        # This is called automatically whenever the shticker book is hidden, so that our GUI isn't just sticking around when it shouldn't

        self.notify.debug("hideAll()")
        self.isOpen = False
        self.openButton.hide()
        self.closeButton.hide()
        self.hide()
        self.title.hide()
        for stat in self.stats:
            stat.hide()

    def reshowOpenButton(self):
        self.notify.debug("reshowOpenButton()")
        if getWhereName(base.localAvatar.zoneId, 1) != "playground" or getCanonicalHoodId(base.localAvatar.zoneId) not in TreasureCollectionGlobals.safezones:
            # Don't show GUI unless in a supported playground, don't show in buildings or streets either
            self.notify.debug("NOT showing open button.")
            return
        self.openButton.show()