using System.Text.Json;
using System.Text.Json.Serialization;
using Client.Common.Models;
using Microsoft.AspNetCore.Mvc;
using Server.Services.Interfaces;

namespace Server.Controllers;

/// <summary>
/// Controller for handling A2A JSON-RPC requests.
/// </summary>
[ApiController]
[Route("/")]
public class JsonRpcController : ControllerBase
{
    private readonly ILogger<JsonRpcController> _logger;
    private readonly ITaskStore _taskStore;
    private readonly ITaskProcessor _taskProcessor;

    private static readonly JsonSerializerOptions _jsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters = { new JsonStringEnumConverter() }
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="JsonRpcController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="taskStore">The task store.</param>
    /// <param name="taskProcessor">The task processor.</param>
    public JsonRpcController(
        ILogger<JsonRpcController> logger,
        ITaskStore taskStore,
        ITaskProcessor taskProcessor)
    {
        _logger = logger;
        _taskStore = taskStore;
        _taskProcessor = taskProcessor;
    }

    /// <summary>
    /// Processes an A2A JSON-RPC request.
    /// </summary>
    /// <param name="request">The JSON-RPC request.</param>
    /// <returns>A JSON-RPC response.</returns>
    [HttpPost]
    public async Task<IActionResult> ProcessRequest([FromBody] JsonRpcRequest request)
    {
        if (request == null || string.IsNullOrEmpty(request.Method))
        {
            return new ObjectResult(new JsonRpcError(-32600, "Invalid request: missing method"));
        }

        try
        {
            _logger.LogInformation("Processing request for method: {Method}", request.Method);

            IActionResult response = request.Method switch
            {
                "tasks/send" => await ProcessTaskSend(request),
                _ => new ObjectResult(new JsonRpcError(-32601, $"Method '{request.Method}' not found"))
            };

            return response;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing request: {Message}", ex.Message);
            return new ObjectResult(new JsonRpcError(-32603, $"Internal error: {ex.Message}"));
        }
    }

    private async Task<IActionResult> ProcessTaskSend(JsonRpcRequest request)
    {
        try
        {
            TaskSendParams? parameters = JsonSerializer.Deserialize<TaskSendParams>(
                JsonSerializer.Serialize(request.Params),
                _jsonOptions
            );

            if (parameters == null || string.IsNullOrEmpty(parameters.Id))
            {
                return new ObjectResult(new JsonRpcError(-32602, "Invalid parameters: 'id' is required"));
            }

            if (parameters.Message?.Parts == null || parameters.Message.Parts.Count == 0)
            {
                return new ObjectResult(new JsonRpcError(-32602, "Invalid parameters: 'message.parts' is required"));
            }

            Client.Common.Models.Task task = await _taskProcessor.ProcessTaskAsync(parameters);

            return Ok((request.Id, task));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing tasks/send: {Message}", ex.Message);
            return new ObjectResult(new JsonRpcError(-32603, $"Error processing tasks/send: {ex.Message}"));
        }
    }
}