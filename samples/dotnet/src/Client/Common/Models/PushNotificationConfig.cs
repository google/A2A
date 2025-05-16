using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Push notification configuration.
/// </summary>
public class PushNotificationConfig
{
    [JsonPropertyName("url")]
    public string Url { get; set; } = null!;

    [JsonPropertyName("token")]
    public string Token { get; set; } = null!;

    [JsonPropertyName("authentication")]
    public AuthenticationInfo Authentication { get; set; } = null!;
}