using ModelContextProtocol.Client;

namespace Github;

public interface IMcpClientFactory
{
    Task<IMcpClient> CreateMcpClientAsync();
}