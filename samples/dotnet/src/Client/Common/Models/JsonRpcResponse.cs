using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Base JSON-RPC response.
/// </summary>
public class JsonRpcResponse<T>
{
    [JsonPropertyName("jsonrpc")]
    public string JsonRpc { get; set; } = "2.0";

    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("result")]
    public T Result { get; set; } = default!;

    [JsonPropertyName("error")]
    public JsonRpcError Error { get; set; } = null!;
}