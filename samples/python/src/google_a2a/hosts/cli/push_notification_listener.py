import asyncio
import threading

from common.utils.push_notification_auth import PushNotificationReceiverAuth

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response

import traceback

class PushNotificationListener():
    def __init__(self, host, port, notification_receiver_auth: PushNotificationReceiverAuth):
        self.host = host
        self.port = port
        self.notification_receiver_auth = notification_receiver_auth
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=lambda loop: loop.run_forever(), args=(self.loop,)
        )
        self.thread.daemon = True
        self.thread.start()

    def start(self):
        try:
            # Need to start server in separate thread as current thread
            # will be blocked when it is waiting on user prompt.
            asyncio.run_coroutine_threadsafe(
                self.start_server(),
                self.loop,
            )
            print("======= push notification listener started =======")
        except Exception as e:
            print(e)

    async def start_server(self):
        import uvicorn

        self.app = Starlette()
        self.app.add_route(
            "/notify", self.handle_notification, methods=["POST"]
        )
        self.app.add_route(
            "/notify", self.handle_validation_check, methods=["GET"]
        )
        
        config = uvicorn.Config(self.app, host=self.host, port = self.port, log_level="critical")
        self.server = uvicorn.Server(config)
        await self.server.serve()
    
    async def handle_validation_check(self, request: Request):
        validation_token = request.query_params.get("validationToken")
        print(f"\npush notification verification received => \n{validation_token}\n")

        if not validation_token:
            return Response(status_code=400)
            
        return Response(content=validation_token, status_code=200)
    
    async def handle_notification(self, request: Request):
        data = await request.json()
        try:
            if not await self.notification_receiver_auth.verify_push_notification(request):
                print("push notification verification failed")
                return
        except Exception as e:
            print(f"error verifying push notification: {e}")
            print(traceback.format_exc())
            return
            
        print(f"\npush notification received => \n{data}\n")
        return Response(status_code=200)
