import readline from "node:readline";
import { colorize } from "./colors.js";

// Daytona functionality
export class DaytonaRunner {
  private daytona: any;
  public isWaitingForDaytonaResponse: boolean = false;
  
  constructor(private rl: readline.Interface) {
    // Will be initialized in init()
    this.daytona = null;
  }

  async init(): Promise<boolean> {
    try {
      // Dynamic import to avoid breaking when not using Daytona
      const daytonaModule = await import("@daytonaio/sdk");
      this.daytona = daytonaModule.Daytona;
      return true;
    } catch (error) {
      console.log(colorize("yellow", "⚠️ Daytona SDK not available. Code execution features disabled."));
      return false;
    }
  }

  offerToRunInDaytona(fileName: string, codeContent: string): void {
    if (!this.daytona) return;
    
    const fileExt = fileName.split('.').pop()?.toLowerCase() || '';
    // Only allow TypeScript and Python files
    const codeExtensions = ['ts', 'py'];
    
    if (!codeExtensions.includes(fileExt) || !codeContent) return;
    
    this.askToRun().then(shouldRun => {
      if (shouldRun) {
        this.runCodeInDaytona(fileName, codeContent);
      }
    });
  }

  private askToRun(): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      const originalPrompt = this.rl.getPrompt();
      this.rl.setPrompt(colorize("yellow", "Run the code in a Daytona Sandbox? (y/n): "));
      this.isWaitingForDaytonaResponse = true;
      this.rl.prompt();
      
      const oneLine = (line: string) => {
        this.isWaitingForDaytonaResponse = false;
        const response = line.trim().toLowerCase();
        if (response === 'y' || response === 'yes') {
          resolve(true);
        } else {
          resolve(false);
        }
        this.rl.removeListener('line', oneLine);
        this.rl.setPrompt(originalPrompt);
      };
      
      this.rl.once('line', oneLine);
    });
  }

  async runCodeInDaytona(fileName: string, codeContent: string): Promise<void> {
    if (!this.daytona) return;

    let daytonaSandbox: any = null;
    const daytona = new this.daytona();

    try {
      console.log(colorize("blue", `\n🚀 Running the code in a Daytona Sandbox: ${fileName}`));
      
      // Determine language from file extension
      const fileExt = fileName.split('.').pop()?.toLowerCase() || 'py';
      
      // Map common extensions to languages
      const extMap: Record<string, string> = {
        'ts': 'typescript',
        'py': 'python'
      };
      
      let language = extMap[fileExt] || 'python';    

      // Create the Sandbox instance
      daytonaSandbox = await daytona.create({
        language: language
      });
      
      // Run the code
      const response = await daytonaSandbox.process.codeRun(codeContent);

      console.log("Daytona's response:", response.result);
    } catch (error: any) {
      console.error(colorize("red", `\n❌ Error running code in Daytona: ${error.message || error}`));
    } finally {
      try {
        if (daytonaSandbox) {
          await daytona.remove(daytonaSandbox);
        }
      } catch (error: any) {
        console.error(colorize("red", `❌ Error removing sandbox: ${error.message || error}`));
      }
      
      this.rl.prompt();
    }
  }
}
