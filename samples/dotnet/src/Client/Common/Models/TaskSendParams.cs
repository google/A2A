using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Parameters for sending a task.
/// </summary>
public class TaskSendParams
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("sessionId")]
    public string SessionId { get; set; } = null!;

    [JsonPropertyName("message")]
    public Message Message { get; set; } = null!;

    [JsonPropertyName("pushNotification")]
    public PushNotificationConfig PushNotification { get; set; } = null!;

    [JsonPropertyName("historyLength")]
    public int? HistoryLength { get; set; }

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = null!;
}