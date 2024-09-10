from direct.directnotify import DirectNotifyGlobal
from toontown.hood.ZoneUtil import getCanonicalHoodId
from toontown.safezone import TreasureCollectionGlobals
from toontown.toonbase.ToontownGlobals import MaxHpLimit
from toontown.toonbase.TTLocalizer import TreasureCollectionLaffBoost, HoodIdToName, TreasureCollectionAllHoodsMaxed
from panda3d.otp import WhisperPopup

class TreasureCollectionManagerAI():

    notify = DirectNotifyGlobal.directNotify.newCategory("TreasureCollectionManagerAI")

    def __init__(self, air):
        self.air = air
        self.notify.debug("Initialised.")

    def validateAvatar(self, av, zoneId):

        # Here, we validate the avatar by checking that the hood is valid,
        # and if the avatar actually needs a treasure. We reject avatars who have
        # already maxed on a hood. If an avatar is above the requirements for a hood,
        # we repair them.
        
        self.notify.debug("validateAvatar() avId: %d, zoneId: %d" % (av.doId, zoneId))
        hood = getCanonicalHoodId(zoneId)
        self.notify.debug("Zone %d has a canonical hood ID of %d." % (zoneId, hood))
        index = self.getSafezoneIndex(av, hood)
        if index is not None:
            collectedTreasures = av.getCollectedTreasures()
            self.notify.debug("Collected treasures: %s" % (collectedTreasures))
            if collectedTreasures[index] < TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
                self.notify.debug("Avatar is valid.")
                return True
            elif collectedTreasures[index] > TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
                self.notify.debug("Avatar has not been repaired since the requirement being lowered. Repairing them now.")
                self.repairAvatar(av) # We have an avatar above the current requirement. This can happen if the requirement is lowered in a game update.
            else:
                self.notify.debug("Avatar is invalid, already maxed in this hood.")
        else:
            self.notify.debug("HoodId was invalid: %d" % (hood))
        return False
    
    def repairAvatar(self, av):

        # Ideally in a production envrionment, this won't be necessary and there will be constant sanity checks for game-wide progress vs current laff.
        # But, that doesn't exist in the source used for this demo.

        self.notify.debug("repairAvatar() avId: %d." % (av.doId))
        collectedTreasures = av.getCollectedTreasures()
        self.notify.debug("Collected treasures: %s" % (collectedTreasures))
        index = 0
        for amount in collectedTreasures:
            if index+1 > len(TreasureCollectionGlobals.safezones):
                break
            if amount > TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
                self.notify.debug("Index %d needs repairing." % (index))
                if amount < TreasureCollectionGlobals.oldTreasureLaffBoostCollectionReq:
                    # Making sure the av hasn't already earned the laff boost
                    self.notify.debug("Avatar needs their missing laff boost, giving +1 laff.")
                    oldMaxHp = av.getMaxHp()
                    newMaxHp = min(MaxHpLimit, oldMaxHp + 1)
                    av.b_setMaxHp(newMaxHp)
                    av.toonUp(newMaxHp)

                    # We won't send an individual maxing notification for each hood, since that'll get spammy if multiple needed repairing.
                    # However, we'll still congratulate + fanfair them if all of them are maxed.

                # Correct it so that this doesn't need to run again.
                self.notify.debug("Correcting list item.")
                collectedTreasures[index] = TreasureCollectionGlobals.treasureLaffBoostCollectionReq
            
            index += 1

        self.notify.debug("End of repair.")

        if self.checkFanfare(collectedTreasures):
            # They've maxed in all hoods! Give them a fanfare and congratulate them.
            av.d_setSystemMessage(WhisperPopup.WTSystem, TreasureCollectionAllHoodsMaxed % TreasureCollectionGlobals.treasureLaffBoostCollectionReq)
            av.d_treasureCollectMaxingFanfare()
            self.notify.debug("Avatar has now maxed all hoods.")

        # Save our repairs to the database.
        self.notify.debug("Saving repairs.")
        av.b_setCollectedTreasures(collectedTreasures)

    def getSafezoneIndex(self, av, hood):
        self.notify.debug("getSafezoneIndex() avId: %d, hood: %d" % (av.doId, hood))
        try:
            index = TreasureCollectionGlobals.safezones.index(hood)
        except ValueError:
            self.notify.warning("Safezone treasure collected by av %d in unaccounted hoodId: %d" % (av.doId, hood))
            index = None
        
        return index

    def updateCollectionList(self, av, zoneId):
        self.notify.debug("updateCollectionList() avId: %d, zoneId: %d" % (av.doId, zoneId))
        if not self.validateAvatar(av, zoneId):
            # We check this again, in-case the treasure was valid for health but not for treasure hunting.
            return
        hood = getCanonicalHoodId(zoneId)
        self.notify.debug("Zone %d has a canonical hood ID of %d." % (zoneId, hood))
        index = self.getSafezoneIndex(av, hood)
        if index is None:
            return
        
        collectedTreasures = av.getCollectedTreasures()
        if collectedTreasures[index] < TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
            self.notify.debug("Avatar is able to progress. Was: %d, Now: %d" % (collectedTreasures[index], collectedTreasures[index]+1))
            collectedTreasures[index] += 1
            
            if collectedTreasures[index] == TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
                self.notify.debug("Avatar has now maxed this hood and earned a laff boost.")
                # The avatar has earned a laff boost!
                oldMaxHp = av.getMaxHp()
                newMaxHp = min(MaxHpLimit, oldMaxHp + 1)
                av.b_setMaxHp(newMaxHp)
                av.toonUp(newMaxHp)

                # Let them know.
                av.d_setSystemMessage(WhisperPopup.WTSystem, TreasureCollectionLaffBoost % (TreasureCollectionGlobals.treasureLaffBoostCollectionReq, HoodIdToName[hood]))

                if self.checkFanfare(collectedTreasures):
                    # They've maxed in all hoods! Give them a fanfare and congratulate them.
                    av.d_setSystemMessage(WhisperPopup.WTSystem, TreasureCollectionAllHoodsMaxed % TreasureCollectionGlobals.treasureLaffBoostCollectionReq)
                    av.d_treasureCollectMaxingFanfare()
                    self.notify.debug("Avatar has now maxed all hoods.")

            # And finally, save the progress to the database.
            self.notify.debug("Saving progress to the database.")
            av.b_setCollectedTreasures(collectedTreasures)

    def checkFanfare(self, collectedTreasures):
        self.notify.debug("checkFanfare() collectedTreasures: %s" % (collectedTreasures))
        for amount in collectedTreasures:
            if amount < TreasureCollectionGlobals.treasureLaffBoostCollectionReq:
                self.notify.debug("Toon is not eligible for fanfare.")
                return False
        self.notify.debug("Toon is eligible for fanfare.")
        return True