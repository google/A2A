using Client.Common.Models;

namespace Client.Common.Helpers;

/// <summary>
/// Helper methods for creating A2A protocol messages and parts.
/// </summary>
public static class A2AHelpers
{
    /// <summary>
    /// Creates a user message with text content.
    /// </summary>
    /// <param name="text">The text content.</param>
    /// <param name="metadata">Optional metadata.</param>
    /// <returns>A message object.</returns>
    public static Message CreateUserTextMessage(string text, Dictionary<string, object> metadata = null!)
    {
        return new Message
        {
            Role = "user",
            Parts = [CreateTextPart(text)],
            Metadata = metadata
        };
    }

    /// <summary>
    /// Creates an agent message with text content.
    /// </summary>
    /// <param name="text">The text content.</param>
    /// <param name="metadata">Optional metadata.</param>
    /// <returns>A message object.</returns>
    public static Message CreateAgentTextMessage(string text, Dictionary<string, object> metadata = null!)
    {
        return new Message
        {
            Role = "agent",
            Parts = [CreateTextPart(text)],
            Metadata = metadata
        };
    }

    /// <summary>
    /// Creates a text part.
    /// </summary>
    /// <param name="text">The text content.</param>
    /// <param name="metadata">Optional metadata.</param>
    /// <returns>A text part.</returns>
    public static TextPart CreateTextPart(string text, Dictionary<string, object> metadata = null!)
    {
        return new TextPart
        {
            Text = text,
            Metadata = metadata
        };
    }

    /// <summary>
    /// Creates a file part from a file path.
    /// </summary>
    /// <param name="filePath">The path to the file.</param>
    /// <param name="mimeType">The MIME type of the file.</param>
    /// <param name="metadata">Optional metadata.</param>
    /// <returns>A file part.</returns>
    public static async Task<FilePart> CreateFilePartFromPathAsync(
        string filePath,
        string? mimeType = null,
        Dictionary<string, object> metadata = null!)
    {
        byte[] fileBytes = await File.ReadAllBytesAsync(filePath);
        string base64Content = Convert.ToBase64String(fileBytes);

        return new FilePart
        {
            File = new FileContent
            {
                Name = Path.GetFileName(filePath),
                MimeType = mimeType ?? GetMimeTypeFromExtension(Path.GetExtension(filePath)),
                Bytes = base64Content
            },
            Metadata = metadata
        };
    }

    /// <summary>
    /// Creates a file part from a URI.
    /// </summary>
    /// <param name="uri">The URI to the file.</param>
    /// <param name="fileName">The name of the file.</param>
    /// <param name="mimeType">The MIME type of the file.</param>
    /// <param name="metadata">Optional metadata.</param>
    /// <returns>A file part.</returns>
    public static FilePart CreateFilePartFromUri(
        string uri,
        string fileName,
        string? mimeType = null,
        Dictionary<string, object> metadata = null!)
    {
        return new FilePart
        {
            File = new FileContent
            {
                Name = fileName,
                MimeType = mimeType ?? GetMimeTypeFromExtension(Path.GetExtension(fileName)),
                Uri = uri
            },
            Metadata = metadata
        };
    }

    /// <summary>
    /// Creates a data part.
    /// </summary>
    /// <param name="data">The data.</param>
    /// <param name="metadata">Optional metadata.</param>
    /// <returns>A data part.</returns>
    public static DataPart CreateDataPart(
        Dictionary<string, object> data,
        Dictionary<string, object> metadata = null!)
    {
        return new DataPart
        {
            Data = data,
            Metadata = metadata
        };
    }

    /// <summary>
    /// Gets a MIME type from a file extension.
    /// </summary>
    /// <param name="extension">The file extension, including the leading dot.</param>
    /// <returns>The MIME type, or "application/octet-stream" if unknown.</returns>
    private static string GetMimeTypeFromExtension(string extension)
    {
        if (string.IsNullOrEmpty(extension))
        {
            return "application/octet-stream";
        }

        extension = extension.ToLowerInvariant();

        // Common MIME types
        return extension switch
        {
            ".txt" => "text/plain",
            ".html" or ".htm" => "text/html",
            ".css" => "text/css",
            ".js" => "application/javascript",
            ".json" => "application/json",
            ".xml" => "application/xml",
            ".jpg" or ".jpeg" => "image/jpeg",
            ".png" => "image/png",
            ".gif" => "image/gif",
            ".svg" => "image/svg+xml",
            ".pdf" => "application/pdf",
            ".doc" => "application/msword",
            ".docx" => "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls" => "application/vnd.ms-excel",
            ".xlsx" => "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt" => "application/vnd.ms-powerpoint",
            ".pptx" => "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".zip" => "application/zip",
            ".mp3" => "audio/mpeg",
            ".mp4" => "video/mp4",
            _ => "application/octet-stream"
        };
    }
}