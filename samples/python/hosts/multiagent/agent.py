from .host_agent import HostAgent


root_agent = HostAgent(['http://localhost:10000']).create_agent()
