using Client.Common.Models;
using Task = Client.Common.Models.Task;

namespace Server.Services.Interfaces;

public class TaskStore : ITaskStore
{
    public Task CreateTask(string taskId, string? sessionId = null)
    {
        throw new NotImplementedException();
    }

    public Task? UpdateTaskStatus(string taskId, TaskState state, Message? message = null)
    {
        throw new NotImplementedException();
    }
}