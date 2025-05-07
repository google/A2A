using Client.Common.Models;
using Task = Client.Common.Models.Task;  // Explicitly indicate we're using Client.Common.Models.Task

namespace Server.Services.Interfaces;

/// <summary>
/// Interface for storing and retrieving A2A tasks.
/// </summary>
public interface ITaskStore
{
    /// <summary>
    /// Creates a new task.
    /// </summary>
    /// <param name="taskId">The task ID.</param>
    /// <param name="sessionId">Optional session ID.</param>
    /// <returns>The newly created task.</returns>
    Task CreateTask(string taskId, string? sessionId = null);

    /// <summary>
    /// Updates a task's status.
    /// </summary>
    /// <param name="taskId">The task ID.</param>
    /// <param name="state">The new task state.</param>
    /// <param name="message">Optional message to associate with the status.</param>
    /// <returns>The updated task, or null if the task was not found.</returns>
    Task? UpdateTaskStatus(string taskId, TaskState state, Message? message = null);
}