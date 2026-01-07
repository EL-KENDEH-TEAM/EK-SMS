"use client";

import { useState, useEffect, useCallback } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

// Helper to check iOS - runs only on client
function getIsIOS(): boolean {
  if (typeof window === "undefined") return false;
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as unknown as { MSStream?: unknown }).MSStream;
}

// Helper to check if already installed
function getIsStandalone(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(display-mode: standalone)").matches;
}

// Helper to check if dismissed
function getIsDismissed(): boolean {
  if (typeof window === "undefined") return false;
  return sessionStorage.getItem("pwa-prompt-dismissed") === "true";
}

export function PWAInstallPrompt() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isIOS] = useState(getIsIOS);

  const showPrompt = useCallback(() => {
    if (!getIsStandalone() && !getIsDismissed()) {
      setIsVisible(true);
    }
  }, []);

  useEffect(() => {
    // Don't show if already installed or dismissed
    if (getIsStandalone() || getIsDismissed()) {
      return;
    }

    // Show iOS instructions after a delay
    if (getIsIOS()) {
      const timer = setTimeout(showPrompt, 3000);
      return () => clearTimeout(timer);
    }

    // Listen for the beforeinstallprompt event (Android/Desktop)
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
      showPrompt();
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    };
  }, [showPrompt]);

  const handleInstallClick = async () => {
    if (!installPrompt) return;

    await installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice;

    if (outcome === "accepted") {
      setIsVisible(false);
    }
    setInstallPrompt(null);
  };

  const handleDismiss = () => {
    setIsVisible(false);
    // Remember dismissal for this session
    sessionStorage.setItem("pwa-prompt-dismissed", "true");
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white border-t border-gray-200 shadow-lg animate-slide-up">
      <div className="max-w-md mx-auto flex items-center gap-4">
        <div className="shrink-0 w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
          <span className="text-white font-bold text-lg">EK</span>
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-sm">Install EK-SMS</h3>
          {isIOS ? (
            <p className="text-xs text-gray-600 mt-0.5">
              Tap <span className="inline-flex items-center"><ShareIcon /></span> then &quot;Add to Home Screen&quot;
            </p>
          ) : (
            <p className="text-xs text-gray-600 mt-0.5">
              Install for quick access anytime
            </p>
          )}
        </div>

        <div className="shrink-0 flex gap-2">
          {!isIOS && (
            <button
              onClick={handleInstallClick}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Install
            </button>
          )}
          <button
            onClick={handleDismiss}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Dismiss"
          >
            <CloseIcon />
          </button>
        </div>
      </div>
    </div>
  );
}

function ShareIcon() {
  return (
    <svg className="w-4 h-4 mx-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}
