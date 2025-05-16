using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Task status update event.
/// </summary>
public class TaskStatusUpdateEvent
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("status")]
    public TaskStatus Status { get; set; } = null!;

    [JsonPropertyName("final")]
    public bool Final { get; set; }

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}