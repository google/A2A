using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Status of a task.
/// </summary>
public class TaskStatus
{
    [JsonPropertyName("state")]
    public TaskState State { get; set; }

    [JsonPropertyName("message")]
    public Message Message { get; set; } = null!;

    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; set; }
}