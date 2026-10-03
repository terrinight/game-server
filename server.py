import asyncio
import websockets
import json
import random
import os

player = {"x": 5, "y": 5}
apple = {"x": random.randint(0, 9), "y": random.randint(0, 9)}
score = 0

async def game_handler(websocket):
    global score
    await websocket.send(json.dumps({"player": player, "apple": apple, "score": score}))
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "up" and player["y"] > 0: player["y"] -= 1
            elif action == "down" and player["y"] < 9: player["y"] += 1
            elif action == "left" and player["x"] > 0: player["x"] -= 1
            elif action == "right" and player["x"] < 9: player["x"] += 1
            
            if player["x"] == apple["x"] and player["y"] == apple["y"]:
                score += 1
                apple = {"x": random.randint(0, 9), "y": random.randint(0, 9)}
            
            await websocket.send(json.dumps({"player": player, "apple": apple, "score": score}))
    except websockets.exceptions.ConnectionClosed:
        pass

async def main():
    # Lấy Port động từ Render cấp phát
    PORT = int(os.environ.get("PORT", 8765))
    # 0.0.0.0 cho phép kết nối từ internet
    async with websockets.serve(game_handler, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
