using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Message from a user or agent.
/// </summary>
public class Message
{
    [JsonPropertyName("role")]
    public string Role { get; set; } = null!;

    [JsonPropertyName("parts")]
    public List<Part> Parts { get; set; } = null!;

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}