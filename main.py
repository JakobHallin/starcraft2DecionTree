from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer

class DecisionTree(BotAI):
    def __init__(self):
        self.game_state = {
            'supply_left': 0,
            'supply_total': 0,
            'workers': 0,
            'minerals': 0,   
            #'barracks_built': False,
            #'enemy_near_base': False,
            #'our_army_value': 100,
            #'enemy_army_value': 80,
            }

    async def on_start(self):
        self.client.game_step = 1
        
    async def on_step(self, iteration):
         print(f"Step {iteration}")
         self.game_state = await self.setgame_state()
         print(f"Game State: {self.game_state}")
        
    async def setgame_state(self):
        self.game_state['supply_left'] = self.supply_left
        self.game_state['supply_total'] = self.supply_cap
        self.game_state['workers'] = self.workers.amount
        self.game_state['minerals'] = self.minerals
        return self.game_state

def main():
    run_game(
        maps.get("Flat96"),  # You can replace with any valid map
        [Bot(Race.Terran, DecisionTree()), Computer(Race.Zerg, Difficulty.Easy)],
        realtime=False,
    )

if __name__ == "__main__":
    main()