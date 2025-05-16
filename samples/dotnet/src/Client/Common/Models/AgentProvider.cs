using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Information about the provider of an agent.
/// </summary>
public class AgentProvider
{
    [JsonPropertyName("organization")]
    public string Organization { get; set; } = null!;

    [JsonPropertyName("url")]
    public string Url { get; set; } = null!;
}