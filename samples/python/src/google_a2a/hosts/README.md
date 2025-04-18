## Hosts

Sample apps or agents that are A2A clients that work with A2A servers. 

* [CLI](/samples/python/hosts/cli)  
  Command line tool to interact with an A2A server. Specify the server location on the command line. The CLI client looks up the agent card and then performs task completion in a loop based on command line inputs. 

* [Orchestrator Agent](/samples/python/hosts/multiagent)  
An Agent that speaks A2A and can delegate tasks to remote agents. Built on the Google ADK for demonstration purposes. Includes a "Host Agent" that maintains a collection of "Remote Agents". The Host Agent is itself an agent and can delegate tasks to one or more Remote Agents. Each RemoteAgent is an A2AClient that delegates to an A2A Server. 

* [MultiAgent Web Host](/demo/README.md)  
*This lives in the [demo](/demo/README.md) directory*  
A web app that visually shows A2A conversations with multiple agents (using the [Orchestrator Agent](/samples/python/hosts/multiagent)). Will render text, image, and webform artifacts. Has a separate tab to visualize task state and history as well as known agent cards. 