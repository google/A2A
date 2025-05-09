using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Client;

namespace Github;

public class KernelBuilder(IConfiguration config)
{
    private readonly IConfiguration _config = config;

    public Kernel BuildKernel(IList<McpClientTool> tools)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services
            .AddLogging(c => c.AddDebug().SetMinimumLevel(LogLevel.Trace))
            .AddOpenAIChatCompletion(
                modelId: Environment.GetEnvironmentVariable("OPENAI_MODEL_NAME") ?? "gpt-4o-mini",
                apiKey: Environment.GetEnvironmentVariable("OPENAI_API_KEY")!);

        Kernel kernel = builder.Build();

#pragma warning disable SKEXP0001
        kernel.Plugins.AddFromFunctions("GitHub", tools.Select(aiFunction => aiFunction.AsKernelFunction()));
#pragma warning restore SKEXP0001

        return kernel;
    }
}