"""Decode and parse raw socket stream for game 9995585 into fully structured entities."""

import json
import re
from pathlib import Path

# SCB Protocol Mappings extracted from C7LJJbUd.js
k = {0:"scorelist",1:"action",2:"team",3:"time_event",4:"player_stats",5:"scorelist_delete",6:"action_delete",7:"starting_five",8:"delete_player",20:"history_end"}
K = {1:"q1",2:"q2",3:"q3",4:"q4",5:"ot1",6:"ot2",7:"ot3",8:"ot4",9:"ot5",10:"ot6",11:"ot7",12:"ot8",13:"ot9",14:"ot10"}
at = {0:"JB",1:"JS",2:"FT",3:"P2",4:"P3",5:"FOUL",6:"RFOUL",7:"REB",8:"TREB",9:"TO",10:"ST",11:"BL",12:"TIMEO",13:"SUBST",14:"CFOUL",15:"TTO"}
ct = {0:"D",1:"O",2:"P",3:"T",4:"U",5:"Q",6:"C",7:"P",8:"1",9:"2",10:"3",11:"LB",12:"BP",13:"OB",14:"TR",15:"VI",16:"5",17:"8",18:"24",19:"E"}
ht = {0:0,1:1,2:2,3:3,4:4,5:5,6:"SC",7:"FB",8:"TO",9:"FT",10:"ST",11:"SF",12:"AL",51:"JS",52:"LU",53:"DU",54:"AO",55:"TI"}
ut = {0:"-",1:"+",2:"BL"}
P = {1:"A",2:"B"}
lt = {0:"start",1:"end",2:"Game end"}
ft = {0:"N",1:"S"}

pt = {
    0: {"objects":["type","id","quarter","time","points_1","points_2"], "mappings":{0:k,2:K}},
    1: {"objects":["type","id","quarter","teamcode","player_id1","player_id2","time","player_nr1","player_nr2","action","info1","info2","info3","result","points1","points2","x","y"], "mappings":{0:k,2:K,3:P,9:at,10:ct,12:ht,13:ut}},
    2: {"objects":["type","id","teamcode","FT_points","FT_attempts","FT_rate","P2_points","P2_attempts","P2_rate","P3_points","P3_attempts","P3_rate","FOUL_nr","REBD_nr","REBO_nr","BL_nr","ST_nr","TO_nr","index1","index2","team_foul_nr"], "mappings":{0:k,2:P}},
    3: {"objects":["type","id","quarter","time","action","points1","points2"], "mappings":{0:k,2:K,4:lt}},
    4: {"objects":["type","id","teamcode","player_id","playcode","player_nr","points","FT_points","FT_attempts","FT_rate","P2_points","P2_attempts","p2_rate","P3_points","P3_attempts","P3_rate","FOUL_nr","REB_nr","ASSIST_nr","BL_nr","ST_nr","TO_nr","index1","index2","time_s"], "mappings":{0:k,2:P,4:ft}},
    5: {"objects":["type","id","points_1","points_2"], "mappings":{0:k}},
    6: {"objects":["type","id"], "mappings":{0:k}},
    7: {"objects":["type","quarter","teamcode","player_id1","player_id2","player_id3","player_id4","player_id5"], "mappings":{0:k,1:K,2:P}},
    8: {"objects":["type","id"], "mappings":{0:k}},
    20: {"objects":["type"], "mappings":{0:k}},
}

def decode_packet(raw_arr):
    type_id = raw_arr[0]
    schema = pt.get(type_id)
    if not schema:
        return {"raw": raw_arr}
    res = {}
    for idx, key in enumerate(schema["objects"]):
        val = raw_arr[idx] if idx < len(raw_arr) else None
        mapping = schema["mappings"].get(idx)
        if mapping and val in mapping:
            res[key] = mapping[val]
        else:
            res[key] = val
    return res

def parse_match_stream(log_path: Path):
    text = log_path.read_text(encoding="utf-8")
    # Find all 42[matchId, [array]]
    raw_arrays = re.findall(r'42\[\d+,\s*(\[[^\]]+\])\]', text)
    print(f"Found {len(raw_arrays)} raw socket arrays in log.")
    
    decoded = {
        "team_stats": [],
        "player_stats": [],
        "actions": [],
        "time_events": [],
        "scorelist": [],
        "starting_five": [],
    }
    
    for s in raw_arrays:
        try:
            arr = json.loads(s)
            obj = decode_packet(arr)
            t = obj.get("type")
            if t == "team":
                decoded["team_stats"].append(obj)
            elif t == "player_stats":
                decoded["player_stats"].append(obj)
            elif t == "action":
                decoded["actions"].append(obj)
            elif t == "time_event":
                decoded["time_events"].append(obj)
            elif t == "scorelist":
                decoded["scorelist"].append(obj)
            elif t == "starting_five":
                decoded["starting_five"].append(obj)
        except Exception as e:
            print(f"Error decoding {s}: {e}")

    print(f"Decoded summary:")
    print(f"  Team stats: {len(decoded['team_stats'])}")
    print(f"  Player stats: {len(decoded['player_stats'])}")
    print(f"  PBP Actions: {len(decoded['actions'])}")
    print(f"  Time events: {len(decoded['time_events'])}")
    print(f"  Scorelist items: {len(decoded['scorelist'])}")
    print(f"  Starting lineups: {len(decoded['starting_five'])}")

    out_file = Path("reports/source_audit/samples/match_9995585_decoded.json")
    out_file.write_text(json.dumps(decoded, indent=2), encoding="utf-8")
    print(f"Saved decoded match to {out_file}")

if __name__ == "__main__":
    parse_match_stream(Path("reports/source_audit/samples/socket_raw_game_9995585.txt"))
