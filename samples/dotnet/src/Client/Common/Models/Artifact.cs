using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Artifact produced during a task.
/// </summary>
public class Artifact
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = null!;

    [JsonPropertyName("description")]
    public string Description { get; set; } = null!;

    [JsonPropertyName("parts")]
    public List<Part> Parts { get; set; } = null!;

    [JsonPropertyName("index")]
    public int Index { get; set; } = 0;

    [JsonPropertyName("append")]
    public bool Append { get; set; }

    [JsonPropertyName("lastChunk")]
    public bool LastChunk { get; set; }

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}