export class CommandQueue {
  private queue: string[] = [];
  private isProcessing: boolean = false;
  private processor: (command: string) => Promise<void>;
  private onQueueChange: (size: number) => void;
  private delay: number;

  constructor(
    processor: (command: string) => Promise<void>,
    onQueueChange: (size: number) => void,
    delayMs: number = 200
  ) {
    this.processor = processor;
    this.onQueueChange = onQueueChange;
    this.delay = delayMs;
  }

  public enqueue(command: string) {
    this.queue.push(command);
    this.onQueueChange(this.queue.length);
    this.process();
  }

  private async process() {
    if (this.isProcessing) return;
    this.isProcessing = true;

    while (this.queue.length > 0) {
      const command = this.queue.shift();
      if (command) {
        this.onQueueChange(this.queue.length); // Update UI: Queue reduced
        
        try {
          await this.processor(command);
        } catch (error) {
          console.error("Throttler Error:", error);
        }
        
        // Artificial cool-down to prevent flooding
        await new Promise(resolve => setTimeout(resolve, this.delay));
      }
    }

    this.isProcessing = false;
  }
}
