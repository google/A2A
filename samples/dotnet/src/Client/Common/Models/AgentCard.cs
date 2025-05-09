using System.Text.Json.Serialization;

namespace Client.Common.Models;

/// <summary>
/// Metadata and capabilities of an agent.
/// </summary>
public class AgentCard
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = null!;

    [JsonPropertyName("description")]
    public string Description { get; set; } = null!;

    [JsonPropertyName("url")]
    public string Url { get; set; } = null!;

    [JsonPropertyName("provider")]
    public AgentProvider Provider { get; set; } = null!;

    [JsonPropertyName("version")]
    public string Version { get; set; } = null!;

    [JsonPropertyName("documentationUrl")]
    public string DocumentationUrl { get; set; } = null!;

    [JsonPropertyName("capabilities")]
    public AgentCapabilities Capabilities { get; set; } = null!;

    [JsonPropertyName("authentication")]
    public AgentAuthentication Authentication { get; set; } = null!;

    [JsonPropertyName("defaultInputModes")]
    public List<string> DefaultInputModes { get; set; } = ["text"];

    [JsonPropertyName("defaultOutputModes")]
    public List<string> DefaultOutputModes { get; set; } = ["text"];

    [JsonPropertyName("skills")]
    public List<AgentSkill> Skills { get; set; } = null!;
}