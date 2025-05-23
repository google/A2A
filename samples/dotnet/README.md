# GitHub Agent Sample with Semantic Kernel, MCP, and A2A

This project demonstrates how to create an intelligent GitHub agent using C# and .NET 8, combining three powerful AI technologies:

1. [Microsoft Semantic Kernel](https://github.com/microsoft/semantic-kernel) - A lightweight SDK for integrating AI Large Language Models (LLMs) with conventional programming languages
2. [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/servers) - A protocol for providing models with contextual information and tools
3. [Google Agent-to-Agent (A2A)](https://github.com/google/A2A) - A protocol for agent communication and task management

## Project Overview

This sample application creates a GitHub agent capable of answering questions about repositories by leveraging the following components:

- **Semantic Kernel** - Orchestrates the agent and LLM interactions
- **MCP GitHub Server** - Provides tools for GitHub repository analysis
- **A2A Client** - Enables standardized agent communication

## Architecture

The project follows a modular design with clear separation of concerns:

```
├── Kernel Building
│   └── KernelBuilder.cs       # Creates and configures the Semantic Kernel instance
│
├── Agent Components  
│   ├── AgentFactory.cs        # Creates GitHub agent instances
│   └── AgentService.cs        # Processes queries through the agent
│
├── MCP Integration
│   ├── IMcpClientFactory.cs   # Interface for MCP client creation
│   ├── McpClientFactory.cs    # Creates MCP client instances
│   ├── McpClientService.cs    # Service for managing MCP client
│   └── ToolService.cs         # Retrieves GitHub tools from MCP
│
├── Execution Components
│   ├── ExecutionSettingsProvider.cs  # Configures LLM execution settings
│   └── PromptExecutor.cs             # Executes prompts against the kernel
│
└── A2A Integration
    └── A2AClient.cs           # Client for A2A protocol communication
```

## Core Components

### Semantic Kernel Setup

The `KernelBuilder` class configures the Semantic Kernel with OpenAI integration and adds GitHub-specific functions:

```csharp
// KernelBuilder.cs
public Kernel BuildKernel(IList<McpClientTool> tools)
{
    IKernelBuilder builder = Kernel.CreateBuilder();
    builder.Services
        .AddLogging(c => c.AddDebug().SetMinimumLevel(LogLevel.Trace))
        .AddOpenAIChatCompletion(
            modelId: Environment.GetEnvironmentVariable("OPENAI_MODEL_NAME") ?? "gpt-4o-mini",
            apiKey: "YOUR_API_KEY");

    Kernel kernel = builder.Build();
    kernel.Plugins.AddFromFunctions("GitHub", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

    return kernel;
}
```

### Agent Creation

The `AgentFactory` creates a GitHub-specific agent with appropriate instructions:

```csharp
// AgentFactory.cs
public ChatCompletionAgent CreateGithubAgent()
{
    OpenAIPromptExecutionSettings executionSettings = ExecutionSettingsProvider.GetOpenAiSettings();

    return new ChatCompletionAgent
    {
        Instructions = "Answer questions about GitHub repositories.",
        Name = "GitHubAgent",
        Kernel = kernel,
        Arguments = new KernelArguments(executionSettings),
    };
}
```

### MCP Integration

The project uses the Model Context Protocol to provide the agent with GitHub-specific tools:

```csharp
// McpClientFactory.cs
public async Task<IMcpClient> CreateMcpClientAsync()
{
    return await ModelContextProtocol.Client.McpClientFactory.CreateAsync(
        new StdioClientTransport(new StdioClientTransportOptions
        {
            Name = "MCPServer",
            Command = "npx",
            Arguments = ["-y", "@modelcontextprotocol/server-github"],
        }));
}
```

### A2A Protocol Support

The `A2AClient` implements the Agent-to-Agent protocol for standardized communication:

```csharp
// A2AClient.cs (abbreviated)
public class A2AClient : IDisposable
{
    // Implements JSON-RPC methods for agent communication
    public async Task<AgentCard> GetAgentCardAsync(CancellationToken cancellationToken = default)
    {
        // Gets agent capabilities
    }
    
    public async Task<System.Threading.Tasks.Task> SendTaskAsync(
        TaskSendParams parameters,
        CancellationToken cancellationToken = default)
    {
        // Sends tasks to other agents
    }
    
    // Additional methods for task management and streaming updates
}
```

## Getting Started

### Prerequisites

- .NET 8 SDK
- Node.js (for MCP GitHub server)
- OpenAI API key

### Environment Setup

1. Clone this repository
2. Set up environment variables:
   ```
   OPENAI_MODEL_NAME=gpt-4o-mini
   ```

### Running the Sample

1. Build the solution:
   ```
   dotnet build
   ```

2. Run the application:
   ```
   dotnet run
   ```

## Usage Example

```csharp
// Example usage
var mcpClientFactory = new McpClientFactory();
var mcpClientService = new McpClientService(mcpClientFactory);
var mcpClient = await mcpClientService.CreateClient();

var toolService = new ToolService(mcpClient);
var tools = await toolService.GetGithubTools();

var kernelBuilder = new KernelBuilder(configuration);
var kernel = kernelBuilder.BuildKernel(tools);

var agentFactory = new AgentFactory(kernel);
var agent = agentFactory.CreateGithubAgent();

var agentService = new AgentService(agent);
var response = await agentService.ProcessQuery("What are the recent commits in repository X?");

Console.WriteLine(response.Content);
```

## How It Works

1. The application builds a Semantic Kernel with OpenAI LLM integration
2. It creates an MCP client that connects to the GitHub server
3. GitHub tools are retrieved from the MCP server and added to the kernel
4. A specialized GitHub agent is created with appropriate instructions
5. User queries are processed through the agent, which uses GitHub tools as needed
6. The A2A client can be used to communicate with other agents in a standardized way

## Advanced Features

### Prompt Execution

The `PromptExecutor` allows direct execution of prompts against the kernel:

```csharp
var executor = new PromptExecutor(kernel);
await executor.ExecutePrompt("List the top contributors for repository X");
```

### Execution Settings

The `ExecutionSettingsProvider` configures the LLM behavior:

```csharp
public static OpenAIPromptExecutionSettings GetOpenAiSettings()
{
    return new OpenAIPromptExecutionSettings
    {
        Temperature = 0,
        FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new FunctionChoiceBehaviorOptions { RetainArgumentTypes = true })
    };
}
```

## Resources

- [Semantic Kernel Documentation](https://github.com/microsoft/semantic-kernel)
- [Model Context Protocol](https://github.com/modelcontextprotocol/servers)
- [Google A2A Protocol](https://github.com/google/A2A)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
