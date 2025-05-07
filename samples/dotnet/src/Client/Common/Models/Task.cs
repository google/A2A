using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Task information.
/// </summary>
public class Task
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("sessionId")]
    public string SessionId { get; set; } = null!;

    [JsonPropertyName("status")]
    public TaskStatus Status { get; set; } = null!;

    [JsonPropertyName("artifacts")]
    public List<Artifact> Artifacts { get; set; } = null!;

    [JsonPropertyName("history")]
    public List<Message> History { get; set; } = null!;

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}