/**
 * useWebContainer Hook
 * ====================
 * Manages WebContainer lifecycle, including boot, file system mounting,
 * npm install, and process management.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { WebContainer } from "@webcontainer/api";
import { Terminal } from "xterm";
import { CommandQueue } from "./Throttler";

// @ts-ignore
import agentSource from "../files/agent.js?raw";
// @ts-ignore
import packageJsonSource from "../files/package.json?raw";

export type ContainerStatus = "booting" | "installing" | "ready" | "error";

interface UseWebContainerOptions {
  onFileSync?: (path: string, success: boolean) => void;
  onRefresh?: () => void;
}

interface UseWebContainerResult {
  status: ContainerStatus;
  queueSize: number;
  handleInput: (data: string) => void;
  terminalRef: React.MutableRefObject<Terminal | null>;
}

export function useWebContainer(
  options: UseWebContainerOptions = {}
): UseWebContainerResult {
  const [status, setStatus] = useState<ContainerStatus>("booting");
  const [queueSize, setQueueSize] = useState(0);

  const terminalRef = useRef<Terminal | null>(null);
  const containerRef = useRef<WebContainer | null>(null);
  const processRef = useRef<any>(null);
  const queueRef = useRef<CommandQueue | null>(null);

  const addLog = useCallback(
    (msg: string, type: "info" | "warn" | "success" = "info") => {
      console.log(`[${type}] ${msg}`);
      if (terminalRef.current) {
        const color =
          type === "warn"
            ? "\x1b[31m"
            : type === "success"
            ? "\x1b[32m"
            : "\x1b[90m";
        if (
          type !== "info" ||
          msg.includes("Booting") ||
          msg.includes("Ready")
        ) {
          terminalRef.current.write(`\r\n${color}[SYS] ${msg}\x1b[0m\r\n`);
        }
      }
    },
    []
  );

  const handleInput = useCallback((data: string) => {
    queueRef.current?.enqueue(data);
  }, []);

  useEffect(() => {
    queueRef.current = new CommandQueue(
      async (command: string) => {
        const process = processRef.current;
        if (!process) return;
        const writer = process.input.getWriter();
        await writer.write(command);
        writer.releaseLock();
      },
      (size) => setQueueSize(size),
      50
    );

    let isMounted = true;

    async function boot() {
      if (containerRef.current) return;

      // Allow terminal to mount
      await new Promise((r) => setTimeout(r, 100));

      try {
        const term = terminalRef.current;
        if (!term || !isMounted) return;

        // --- PRE-FLIGHT CHECKS ---
        addLog("Starting Pre-flight Diagnostics...", "info");
        const isIsolated = window.crossOriginIsolated;

        if (!isIsolated) {
          throw new Error(
            "Security Headers Missing. Site must be Cross-Origin Isolated."
          );
        }

        addLog("Booting WebContainer...", "info");
        const webcontainer = await WebContainer.boot();
        containerRef.current = webcontainer;

        addLog("Mounting file system...", "info");
        await webcontainer.mount({
          "agent.js": { file: { contents: agentSource } },
          "package.json": { file: { contents: packageJsonSource } },
        });

        setStatus("installing");
        addLog("Running npm install...", "info");

        const installProcess = await webcontainer.spawn("npm", ["install"]);
        installProcess.output.pipeTo(
          new WritableStream({
            write(data) {
              term.write(`\x1b[2m${data}\x1b[0m`);
            },
          })
        );

        const exitCode = await installProcess.exit;
        if (exitCode !== 0)
          throw new Error(`npm install failed with code ${exitCode}`);

        addLog("Agent Environment Ready.", "success");
        const process = await webcontainer.spawn("node", ["agent.js"]);
        processRef.current = process;

        process.output.pipeTo(
          new WritableStream({
            write(data) {
              term.write(data);

              // --- SYNC INTERCEPTOR ---
              if (data.includes("<<SYS_FILE_SYNC>>")) {
                const payload = data.split("<<SYS_FILE_SYNC>>")[1].trim();
                try {
                  const fileData = JSON.parse(payload);
                  addLog(`Syncing ${fileData.path} to host...`, "info");

                  fetch("http://localhost:8000/fs/write", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(fileData),
                  })
                    .then((res) => {
                      if (res.ok) {
                        addLog(`Saved: ${fileData.path}`, "success");
                        options.onFileSync?.(fileData.path, true);
                        options.onRefresh?.();
                      } else {
                        addLog(`Save Failed: ${res.statusText}`, "warn");
                        options.onFileSync?.(fileData.path, false);
                      }
                    })
                    .catch((err) => {
                      addLog(`Network Error: ${err}`, "warn");
                      options.onFileSync?.("", false);
                    });
                } catch (e) {
                  addLog("Sync Protocol Error", "warn");
                }
              }

              if (data.includes("[AGENT]"))
                addLog(data.replace(/\x1b\[[0-9;]*m/g, ""), "info");
            },
          })
        );

        setStatus("ready");
      } catch (err) {
        if (!isMounted) return;
        addLog(`FATAL: ${err}`, "warn");
        setStatus("error");
        terminalRef.current?.write(
          `\r\n\x1b[31mFATAL ERROR:\r\n${err}\x1b[0m\r\n`
        );
      }
    }

    boot();

    return () => {
      isMounted = false;
    };
  }, [addLog, options]);

  return {
    status,
    queueSize,
    handleInput,
    terminalRef,
  };
}
