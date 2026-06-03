from api import MCTS
import os

mcts = MCTS(filename="synth_temp")
if mcts.load_state():
    print("node_hashmap keys count:", len(mcts._node_hashmap))
    for k, v in mcts._node_hashmap.items():
        print(f"Key: {k} (type: {type(k)}) -> Node intent: {v.intent}")
else:
    print("Failed to load state.")
