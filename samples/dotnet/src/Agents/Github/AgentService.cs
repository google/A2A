using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace Github;

public class AgentService(ChatCompletionAgent agent)
{
    public async Task<ChatMessageContent> ProcessQuery(string query, CancellationToken cancellationToken)
    {
        ChatMessageContent response = await agent.InvokeAsync(query, cancellationToken: cancellationToken).FirstAsync(cancellationToken: cancellationToken);
        return response;
    }
}