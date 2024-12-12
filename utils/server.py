import asyncio
import websockets
import threading
import json

class Server:
    def __init__(self):
        self.connected_clients = set()
        self._event_loop = None
        self._events = []

    def notify_clients_threadsafe(self, event_message, save_event=True):
        if self._event_loop is None:
            print("Warning: Event loop is not running. Cannot notify clients.")
            return

        asyncio.run_coroutine_threadsafe(self._notify_clients(event_message, save_event), self._event_loop)

    async def _notify_clients(self, event_message, save_event=True):
        if save_event:
            self._events.append(event_message)

        if self.connected_clients:
            for client in self.connected_clients:
                await client.send(json.dumps(event_message))

    async def _handler(self, websocket):
        self.connected_clients.add(websocket)

        await websocket.send(json.dumps({
            "type": "catchup",
            "events": self._events,
        }))

        try:
            async for message in websocket:
                print(f"Received: {message}")
        except websockets.exceptions.ConnectionClosedError:
            pass
        finally:
            self.connected_clients.remove(websocket)

    async def _run(self):
        self._event_loop = asyncio.get_event_loop()
        async with websockets.serve(self._handler, host='0.0.0.0', port=8000) as server:
            await server.serve_forever()

    def _start(self):
        asyncio.run(self._run())

    def start_on_separate_thread(self):
        server_thread = threading.Thread(target=self._start, daemon=True)
        server_thread.start()
