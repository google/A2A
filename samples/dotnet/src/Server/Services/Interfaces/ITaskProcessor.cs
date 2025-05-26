using Client.Common.Models;

namespace Server.Services.Interfaces;

/// <summary>
/// Interface for processing tasks with the agent.
/// </summary>
public interface ITaskProcessor
{
    /// <summary>
    /// Processes a task synchronously.
    /// </summary>
    Task<Client.Common.Models.Task> ProcessTaskAsync(TaskSendParams parameters, string content);
}