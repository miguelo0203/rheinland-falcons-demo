"""Test Socket.IO / Engine.IO protocol to retrieve Boxscore, PBP actions, starting five, and scorelist for game 9995585."""

import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

API_KEY = "81e03c389456a1d3441cd89ce9703d88" # JBBL Key
BASE_URL = "https://api.bbl.scb.world"
GAME_ID = 9995585

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def test_engineio_polling():
    print(f"=== Testing Engine.IO Polling on {BASE_URL} for game {GAME_ID} ===")
    
    # Step 1: Handshake (Engine.IO v4)
    handshake_url = f"{BASE_URL}/socket.io/?EIO=4&transport=polling"
    headers = {
        "User-Agent": USER_AGENT,
        "x-api-key": API_KEY,
        "Accept": "*/*",
    }
    
    req = urllib.request.Request(handshake_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8")
        print(f"Handshake response: {content}")
        
        # Engine.IO open packet starts with '0' followed by JSON
        if content.startswith("0"):
            handshake_data = json.loads(content[1:])
            sid = handshake_data["sid"]
            print(f"Session ID (sid): {sid}")
            
            # Step 2: Connect to Socket.IO namespace (packet '40')
            connect_url = f"{BASE_URL}/socket.io/?EIO=4&transport=polling&sid={sid}"
            # Socket.IO connect packet: '40'
            req_connect = urllib.request.Request(connect_url, data=b"40", headers={**headers, "Content-Type": "text/plain;charset=UTF-8"})
            with urllib.request.urlopen(req_connect, timeout=15) as resp2:
                print(f"Connect send response status: {resp2.status}")

            # Step 3: Poll for connection ack (packet '40{"sid":"..."}')
            req_poll = urllib.request.Request(connect_url, headers=headers)
            with urllib.request.urlopen(req_poll, timeout=15) as resp_poll:
                poll_res = resp_poll.read().decode("utf-8")
                print(f"Poll connect ack: {poll_res}")

            # Step 4: Emit 'join' event: 42["join", 9995585]
            join_payload = f'42["join",{GAME_ID}]'.encode("utf-8")
            req_join = urllib.request.Request(connect_url, data=join_payload, headers={**headers, "Content-Type": "text/plain;charset=UTF-8"})
            with urllib.request.urlopen(req_join, timeout=15) as resp_join:
                print(f"Join sent status: {resp_join.status}")

            # Step 5: Emit 'history' event: 42["history", 9995585]
            history_payload = f'42["history",{GAME_ID}]'.encode("utf-8")
            req_hist = urllib.request.Request(connect_url, data=history_payload, headers={**headers, "Content-Type": "text/plain;charset=UTF-8"})
            with urllib.request.urlopen(req_hist, timeout=15) as resp_hist:
                print(f"History request sent status: {resp_hist.status}")

            # Step 6: Poll all incoming data packets until 'history_end'
            all_packets = []
            print("Polling incoming data packets...")
            for i in range(10):
                req_poll_data = urllib.request.Request(connect_url, headers=headers)
                try:
                    with urllib.request.urlopen(req_poll_data, timeout=15) as resp_data:
                        data_str = resp_data.read().decode("utf-8")
                        if not data_str:
                            continue
                        print(f"Poll {i}: received {len(data_str)} chars")
                        all_packets.append(data_str)
                        if "history_end" in data_str:
                            print("Reached history_end!")
                            break
                except Exception as e:
                    print(f"Poll error: {e}")
                    break

            # Save full raw stream
            full_log_path = Path(f"reports/source_audit/samples/socket_raw_game_{GAME_ID}.txt")
            full_log_path.write_text("\n---\n".join(all_packets), encoding="utf-8")
            print(f"Saved raw socket log to {full_log_path}")

if __name__ == "__main__":
    test_engineio_polling()
