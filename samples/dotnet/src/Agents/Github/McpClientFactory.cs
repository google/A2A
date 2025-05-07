using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Transport;

namespace Github;

public class McpClientFactory : IMcpClientFactory
{
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
}