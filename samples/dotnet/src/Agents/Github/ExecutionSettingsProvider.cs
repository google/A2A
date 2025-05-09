using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Github;

public class ExecutionSettingsProvider
{
    public static OpenAIPromptExecutionSettings GetOpenAiSettings()
    {
        return new OpenAIPromptExecutionSettings
        {
            Temperature = 0,
#pragma warning disable SKEXP0001
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new FunctionChoiceBehaviorOptions { RetainArgumentTypes = true })
#pragma warning restore SKEXP0001
        };
    }
}