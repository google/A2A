using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Authentication schemes and credentials for an agent.
/// </summary>
public class AgentAuthentication
{
    [JsonPropertyName("schemes")]
    public List<string> Schemes { get; set; } = null!;

    [JsonPropertyName("credentials")]
    public string Credentials { get; set; } = null!;
}