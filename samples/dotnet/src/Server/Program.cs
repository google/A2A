using Github;
using Microsoft.SemanticKernel;
using Server.Services;
using System.Text.Json.Serialization;
using ModelContextProtocol.Client;
using Server.Services.Interfaces;
using McpClientFactory = Github.McpClientFactory;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
    });

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

ConfigurationService configurationService = new();
IConfiguration config = configurationService.BuildConfiguration();

builder.Services.AddSingleton(config);
builder.Services.AddSingleton<A2ACardService>();
builder.Services.AddSingleton<ITaskStore, TaskStore>();

builder.Services.AddSingleton<IMcpClientFactory, McpClientFactory>();
builder.Services.AddSingleton<McpClientService>();
builder.Services.AddSingleton<IMcpClient>(_ => builder.Services.BuildServiceProvider().GetRequiredService<McpClientService>().CreateClient().Result!);
builder.Services.AddSingleton<ToolService>();

builder.Services.AddSingleton(sp =>
{
    KernelBuilder kernelBuilder = new(config);
    ToolService toolService = sp.GetRequiredService<ToolService>();
    IList<McpClientTool> tools = toolService.GetGithubTools().GetAwaiter().GetResult();
    return kernelBuilder.BuildKernel(tools);
});

builder.Services.AddSingleton(sp =>
{
    Kernel kernel = sp.GetRequiredService<Kernel>();
    AgentFactory agentFactory = new(kernel);
    return agentFactory.CreateGithubAgent();
});

builder.Services.AddSingleton<AgentService>();
builder.Services.AddSingleton<ITaskProcessor, DefaultTaskProcessor>();

WebApplication app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();

app.UseHttpsRedirection();
app.UseRouting();

app.MapControllers();

app.Run();

public class ConfigurationService
{
    public IConfiguration BuildConfiguration()
    {
        return new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();
    }
}

