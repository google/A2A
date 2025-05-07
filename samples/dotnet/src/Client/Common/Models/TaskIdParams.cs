using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Parameters for a task ID.
/// </summary>
public class TaskIdParams
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}