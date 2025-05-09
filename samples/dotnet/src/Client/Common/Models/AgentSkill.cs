using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Describes a skill of an agent.
/// </summary>
public class AgentSkill
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = null!;

    [JsonPropertyName("name")]
    public string Name { get; set; } = null!;

    [JsonPropertyName("description")]
    public string Description { get; set; } = null!;

    [JsonPropertyName("tags")]
    public List<string> Tags { get; set; } = null!;

    [JsonPropertyName("examples")]
    public List<string> Examples { get; set; } = null!;

    [JsonPropertyName("inputModes")]
    public List<string> InputModes { get; set; } = null!;

    [JsonPropertyName("outputModes")]
    public List<string> OutputModes { get; set; } = null!;
}