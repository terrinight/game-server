import asyncio
import websockets
import json
import random
import os

async def game_handler(websocket):
    snake = [{"x": 10, "y": 10}]
    
    # Sử dụng Hàng đợi (Queue) để lưu trữ các lần bấm phím liên tiếp
    direction_queue = ["right"]
    current_dir = "right"
    
    apple = {"x": random.randint(0, 19), "y": random.randint(0, 19)}
    score = 0
    running = True
    game_state = "waiting"

    async def listen():
        nonlocal direction_queue, running, game_state
        try:
            async for message in websocket:
                data = json.loads(message)
                action = data.get("action")
                
                if action == "start" and game_state != "playing":
                    game_state = "playing"
                    
                elif game_state == "playing":
                    # Lấy hướng cuối cùng trong hàng đợi để so sánh, tránh lỗi quay đầu 180 độ
                    last_dir = direction_queue[-1] if len(direction_queue) > 0 else current_dir
                    
                    # Nạp lệnh vào Hàng đợi thay vì ghi đè ngay lập tức
                    if action == "up" and last_dir != "down": direction_queue.append("up")
                    elif action == "down" and last_dir != "up": direction_queue.append("down")
                    elif action == "left" and last_dir != "right": direction_queue.append("left")
                    elif action == "right" and last_dir != "left": direction_queue.append("right")
        except:
            running = False

    async def game_loop():
        nonlocal snake, direction_queue, current_dir, apple, score, running, game_state
        try:
            while running:
                if game_state == "playing":
                    # Lấy lệnh điều khiển đầu tiên trong hàng đợi ra để xử lý
                    if len(direction_queue) > 0:
                        current_dir = direction_queue.pop(0)

                    head = snake[0].copy()
                    
                    if current_dir == "up": head["y"] -= 1
                    elif current_dir == "down": head["y"] += 1
                    elif current_dir == "left": head["x"] -= 1
                    elif current_dir == "right": head["x"] += 1

                    if head["x"] < 0 or head["x"] > 19 or head["y"] < 0 or head["y"] > 19 or head in snake:
                        game_state = "gameover"
                        await websocket.send(json.dumps({"snake": snake, "apple": apple, "score": score, "status": game_state}))
                        
                        snake = [{"x": 10, "y": 10}]
                        direction_queue = ["right"]
                        current_dir = "right"
                        score = 0
                        apple = {"x": random.randint(0, 19), "y": random.randint(0, 19)}
                        
                        await asyncio.sleep(1.5)
                        game_state = "waiting"
                        continue

                    snake.insert(0, head)
                    if head["x"] == apple["x"] and head["y"] == apple["y"]:
                        score += 1
                        apple = {"x": random.randint(0, 19), "y": random.randint(0, 19)}
                    else:
                        snake.pop()

                await websocket.send(json.dumps({"snake": snake, "apple": apple, "score": score, "status": game_state}))
                
                # Tăng tốc độ game để giảm cảm giác trễ (0.09 thay vì 0.15)
                await asyncio.sleep(0.09)
        except:
            running = False

    listener = asyncio.create_task(listen())
    loop = asyncio.create_task(game_loop())
    await asyncio.wait([listener, loop], return_when=asyncio.FIRST_COMPLETED)

async def main():
    PORT = int(os.environ.get("PORT", 8765))
    async with websockets.serve(game_handler, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
