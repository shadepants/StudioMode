import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import MissionControl from "./MissionControl.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MissionControl />
  </StrictMode>
);
