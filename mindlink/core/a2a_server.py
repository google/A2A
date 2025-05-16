from typing import List, Dict, Any
from a2a.agent import A2AAgent, AgentCard
from a2a.server import A2AServer
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import uuid

class MindLinkA2AServer(HTTPServer):
    def __init__(self, agents: List[A2AAgent], port: int = 8080, bind_address: str = "localhost"):
        self.agents: Dict[str, A2AAgent] = {agent.agent_card.id: agent for agent in agents}
        self.port = port
        self.bind_address = bind_address
        self.server_address = (bind_address, port)
        super().__init__(self.server_address, self._RequestHandler)
        self._thread: threading.Thread = None

    class _RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"MindLink A2A Server is running")
            elif self.path.startswith("/agent_card/"):
                agent_id = self.path.split("/")[-1]
                agent = self.server.agents.get(agent_id)
                if agent:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(agent.agent_card.model_dump()).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Agent not found")
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Not found")

        def do_POST(self):
            if self.path.startswith("/agent/"):
                agent_id = self.path.split("/")[-1]
                agent = self.server.agents.get(agent_id)
                if agent:
                    content_length = int(self.headers["Content-Length"])
                    post_data = self.rfile.read(content_length)
                    try:
                        data = json.loads(post_data)
                        method_name = data.get("method")
                        params = data.get("params", {})
                        result = agent.call_agent_method(method_name, params)
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode("utf-8"))
                    except Exception as e:
                        self.send_response(500)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(str(e).encode("utf-8"))

                else:
                    self.send_response(404)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Agent not found")
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Not found")


        def log_message(self, format, *args):
            """Override log message to prevent console spam."""
            return

    def run(self):
        self._thread = threading.Thread(target=self.serve_forever)
        self._thread.daemon = True
        self._thread.start()
        print(f"MindLink A2A Server running at http://{self.bind_address}:{self.port}")
        for agent_id, agent in self.agents.items():
            print(f"Agent: {agent.agent_card.name} : http://{self.bind_address}:{self.port}/agent_card/{agent_id}")


    def stop(self):
        if self._thread:
            self.shutdown()
            self._thread.join()