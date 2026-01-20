import { StateGraph, END, START } from "@langchain/langgraph";
import { HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import readline from 'readline';

// --- 1. STATE DEFINITION ---
const agentState = {
  messages: {
    value: (x, y) => x.concat(y),
    default: () => [],
  },
};

// --- 2. MOCK LLM (The "Brain") ---
async function mockLLMNode(state) {
  const messages = state.messages;
  const lastMessage = messages[messages.length - 1];
  const input = lastMessage.content.toLowerCase();

  console.log(`\x1b[36m[GRAPH:AGENT] Thinking about: "${input}"...\x1b[0m`);

  // COMMAND: List Files
  if (input.includes("list files") || input.includes("ls")) {
    return {
      messages: [
        new AIMessage({
          content: "",
          additional_kwargs: {
            function_call: {
              name: "execute_shell",
              arguments: JSON.stringify({ command: "ls -la" }),
            },
          },
        }),
      ],
    };
  }

  // COMMAND: Save File
  // Example: "save hello.txt with content world"
  if (input.includes("save")) {
    const parts = input.split(" ");
    const filename = parts[1] || "output.txt";
    const content = input.split("with content")[1] || "Hello World";
    
    return {
      messages: [
        new AIMessage({
          content: "",
          additional_kwargs: {
            function_call: {
              name: "save_file",
              arguments: JSON.stringify({ path: filename, content: content.trim() }),
            },
          },
        }),
      ],
    };
  }

  // COMMAND: Research
  if (input.includes("research")) {
    const topic = input.replace("research", "").trim() || "Artificial Intelligence";
    return {
      messages: [
        new AIMessage({
          content: "",
          additional_kwargs: {
            function_call: {
              name: "start_research",
              arguments: JSON.stringify({ topic }),
            },
          },
        }),
      ],
    };
  }

  return {
    messages: [new AIMessage({ content: `I processed: "${input}". Ready for next command.` })],
  };
}

// --- 3. TOOL NODE (The "Hands") ---
async function actionNode(state) {
  const messages = state.messages;
  const lastMessage = messages[messages.length - 1];
  const action = lastMessage.additional_kwargs.function_call;

  const args = JSON.parse(action.arguments);
  console.log(`\x1b[33m[GRAPH:TOOL] Tool Request: ${action.name}\x1b[0m`);

  if (action.name === "start_research") {
    console.log(`[FACTORY] Starting research on: ${args.topic}`);
    try {
      const res = await fetch(`http://localhost:8000/research/start?topic=${encodeURIComponent(args.topic)}`, {
        method: 'POST'
      });
      const data = await res.json();
      return { messages: [new SystemMessage({ content: `Research Job Started: ${data.job_id}`, name: action.name })] };
    } catch (e) {
      return { messages: [new SystemMessage({ content: `Factory Error: ${e.message}`, name: "error" })] };
    }
  }

  if (action.name === "execute_shell") {
    console.log(`[EXEC] ${args.command}`);
    // Simulated output
    const result = "total 4\n-rw-r--r-- 1 user user 123 Jan 15 10:00 agent.js";
    return { messages: [new SystemMessage({ content: result, name: action.name })] };
  }

  if (action.name === "save_file") {
    // We emit a special log tag that the UI intercepts
    console.log(`<<SYS_FILE_SYNC>>${JSON.stringify(args)}`);
    return { messages: [new SystemMessage({ content: "File sync requested.", name: action.name })] };
  }

  return { messages: [new SystemMessage({ content: "Unknown tool", name: "error" })] };
}

// --- 4. EDGES ---
function shouldContinue(state) {
  const messages = state.messages;
  const lastMessage = messages[messages.length - 1];

  if (lastMessage.additional_kwargs?.function_call) {
    return "action";
  }
  return "end";
}

// --- 5. GRAPH ---
const workflow = new StateGraph({ channels: agentState })
  .addNode("agent", mockLLMNode)
  .addNode("action", actionNode)
  .addEdge(START, "agent")
  .addConditionalEdges("agent", shouldContinue, {
    action: "action",
    end: END,
  })
  .addEdge("action", "agent");

const app = workflow.compile();

// --- 6. RUNTIME ---
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log("\x1b[32m[SYSTEM] LangGraph Agent v1.1 (Sync Enabled)\x1b[0m");
console.log("Waiting for input...");

rl.on('line', async (line) => {
  if (!line.trim()) return;
  const inputs = { messages: [new HumanMessage({ content: line })] };
  try {
    const config = { recursionLimit: 50 };
    const stream = await app.stream(inputs, config);
    for await (const output of stream) {}
    console.log("[SYSTEM] Turn Complete.");
  } catch (error) {
    console.error("\x1b[31m[ERROR]\x1b[0m", error);
  }
});
