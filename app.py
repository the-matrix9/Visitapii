from flask import Flask, jsonify, request
import aiohttp
import asyncio
import json
from byte import encrypt_api, Encrypt_ID
from visit_count_pb2 import Info

app = Flask(__name__)


def load_tokens(server_name):
    server_name = server_name.upper()
    try:
        if server_name == "IND":
            path = "token_ind.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            path = "token_br.json"
        else:
            path = "token_bd.json"

        with open(path, "r") as f:
            data = json.load(f)

        tokens = [item["token"] for item in data if "token" in item and item["token"].strip() not in ["", "N/A"]]
        return tokens
    except Exception as e:
        print(f"❌ Token load error: {e}")
        return []


def get_url(server_name):
    server_name = server_name.upper()
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        return "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"


def parse_protobuf_response(response_data):
    try:
        info = Info()
        info.ParseFromString(response_data)
        return {
            "uid": info.AccountInfo.UID,
            "nickname": info.AccountInfo.PlayerNickname,
            "likes": info.AccountInfo.Likes,
            "region": info.AccountInfo.PlayerRegion,
            "level": info.AccountInfo.Levels
        }
    except Exception:
        return None


async def visit(session, url, token, uid, data):
    headers = {
        "ReleaseVersion": "OB54",
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "Host": url.replace("https://", "").split("/")[0]
    }
    try:
        async with session.post(url, headers=headers, data=data, ssl=False, timeout=5) as resp:
            if resp.status == 200:
                return True, await resp.read()
            return False, None
    except:
        return False, None


async def process_visits(tokens, uid, server_name):
    url = get_url(server_name)
    target = len(tokens)
    total_success = 0
    player_info = None

    encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
    payload = bytes.fromhex(encrypted)

    async with aiohttp.ClientSession() as session:
        tasks = [visit(session, url, token, uid, payload) for token in tokens]
        results = await asyncio.gather(*tasks)

        for success, response in results:
            if success:
                total_success += 1
                if player_info is None:
                    player_info = parse_protobuf_response(response)

    return total_success, target, player_info


@app.route('/token_info', methods=['GET'])
def token_info():
    server = request.args.get('server', 'BD').upper()
    tokens = load_tokens(server)
    return jsonify({
        "server": server,
        "total_tokens": len(tokens),
        "status": "Ready" if tokens else "No tokens found"
    })


@app.route('/visit', methods=['GET'])
def start_visit():
    server = request.args.get('server', 'BD').upper()
    uid = request.args.get('uid')

    if not uid:
        return jsonify({"error": "UID is required"}), 400

    tokens = load_tokens(server)
    if not tokens:
        return jsonify({"error": f"No tokens found for {server}"}), 500

    print(f"🚀 Processing {len(tokens)} tokens for UID: {uid}")
    
    # asyncio.run 
    success, total, p_info = asyncio.run(process_visits(tokens, uid, server))

    if p_info:
        return jsonify({
            "status": "Success" if success > 0 else "Failed",
            "nickname": p_info['nickname'],
            "uid": p_info['uid'],
            "level": p_info['level'],
            "likes_before": p_info['likes'],
            "sent_success": success,
            "total_tried": total
        })
    else:
        return jsonify({"error": "All tokens failed or Invalid UID", "success": 0, "tried": total}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=True)

#🔥Owner @Sheihk_Anamul

#🔥 FIXED BY @Sheihk-Anamu

#TELEGRAM : @Sheihk-Anamul

#OB53 
#SHEIHK VISIT API 