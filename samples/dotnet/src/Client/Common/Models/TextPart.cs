using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Text part of a message.
/// </summary>
public class TextPart : Part
{
    public TextPart()
    {
        Type = "text";
    }

    [JsonPropertyName("text")]
    public string Text { get; set; } = null!;
}