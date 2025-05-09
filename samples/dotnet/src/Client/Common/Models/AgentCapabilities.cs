using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Capabilities of an agent.
/// </summary>
public class AgentCapabilities
{
    [JsonPropertyName("streaming")]
    public bool Streaming { get; set; } = false;

    [JsonPropertyName("pushNotifications")]
    public bool PushNotifications { get; set; } = false;

    [JsonPropertyName("stateTransitionHistory")]
    public bool StateTransitionHistory { get; set; } = false;
}