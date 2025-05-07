using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// JSON-RPC error.
/// </summary>
public class JsonRpcError
{
    public JsonRpcError(int code, string message, string data = null!)
    {
        Code = code;
        Message = message;
        Data = data;
    }


    [JsonPropertyName("code")]
    public int Code { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = null!;

    [JsonPropertyName("data")]
    public object Data { get; set; } = null!;
}