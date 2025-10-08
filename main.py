import sys
import asyncio
import json
import uuid
import time
from typing import Dict, Tuple

import pygame
import websockets
from websockets.sync.client import connect


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8080
FPS = 60

screen: pygame.Surface | None = None
clock: pygame.time.Clock | None = None
game_state: Dict[str, Dict] = {}
websocket: websockets.ClientConnection | None = None
is_connected = False
client_id = str(uuid.uuid4())

inu = pygame.image.load("inu.webp")


async def connect_and_handle_ws():
    global websocket, is_connected, game_state

    try:
        async with websockets.connect(f"wss://{BACKEND_HOST}:{BACKEND_PORT}/ws/{client_id}") as ws:
            websocket = ws
            is_connected = True
            while True:
                try:
                    async for raw_message in websocket:
                        if isinstance(raw_message, bytes):
                            raw_message = raw_message.decode("utf-8")
                        data = json.loads(raw_message)
                        if data.get("type") in {"init", "update"}:
                            state = data.get("state", {})
                            players_state = state.get("players", {})
                            game_state.clear()
                            game_state.update(players_state)
                except websockets.exceptions.ConnectionClosedOK:
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"Connection closed with error: {e}")
                    break
                except asyncio.CancelledError:
                    print("WebSocket receive task cancelled.")
                    break
    except ConnectionRefusedError:
        print("Connection refused. Is the server running?")
    except Exception as e:
        print("Error connecting to WebSocket:", e)
    finally:
        is_connected = False
        websocket = None
        print("WebSocket connection closed.")


async def send_message_async(message: Dict):
    global websocket, is_connected
    if is_connected and websocket:
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            print("Error sending message:", e)


def animation():
    global screen, game_state, clock, websocket
    screen.fill((0, 0, 0))
    for state in game_state.values():
        x = state.get("x")
        y = state.get("y")
        width = state.get("width")
        height = state.get("height")

        if None in {x, y, width, height}:
            continue

        color = state.get("color", "blue")
        if isinstance(color, str):
            color_tuple = name_to_color(color)
        else:
            color_tuple = tuple(color)
        rect = pygame.Rect(x, y, width, height)
        mini_inu = pygame.transform.scale(inu, (width, height))
        screen.blit(mini_inu, (x, y))
        # プレイヤーの位置(x, y)を画面右上に表示する
        font = pygame.font.Font(None, 24)
        position_text = font.render(f"({x}, {y})", True, (255, 255, 255))
        screen.blit(position_text, (SCREEN_WIDTH - 100, 10))
    pygame.display.flip()


async def pygame_main_loop():
    global screen, clock, game_state

    running = True
    current_time = 0
    while running:
        last_time, current_time = current_time, time.time()
        await asyncio.sleep(min(1 / FPS - (current_time - last_time - 1 / FPS), 1 / FPS))  # tick
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                input_state = {
                    "up": bool(keys[pygame.K_UP]),
                    "down": bool(keys[pygame.K_DOWN]),
                    "left": bool(keys[pygame.K_LEFT]),
                    "right": bool(keys[pygame.K_RIGHT]),
                }
                if input_state["up"] or input_state["down"] or input_state["left"] or input_state["right"]:
                    print("Sending input:", input_state)
                    asyncio.create_task(send_message_async({
                        "type": "move",
                        "keys": input_state
                    }))
            else:
                input_state = {
                    "up": False,
                    "down": False,
                    "left": False,
                    "right": False,
                }
                asyncio.create_task(send_message_async({
                    "type": "move",
                    "keys": input_state
                }))
        animation()

    print("Exiting Pygame loop.")
    pygame.quit()
    sys.exit()


async def main():
    await asyncio.gather(
        connect_and_handle_ws(),
        pygame_main_loop()
    )


def name_to_color(color_name: str) -> Tuple[int, int, int]:
    try:
        color = pygame.Color(color_name)
        return (color.r, color.g, color.b)
    except ValueError:
        return (0, 0, 255)


if __name__ == "__main__":
    try:
        pygame.init()
        pygame.display.set_caption("Async Pygame Example")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        clock = pygame.time.Clock()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted.")
    except SystemExit:
        pass
