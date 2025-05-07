using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Task artifact update event.
/// </summary>
public class TaskArtifactUpdateEvent
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("artifact")]
    public Artifact Artifact { get; set; } = null!;

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}