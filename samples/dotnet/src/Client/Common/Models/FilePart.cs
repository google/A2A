using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// File part of a message.
/// </summary>
public class FilePart : Part
{
    public FilePart()
    {
        Type = "file";
    }

    [JsonPropertyName("file")]
    public FileContent File { get; set; } = null!;
}