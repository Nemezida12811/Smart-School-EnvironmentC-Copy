import machine
import ujson
import sys
import os


def read_state():
    with open("system.json") as f:
        return ujson.load(f)
    
def write_state(state):
    try:
        with open("system.json.tmp", "w") as f:
            ujson.dump(state, f)
        os.rename("system.json.tmp", "system.json")
    except Exception as e:
        print(f": Error system file save ({e})")


machine.freq(70_000_000)

state = read_state()
saves = False

active = state["active"]
stability_key = f"{active}_stability"
checking_key = f"{active}_checking"

if state.get("rollback") or not state.get(stability_key):
    if not state.get(checking_key):
        state["active"] = "a" if state["active"] == "b" else "b"
        state["rollback"] = False
        saves = True
elif state.get("new"):
    state["active"] = state["new"]
    state["new"] = None
    saves = True
    
write_state(state)

sys.path.insert(0, "/app_" + active)
