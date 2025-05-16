using ModelContextProtocol.Client;

namespace Github;

public class McpClientService(IMcpClientFactory mcpClientFactory)
{
    public async Task<IMcpClient> CreateClient()
    {
        return await mcpClientFactory.CreateMcpClientAsync();
    }
}