using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Github;

public class PromptExecutor(Kernel kernel)
{
    public async Task ExecutePrompt(string prompt)
    {
        OpenAIPromptExecutionSettings executionSettings = ExecutionSettingsProvider.GetOpenAiSettings();
        FunctionResult result = await kernel.InvokePromptAsync(prompt, new KernelArguments(executionSettings)).ConfigureAwait(false);
        Console.WriteLine($"\n\n{prompt}\n{result}");
    }
}