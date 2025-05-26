using Client.Common.Models;
using Github;
using Microsoft.SemanticKernel;
using Server.Services.Interfaces;
using Task = Client.Common.Models.Task;

namespace Server.Services;

public class DefaultTaskProcessor(
    ILogger<DefaultTaskProcessor> logger,
    ITaskStore taskStore,
    AgentService agentService)
    : ITaskProcessor
{
    private readonly Dictionary<string, CancellationTokenSource> _taskCancellations = new();

    public async Task<Task> ProcessTaskAsync(TaskSendParams parameters, string content)
    {
        Task task = taskStore.CreateTask(parameters.Id, parameters.SessionId);

        taskStore.UpdateTaskStatus(parameters.Id, TaskState.WORKING);

        try
        {
            CancellationTokenSource? cts = new();

            lock (_taskCancellations)
            {
                if (_taskCancellations.TryGetValue(parameters.Id, out CancellationTokenSource? value))
                {
                    value.Dispose();
                }

                _taskCancellations[parameters.Id] = cts;
            }

            ChatMessageContent result = await agentService.ProcessQuery(content, cts.Token);

            Message? agentMessage = new()
            {
                Role = "agent",
                Parts = [new TextPart { Text = result.Content! }]
            };


            taskStore.UpdateTaskStatus(parameters.Id, TaskState.COMPLETED, agentMessage);
        }
        catch (OperationCanceledException)
        {
            Message? cancelMessage = new()
            {
                Role = "agent",
                Parts = [new TextPart { Text = "Task was canceled." }]
            };

            taskStore.UpdateTaskStatus(parameters.Id, TaskState.CANCELED, cancelMessage);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error processing task {TaskId}: {Message}", parameters.Id, ex.Message);

            Message? errorMessage = new()
            {
                Role = "agent",
                Parts = [new TextPart { Text = $"Error: {ex.Message}" }]
            };

            taskStore.UpdateTaskStatus(parameters.Id, TaskState.FAILED, errorMessage);
        }
        finally
        {
            lock (_taskCancellations)
            {
                if (_taskCancellations.Remove(parameters.Id, out CancellationTokenSource? cts))
                {
                    cts.Dispose();
                }
            }
        }

        return task;
    }
}