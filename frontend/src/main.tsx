import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { QueryClientProvider } from "@tanstack/react-query";
import { crmQueryClient } from "./lib/crmQuery";
import "./styles.css";
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={crmQueryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
