from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer

from sc2.ids.unit_typeid import UnitTypeId

from functools import partial

# Decision Node Class
class DecisionNode:
    def __init__(self, name, condition_func=None, action_func=None, weight=0):
        self.name = name
        self.condition_func = condition_func
        self.action_func = action_func
        self.weight = weight
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def evaluate(self, game_state):
        best_node = None
        best_weight = -1

        if self.action_func and (self.condition_func is None or self.condition_func(game_state)):
            best_node = self
            best_weight = self.weight

        for child in self.children:
            evaluated_node, evaluated_weight = child.evaluate(game_state)
            if evaluated_weight > best_weight:
                best_node = evaluated_node
                best_weight = evaluated_weight

        return best_node, best_weight


class DecisionTree(BotAI):
    def __init__(self):
        self.game_state = {
            'supply_left': 0,
            'supply_total': 0,
            'workers': 0,
            'minerals': 0,   
            'barracks_built': False,
            #'enemy_near_base': False,
            #'our_army_value': 100,
            #'enemy_army_value': 80,
            }
        self.root_node = None  

    async def on_start(self):
        self.client.game_step = 1
        self.build_decision_tree()
        
    async def on_step(self, iteration):
        print(f"Step {iteration}")
        self.game_state = await self.setgame_state()
        print(f"Game State: {self.game_state}")
        best_node, best_weight = self.root_node.evaluate(self.game_state)
        if best_node:
            print(f"[Decision]: {best_node.name} (Weight: {best_weight})")
            await best_node.action_func()
        else:
            print("No valid actions found.")
        

        
    async def setgame_state(self):
        self.game_state['supply_left'] = self.supply_left
        self.game_state['supply_total'] = self.supply_cap
        self.game_state['workers'] = self.workers.amount
        self.game_state['minerals'] = self.minerals
        self.game_state['barracks_built'] = self.structures(UnitTypeId.BARRACKS).ready.exists
        return self.game_state
    
    #condions
    def is_supply_blocked(self, gs):
        supply_depots_in_progress = self.already_pending(UnitTypeId.SUPPLYDEPOT)
        return gs['supply_left'] <= 2 and supply_depots_in_progress == 0


    def near_supply_cap(self, gs):
        return gs['supply_left'] >= 7 and gs['minerals'] >= 200
        #return gs['supply_total'] >= 180 and gs['minerals'] >= 100

    def need_more_workers(self, gs):
        return gs['workers'] < 22
    def first_barack(self, gs):

        # Check if we have at least one supply depot built
        supply_depot_ready = self.structures(UnitTypeId.SUPPLYDEPOT).ready.exists
        # Cheack so we are not building a barrack already
        barracks_in_progress = self.already_pending(UnitTypeId.BARRACKS)
        return not gs['barracks_built'] and supply_depot_ready and barracks_in_progress == 0

    
    
    # ----- Action Functions -----
    async def build_supply_depot(self):
        if self.can_afford(UnitTypeId.SUPPLYDEPOT):
            location = await self.get_build_location(UnitTypeId.SUPPLYDEPOT)
            if location:
                await self.build(UnitTypeId.SUPPLYDEPOT, location)
                print("Building Supply Depot")

    async def build_worker(self):
        if self.can_afford(UnitTypeId.SCV):
            for cc in self.townhalls.ready.idle:
                cc.train(UnitTypeId.SCV)
                print("Training SCV")
                break

    async def build_barack(self):
        if self.structures(UnitTypeId.SUPPLYDEPOT).ready.amount >= 1:
            if self.can_afford(UnitTypeId.BARRACKS):
                location = await self.get_build_location(UnitTypeId.BARRACKS)
                if location:
                    await self.build(UnitTypeId.BARRACKS, location)
                    print("Building Barracks")

     # Helper for finding build location
    async def get_build_location(self, structure):
        placement_positions = await self.find_placement(structure, near=self.start_location)
        return placement_positions
    

    
    
    # ----- Build the Decision Tree -----
    def build_decision_tree(self):
        self.root_node = DecisionNode("Game Start")

        # Define the decision nodes and their actions
        supply_blocked_node = DecisionNode(
            "Supply Blocked?",
            partial(self.is_supply_blocked),
            self.build_supply_depot,
            weight=100
        )
        
        proactive_supply_node = DecisionNode(
            "Proactively Build Supply Depot",
            partial(self.near_supply_cap),
            self.build_supply_depot,
            weight=70
        )

        build_worker_node = DecisionNode(
            "Build Worker",
            partial(self.need_more_workers),
            self.build_worker,
            weight=80
        )
        build_firstbarack_node = DecisionNode(
            "Build First Barack",
            partial(self.first_barack),
            self.build_barack,
            weight=90
        )

        self.root_node.add_child(supply_blocked_node)
        self.root_node.add_child(proactive_supply_node)
        self.root_node.add_child(build_worker_node)
        self.root_node.add_child(build_firstbarack_node)



def main():
    run_game(
        maps.get("Flat96"),  # You can replace with any valid map
        [Bot(Race.Terran, DecisionTree()), Computer(Race.Zerg, Difficulty.Easy)],
        realtime=False,
    )

if __name__ == "__main__":
    main()