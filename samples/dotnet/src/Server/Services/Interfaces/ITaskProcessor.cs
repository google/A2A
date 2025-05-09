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
    /// <param name="parameters">The task parameters.</param>
    /// <returns>The processed task.</returns>
    Task<Client.Common.Models.Task> ProcessTaskAsync(TaskSendParams parameters);
}