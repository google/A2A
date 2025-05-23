using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Authentication information.
/// </summary>
public class AuthenticationInfo
{
    [JsonPropertyName("schemes")]
    public List<string> Schemes { get; set; } = null!;

    [JsonPropertyName("credentials")]
    public string Credentials { get; set; } = null!;
}