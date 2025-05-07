using ModelContextProtocol.Client;

namespace Github;

public class ToolService(IMcpClient mcpClient)
{
    public async Task<IList<McpClientTool>> GetGithubTools()
    {
        return await mcpClient.ListToolsAsync().ConfigureAwait(false);
    }
}