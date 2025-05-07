using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Represents the content of a file, either as base64 encoded bytes or a URI.
/// </summary>
public class FileContent
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = null!;

    [JsonPropertyName("mimeType")]
    public string MimeType { get; set; } = null!;

    [JsonPropertyName("bytes")]
    public string Bytes { get; set; } = null!;

    [JsonPropertyName("uri")]
    public string Uri { get; set; } = null!;
}