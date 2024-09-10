from . import DistributedTreasureAI
from toontown.toonbase import ToontownGlobals

class DistributedSZTreasureAI(DistributedTreasureAI.DistributedTreasureAI):

    def __init__(self, air, treasurePlanner, x, y, z):
        DistributedTreasureAI.DistributedTreasureAI.__init__(self, air, treasurePlanner, x, y, z)
        self.healAmount = treasurePlanner.healAmount

    def validAvatar(self, av):
        # Allows the avatar to pick up the treasure at full hp if they still need it for their treasure collection laff boost.
        return (av.hp >= -1 and av.hp < av.maxHp) or self.air.treasureCollectionMgr.validateAvatar(av, self.zoneId)

    def d_setGrab(self, avId):
        DistributedTreasureAI.DistributedTreasureAI.d_setGrab(self, avId)
        if avId in self.air.doId2do:
            av = self.air.doId2do[avId]
            if self.validAvatar(av):
                if av.hp == -1:
                    av.hp = 0
                if ToontownGlobals.VALENTINES_DAY in simbase.air.holidayManager.currentHolidays:
                    av.toonUp(self.healAmount * 2)
                else:
                    av.toonUp(self.healAmount)
