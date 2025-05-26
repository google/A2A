using Client.Common.Models;

namespace Server.Services;

/// <summary>
/// Service for providing the agent card information.
/// </summary>
public class A2ACardService
{
    private readonly IConfiguration _configuration;

    /// <summary>
    /// Initializes a new instance of the <see cref="A2ACardService"/> class.
    /// </summary>
    /// <param name="configuration">The configuration.</param>
    public A2ACardService(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    /// <summary>
    /// Gets the agent card.
    /// </summary>
    /// <returns>The agent card.</returns>
    public AgentCard GetAgentCard()
    {
        return new AgentCard
        {
            Name = "A2A Agent with Semantic Kernel",
            Description = "An A2A-compliant agent built with Semantic Kernel that demonstrates Model Context Protocol and Agent-to-Agent capabilities.",
            Url = _configuration["A2A:AgentUrl"] ?? "http://localhost:5000",
            Provider = new AgentProvider
            {
                Organization = "Demo Organization",
                Url = "https://example.com"
            },
            Version = "0.1.0",
            DocumentationUrl = "https://github.com/microsoft/semantic-kernel",
            Capabilities = new AgentCapabilities
            {
                Streaming = false,
                PushNotifications = false,
                StateTransitionHistory = false
            },
            Authentication = null!,
            DefaultInputModes = ["text/plain"],
            DefaultOutputModes = ["text/plain"],
            Skills =
            [
                new AgentSkill
                {
                    Id = "github-info",
                    Name = "GitHub Information",
                    Description = "Can retrieve and analyze information from GitHub repositories",
                    Tags = ["github", "code", "repository"],
                    Examples = ["Summarize the last commits to a repository", "List issues for a repository"]
                }
            ]
        };
    }
}
