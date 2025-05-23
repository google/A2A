using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Parameters for querying a task.
/// </summary>
public class TaskQueryParams
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("historyLength")]
    public int? HistoryLength { get; set; }

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}