using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Client.Common.Exceptions;
using Client.Common.Models;

namespace Client;

/// <summary>
/// A client implementation for the A2A protocol that communicates with an A2A server over HTTP using JSON-RPC.
/// </summary>
public class A2AClient : IDisposable
{
    private readonly string _baseUrl;
    private readonly HttpClient _httpClient;
    private AgentCard _cachedAgentCard = null!;
    private bool _disposed;

    /// <summary>
    /// Creates a new instance of <see cref="A2AClient"/>.
    /// </summary>
    /// <param name="baseUrl">The base URL of the A2A server endpoint.</param>
    /// <param name="httpClient">Optional HTTP client to use for requests.</param>
    public A2AClient(string baseUrl, HttpClient? httpClient = null)
    {
        // Ensure baseUrl doesn't end with a slash for consistency
        _baseUrl = baseUrl.EndsWith("/") ? baseUrl.Substring(0, baseUrl.Length - 1) : baseUrl;
        _httpClient = httpClient ?? new HttpClient();
    }

    /// <summary>
    /// Generates a unique request ID.
    /// </summary>
    /// <returns>A unique ID string.</returns>
    private string GenerateRequestId()
    {
        return Guid.NewGuid().ToString();
    }

    /// <summary>
    /// Makes an HTTP request for a JSON-RPC call.
    /// </summary>
    /// <param name="method">The JSON-RPC method name.</param>
    /// <param name="parameters">The parameters for the method.</param>
    /// <param name="acceptHeader">The Accept header value.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The HTTP response message.</returns>
    private async Task<HttpResponseMessage> MakeHttpRequestAsync(
        string method,
        object parameters,
        string acceptHeader = "application/json",
        CancellationToken cancellationToken = default)
    {
        string requestId = GenerateRequestId();
        JsonRpcRequest request = new()
        {
            Id = requestId,
            Method = method,
            Params = parameters
        };

        try
        {
            StringContent content = new(
                JsonSerializer.Serialize(request),
                Encoding.UTF8,
                "application/json");

            HttpRequestMessage httpRequest = new(HttpMethod.Post, _baseUrl)
            {
                Content = content
            };
            httpRequest.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue(acceptHeader));

            HttpResponseMessage response = await _httpClient.SendAsync(
                httpRequest,
                HttpCompletionOption.ResponseHeadersRead,
                cancellationToken);

            return response;
        }
        catch (HttpRequestException networkError)
        {
            await Console.Error.WriteLineAsync($"Network error during RPC call: {networkError}");
            throw new RpcException(
                -32603, // Internal error
                $"Network error: {networkError.Message}",
                networkError);
        }
    }

    /// <summary>
    /// Handles a JSON-RPC response.
    /// </summary>
    /// <typeparam name="T">The type of the result.</typeparam>
    /// <param name="response">The HTTP response message.</param>
    /// <param name="expectedMethod">The expected method name (for debugging).</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The result of the JSON-RPC call.</returns>
    private async Task<T> HandleJsonResponseAsync<T>(
        HttpResponseMessage response,
        string? expectedMethod = null,
        CancellationToken cancellationToken = default)
    {
        string responseBody = null!;
        try
        {
            if (!response.IsSuccessStatusCode)
            {
                // Attempt to read body even for non-ok responses for potential JSON errors
                responseBody = await response.Content.ReadAsStringAsync(cancellationToken);

                try
                {
                    // Try parsing as JSON RPC Error response
                    JsonRpcResponse<T>? parsedError = JsonSerializer.Deserialize<JsonRpcResponse<T>>(responseBody);
                    if (parsedError?.Error != null)
                    {
                        JsonRpcError errorData = parsedError.Error;
                        throw new RpcException(
                            errorData.Code,
                            errorData.Message,
                            errorData.Data);
                    }
                }
                catch (JsonException)
                {
                    // Ignore parsing error, fall through to generic HTTP error
                }

                // If not a JSON RPC error, throw generic HTTP error
                throw new HttpRequestException(
                    $"HTTP error {(int)response.StatusCode}: {response.ReasonPhrase}" +
                    (string.IsNullOrEmpty(responseBody) ? "" : $" - {responseBody}"));
            }

            // Read and parse the successful JSON response
            responseBody = await response.Content.ReadAsStringAsync(cancellationToken);
            JsonRpcResponse<T>? jsonResponse = JsonSerializer.Deserialize<JsonRpcResponse<T>>(responseBody);

            // Basic validation of the JSON-RPC response structure
            if (jsonResponse is not { JsonRpc: "2.0" })
            {
                throw new RpcException(
                    -32603,
                    "Invalid JSON-RPC response structure received from server.");
            }

            // Check for application-level errors within the JSON-RPC response
            if (jsonResponse.Error != null)
            {
                throw new RpcException(
                    jsonResponse.Error.Code,
                    jsonResponse.Error.Message,
                    jsonResponse.Error.Data);
            }

            // Extract and return only the result payload
            return jsonResponse.Result;
        }
        catch (Exception error)
        {
            await Console.Error.WriteLineAsync(
                $"Error processing RPC response for method {expectedMethod ?? "unknown"}: {error}" +
                (string.IsNullOrEmpty(responseBody) ? "" : $"\nResponse Body: {responseBody}"));

            // Re-throw RpcException instances directly, wrap others
            if (error is RpcException)
            {
                throw;
            }
            else
            {
                throw new RpcException(
                    -32603, // Internal error
                    $"Failed to process response: {error.Message}",
                    error);
            }
        }
    }

    /// <summary>
    /// Handles a streaming Server-Sent Events (SSE) response.
    /// </summary>
    /// <typeparam name="T">The type of the events.</typeparam>
    /// <param name="response">The HTTP response message.</param>
    /// <param name="eventHandler">The handler for events.</param>
    /// <param name="expectedMethod">The expected method name (for debugging).</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>A task that completes when the stream ends.</returns>
    private async System.Threading.Tasks.Task HandleStreamingResponseAsync<T>(
        HttpResponseMessage response,
        Action<T> eventHandler,
        string? expectedMethod = null,
        CancellationToken cancellationToken = default)
    {
        if (!response.IsSuccessStatusCode)
        {
            string errorText = null!;
            try
            {
                errorText = await response.Content.ReadAsStringAsync(cancellationToken);
            }
            catch
            {
                // Ignore read error
            }

            await Console.Error.WriteLineAsync(
                $"HTTP error {(int)response.StatusCode} received for streaming method {expectedMethod ?? "unknown"}." +
                (string.IsNullOrEmpty(errorText) ? "" : $" Response: {errorText}"));

            throw new HttpRequestException(
                $"HTTP error {(int)response.StatusCode}: {response.ReasonPhrase} - Failed to establish stream.");
        }

        Stream stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        StreamReader reader = new(stream);
        StringBuilder buffer = new();

        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                string? line = await reader.ReadLineAsync(cancellationToken);
                if (line == null)
                {
                    // End of stream
                    if (buffer.Length > 0)
                    {
                        // Console.Warning($"SSE stream ended with partial data in buffer for method {expectedMethod}: {buffer}");
                    }
                    break;
                }

                // SSE messages are separated by blank lines
                if (string.IsNullOrEmpty(line))
                {
                    string message = buffer.ToString();
                    buffer.Clear();

                    if (message.StartsWith("data:"))
                    {
                        string dataLine = message.Substring("data:".Length).Trim();
                        if (!string.IsNullOrEmpty(dataLine))
                        {
                            try
                            {
                                JsonRpcResponse<T>? parsedData = JsonSerializer.Deserialize<JsonRpcResponse<T>>(dataLine);

                                // Basic validation of streamed data structure
                                if (parsedData is not { JsonRpc: "2.0" })
                                {
                                    await Console.Error.WriteLineAsync($"Invalid SSE data structure received for method {expectedMethod}: {dataLine}");
                                    continue; // Skip invalid data
                                }

                                // Check for errors within the streamed message
                                if (parsedData.Error != null)
                                {
                                    await Console.Error.WriteLineAsync($"Error received in SSE stream for method {expectedMethod}: {parsedData.Error}");
                                    // Throw an error to terminate the stream
                                    throw new RpcException(
                                        parsedData.Error.Code,
                                        parsedData.Error.Message,
                                        parsedData.Error.Data);
                                }
                                else if (parsedData.Result != null)
                                {
                                    // Invoke the event handler with the result
                                    eventHandler(parsedData.Result);
                                }
                                else
                                {
                                    // Should not happen if error and result are mutually exclusive per spec
                                    // Console.Warning($"SSE data for {expectedMethod} has neither result nor error: {parsedData}");
                                }
                            }
                            catch (JsonException e)
                            {
                                Console.Error.WriteLine($"Failed to parse SSE data line for method {expectedMethod}: {dataLine}", e);
                            }
                        }
                    }
                    else if (!string.IsNullOrWhiteSpace(message))
                    {
                        // Handle other SSE lines if necessary (e.g., 'event:', 'id:', 'retry:')
                        // Console.Debug($"Received non-data SSE line: {message}");
                    }
                }
                else
                {
                    buffer.AppendLine(line);
                }
            }
        }
        catch (Exception error)
        {
            await Console.Error.WriteLineAsync($"Error reading SSE stream for method {expectedMethod}: {error}");
            throw; // Re-throw the stream reading error
        }
        finally
        {
            reader.Dispose();
            Console.WriteLine($"SSE stream finished for method {expectedMethod}.");
        }
    }

    /// <summary>
    /// Retrieves the agent card.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The agent card.</returns>
    public async Task<AgentCard> GetAgentCardAsync(CancellationToken cancellationToken = default)
    {
        if (_cachedAgentCard != null)
        {
            return _cachedAgentCard;
        }

        // Assumption: Server exposes the card at a simple GET endpoint.
        string cardUrl = $"{_baseUrl}/agent-card";

        try
        {
            HttpRequestMessage request = new(HttpMethod.Get, cardUrl);
            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

            HttpResponseMessage response = await _httpClient.SendAsync(request, cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                throw new HttpRequestException(
                    $"HTTP error {(int)response.StatusCode} fetching agent card from {cardUrl}: {response.ReasonPhrase}");
            }

            string content = await response.Content.ReadAsStringAsync(cancellationToken);
            _cachedAgentCard = JsonSerializer.Deserialize<AgentCard>(content)!;
            return _cachedAgentCard;
        }
        catch (Exception error)
        {
            await Console.Error.WriteLineAsync($"Failed to fetch or parse agent card: {error}");
            throw new RpcException(
                -32603, // Internal error
                $"Could not retrieve agent card: {error.Message}",
                error);
        }
    }

    /// <summary>
    /// Sends a task request to the agent (non-streaming).
    /// </summary>
    /// <param name="parameters">The parameters for the tasks/send method.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The task object or null.</returns>
    public async Task<System.Threading.Tasks.Task> SendTaskAsync(
        TaskSendParams parameters,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await MakeHttpRequestAsync(
            "tasks/send",
            parameters,
            cancellationToken: cancellationToken);

        return await HandleJsonResponseAsync<System.Threading.Tasks.Task>(
            response,
            "tasks/send",
            cancellationToken);
    }

    /// <summary>
    /// Sends a task request and subscribes to streaming updates.
    /// </summary>
    /// <param name="parameters">The parameters for the tasks/sendSubscribe method.</param>
    /// <param name="statusUpdateHandler">Handler for task status updates.</param>
    /// <param name="artifactUpdateHandler">Handler for task artifact updates.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>A task that completes when the stream ends.</returns>
    public async System.Threading.Tasks.Task SendTaskSubscribeAsync(
        TaskSendParams parameters,
        Action<TaskStatusUpdateEvent> statusUpdateHandler,
        Action<TaskArtifactUpdateEvent> artifactUpdateHandler,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await MakeHttpRequestAsync(
            "tasks/sendSubscribe",
            parameters,
            "text/event-stream",
            cancellationToken);

        // Handle both types of events with a router function
        await HandleStreamingResponseAsync<object>(
            response,
            eventObj => {
                if (eventObj is JsonElement jsonElement)
                {
                    // Need to determine the type of the event
                    if (jsonElement.TryGetProperty("status", out _))
                    {
                        TaskStatusUpdateEvent? statusEvent = JsonSerializer.Deserialize<TaskStatusUpdateEvent>(jsonElement.GetRawText());
                        statusUpdateHandler?.Invoke(statusEvent!);
                    }
                    else if (jsonElement.TryGetProperty("artifact", out _))
                    {
                        TaskArtifactUpdateEvent? artifactEvent = JsonSerializer.Deserialize<TaskArtifactUpdateEvent>(jsonElement.GetRawText());
                        artifactUpdateHandler?.Invoke(artifactEvent!);
                    }
                }
            },
            "tasks/sendSubscribe",
            cancellationToken);
    }

    /// <summary>
    /// Retrieves the current state of a task.
    /// </summary>
    /// <param name="parameters">The parameters for the tasks/get method.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The task object or null.</returns>
    public async Task<System.Threading.Tasks.Task> GetTaskAsync(
        TaskQueryParams parameters,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await MakeHttpRequestAsync(
            "tasks/get",
            parameters,
            cancellationToken: cancellationToken);

        return await HandleJsonResponseAsync<System.Threading.Tasks.Task>(
            response,
            "tasks/get",
            cancellationToken);
    }

    /// <summary>
    /// Cancels a currently running task.
    /// </summary>
    /// <param name="parameters">The parameters for the tasks/cancel method.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The updated task object (usually canceled state) or null.</returns>
    public async Task<System.Threading.Tasks.Task> CancelTaskAsync(
        TaskIdParams parameters,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await MakeHttpRequestAsync(
            "tasks/cancel",
            parameters,
            cancellationToken: cancellationToken);

        return await HandleJsonResponseAsync<System.Threading.Tasks.Task>(
            response,
            "tasks/cancel",
            cancellationToken);
    }

    /// <summary>
    /// Sets or updates the push notification config for a task.
    /// </summary>
    /// <param name="parameters">The parameters for the tasks/pushNotification/set method.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The confirmed task push notification config or null.</returns>
    public async Task<TaskPushNotificationConfig> SetTaskPushNotificationAsync(
        TaskPushNotificationConfig parameters,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await MakeHttpRequestAsync(
            "tasks/pushNotification/set",
            parameters,
            cancellationToken: cancellationToken);

        return await HandleJsonResponseAsync<TaskPushNotificationConfig>(
            response,
            "tasks/pushNotification/set",
            cancellationToken);
    }

    /// <summary>
    /// Retrieves the currently configured push notification config for a task.
    /// </summary>
    /// <param name="parameters">The parameters for the tasks/pushNotification/get method.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The task push notification config or null.</returns>
    public async Task<TaskPushNotificationConfig> GetTaskPushNotificationAsync(
        TaskIdParams parameters,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await MakeHttpRequestAsync(
            "tasks/pushNotification/get",
            parameters,
            cancellationToken: cancellationToken);

        return await HandleJsonResponseAsync<TaskPushNotificationConfig>(
            response,
            "tasks/pushNotification/get",
            cancellationToken);
    }

    /// <summary>
    /// Resubscribes to updates for a task after a potential connection interruption.
    /// </summary>
    /// <param name="parameters">The parameters for the tasks/resubscribe method.</param>
    /// <param name="statusUpdateHandler">Handler for task status updates.</param>
    /// <param name="artifactUpdateHandler">Handler for task artifact updates.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>A task that completes when the stream ends.</returns>
    public async System.Threading.Tasks.Task ResubscribeTaskAsync(
        TaskQueryParams parameters,
        Action<TaskStatusUpdateEvent> statusUpdateHandler,
        Action<TaskArtifactUpdateEvent> artifactUpdateHandler,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await MakeHttpRequestAsync(
            "tasks/resubscribe",
            parameters,
            "text/event-stream",
            cancellationToken);

        // Handle both types of events with a router function
        await HandleStreamingResponseAsync<object>(
            response,
            eventObj => {
                if (eventObj is JsonElement jsonElement)
                {
                    // Need to determine the type of the event
                    if (jsonElement.TryGetProperty("status", out _))
                    {
                        TaskStatusUpdateEvent? statusEvent = JsonSerializer.Deserialize<TaskStatusUpdateEvent>(jsonElement.GetRawText());
                        statusUpdateHandler?.Invoke(statusEvent!);
                    }
                    else if (jsonElement.TryGetProperty("artifact", out _))
                    {
                        TaskArtifactUpdateEvent? artifactEvent = JsonSerializer.Deserialize<TaskArtifactUpdateEvent>(jsonElement.GetRawText());
                        artifactUpdateHandler?.Invoke(artifactEvent!);
                    }
                }
            },
            "tasks/resubscribe",
            cancellationToken);
    }

    /// <summary>
    /// Checks if the server likely supports optional methods based on agent card.
    /// </summary>
    /// <param name="capability">The capability to check.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>True if the capability is likely supported, false otherwise.</returns>
    public async Task<bool> SupportsAsync(
        string capability,
        CancellationToken cancellationToken = default)
    {
        try
        {
            AgentCard card = await GetAgentCardAsync(cancellationToken);
            return capability.ToLowerInvariant() switch
            {
                "streaming" => card.Capabilities?.Streaming ?? false,
                "pushnotifications" => card.Capabilities?.PushNotifications ?? false,
                _ => false
            };
        }
        catch (Exception error)
        {
            await Console.Error.WriteLineAsync($"Failed to determine support for capability '{capability}': {error}");
            return false; // Assume not supported if card fetch fails
        }
    }

    /// <summary>
    /// Disposes the client and releases resources.
    /// </summary>
    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the client and releases resources.
    /// </summary>
    /// <param name="disposing">True if disposing, false if finalizing.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (!_disposed)
        {
            if (disposing)
            {
                _httpClient?.Dispose();
            }

            _disposed = true;
        }
    }

    /// <summary>
    /// Finalizes an instance of the <see cref="A2AClient"/> class.
    /// </summary>
    ~A2AClient()
    {
        Dispose(false);
    }
}