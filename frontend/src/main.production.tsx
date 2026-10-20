import React from "react";
import { createRoot } from "react-dom/client";
import Workspace from "./Workspace";
import { isCrmRoute } from "./lib/routes";
import "./styles.css";
import "./depth.css";

// The hosting build has no demo entry point or public access to sample clients.
function ensureCrmRoute() {
  if (!isCrmRoute()) window.history.replaceState(null, "", "#crm");
}
ensureCrmRoute();
window.addEventListener("hashchange", ensureCrmRoute);
createRoot(document.getElementById("root")!).render(
  <React.StrictMode><Workspace /></React.StrictMode>,
);
