using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Base JSON-RPC request.
/// </summary>
public class JsonRpcRequest
{
    [JsonPropertyName("jsonrpc")]
    public string JsonRpc { get; set; } = "2.0";

    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("method")]
    public string Method { get; set; } = null!;

    [JsonPropertyName("params")]
    public object Params { get; set; } = null!;
}