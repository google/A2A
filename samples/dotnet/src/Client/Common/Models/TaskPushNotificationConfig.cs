using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Task push notification configuration.
/// </summary>
public class TaskPushNotificationConfig
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("pushNotificationConfig")]
    public PushNotificationConfig PushNotificationConfig { get; set; } = null!;
}