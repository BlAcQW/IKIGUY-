import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { registerServiceWorker, setupInstallPrompt } from "./utils/pwa";

// Initialize PWA features
const initializePWA = async () => {
  try {
    await registerServiceWorker();
    setupInstallPrompt();
    console.log('PWA features initialized successfully');
  } catch (error) {
    console.error('Failed to initialize PWA features:', error);
  }
};

// Initialize PWA on app load
if (import.meta.env.PROD) {
  initializePWA();
}

createRoot(document.getElementById("root")!).render(<App />);
