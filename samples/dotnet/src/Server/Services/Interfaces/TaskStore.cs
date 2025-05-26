using Client.Common.Models;
using Task = Client.Common.Models.Task;
using TaskStatus = Client.Common.Models.TaskStatus;

namespace Server.Services.Interfaces;

public class TaskStore : ITaskStore
{
    private static IList<Task> Tasks = new List<Task>();
    public Task CreateTask(string taskId, string? sessionId = null)
    {
        Task task = new Task
        {
            Id = taskId,
            SessionId = sessionId!,
            Status = new TaskStatus
            {
                State = TaskState.SUBMITTED,
                Timestamp = DateTime.UtcNow,
                Message = null!
            },
            History = []
        };

        Tasks.Add(task);

        return task;
    }

    public Task? UpdateTaskStatus(string taskId, TaskState state, Message message)
    {
        Task task = Tasks.Single(t => t.Id.Equals(taskId));
        task.Status = new TaskStatus()
        {
            Message = message,
            State = state,
            Timestamp = DateTime.Now
        };
        task.History.Add(message);

        return task;
    }
}