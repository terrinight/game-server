import asyncio
import websockets
import json
import random
import os

async def game_handler(websocket):
    # Khởi tạo bản đồ 20x20. Rắn giờ là 1 "danh sách" các ô (đang có 1 ô đầu tiên)
    snake = [{"x": 10, "y": 10}]
    direction = "right" # Hướng mặc định lúc mới vào
    apple = {"x": random.randint(0, 19), "y": random.randint(0, 19)}
    score = 0
    running = True

    # 1. Nhiệm vụ 1: Lắng nghe phím bấm liên tục để đổi hướng
    async def listen():
        nonlocal direction, running
        try:
            async for message in websocket:
                data = json.loads(message)
                action = data.get("action")
                
                # Không cho phép quay đầu 180 độ (đang đi trái thì không được bấm phải)
                if action == "up" and direction != "down": direction = "up"
                elif action == "down" and direction != "up": direction = "down"
                elif action == "left" and direction != "right": direction = "left"
                elif action == "right" and direction != "left": direction = "right"
        except:
            running = False

    # 2. Nhiệm vụ 2: Vòng lặp tự động chạy của rắn
    async def game_loop():
        nonlocal snake, direction, apple, score, running
        try:
            while running:
                # Lấy vị trí cái ĐẦU rắn hiện tại
                head = snake[0].copy()
                
                # Tính toán tọa độ cái đầu mới
                if direction == "up": head["y"] -= 1
                elif direction == "down": head["y"] += 1
                elif direction == "left": head["x"] -= 1
                elif direction == "right": head["x"] += 1

                # Luật thua: Đụng 4 bức tường hoặc tự cắn trúng thân mình
                if head["x"] < 0 or head["x"] > 19 or head["y"] < 0 or head["y"] > 19 or head in snake:
                    # Gửi tin báo thua, sau đó reset lại game từ đầu
                    await websocket.send(json.dumps({"snake": snake, "apple": apple, "score": score, "status": "gameover"}))
                    snake = [{"x": 10, "y": 10}]
                    direction = "right"
                    score = 0
                    apple = {"x": random.randint(0, 19), "y": random.randint(0, 19)}
                    await asyncio.sleep(1.5) # Chờ 1.5 giây rồi mới cho chơi tiếp
                    continue

                # Rắn mọc thêm đầu mới
                snake.insert(0, head)

                # Kiểm tra xem có ăn trúng táo không
                if head["x"] == apple["x"] and head["y"] == apple["y"]:
                    score += 1
                    apple = {"x": random.randint(0, 19), "y": random.randint(0, 19)}
                else:
                    # Nếu KHÔNG ăn táo thì xóa cái đuôi cuối cùng (cắt đuôi bù đầu = giữ nguyên độ dài)
                    # Nếu CÓ ăn táo thì không xóa đuôi (rắn sẽ tự dài ra 1 ô)
                    snake.pop()

                # Gửi trạng thái về cho Web
                await websocket.send(json.dumps({"snake": snake, "apple": apple, "score": score, "status": "playing"}))
                
                # Tốc độ rắn chạy (0.15 giây 1 ô). Số càng nhỏ rắn chạy càng nhanh.
                await asyncio.sleep(0.15) 
        except:
            running = False

    # Chạy song song 2 nhiệm vụ trên cùng lúc
    listener = asyncio.create_task(listen())
    loop = asyncio.create_task(game_loop())
    await asyncio.wait([listener, loop], return_when=asyncio.FIRST_COMPLETED)

async def main():
    PORT = int(os.environ.get("PORT", 8765))
    async with websockets.serve(game_handler, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
