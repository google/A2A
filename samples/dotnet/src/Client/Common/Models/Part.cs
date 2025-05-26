using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Base class for parts of a message.
/// </summary>
public class Part
{
    protected Part()
    {
    }

    [JsonPropertyName("type")]
    public string Type { get; set; } = null!;

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}