export const AGENT_SOURCE = `
console.log("BOOT: Internal Agent Starting...");
console.log("ENV: Node " + process.version);
console.log("cwd: " + process.cwd());

const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.on('line', (line) => {
  console.log("[AGENT] Received: " + line);
  if (line.trim() === 'ping') {
    console.log('[AGENT] Pong!');
  }
});

console.log("READY: Waiting for commands...");
`;
