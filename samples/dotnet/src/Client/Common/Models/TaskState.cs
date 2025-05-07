using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// State of a task.
/// </summary>
public enum TaskState
{
    [JsonPropertyName("submitted")]
    SUBMITTED,

    [JsonPropertyName("working")]
    WORKING,

    [JsonPropertyName("input-required")]
    INPUT_REQUIRED,

    [JsonPropertyName("completed")]
    COMPLETED,

    [JsonPropertyName("canceled")]
    CANCELED,

    [JsonPropertyName("failed")]
    FAILED,

    [JsonPropertyName("unknown")]
    UNKNOWN
}