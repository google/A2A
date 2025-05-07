using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Data part of a message.
/// </summary>
public class DataPart : Part
{
    public DataPart()
    {
        Type = "data";
    }

    [JsonPropertyName("data")]
    public Dictionary<string, object> Data { get; set; } = null!;
}