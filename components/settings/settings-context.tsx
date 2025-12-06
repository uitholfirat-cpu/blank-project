"use client";

import * as React from "react";

export type EngineSettings = {
  threshold: number;
  sensitivityMode: "smart" | "balanced" | "strict" | "custom";
  ignoreComments: boolean;
  ignoreVariableNames: boolean;
  ignoreFunctionNames: boolean;
  ignoreTypeNames: boolean;
  ignoreStringLiterals: boolean;
  ignoreNumericLiterals: boolean;
  functionSorting: boolean;
};

type SettingsContextValue = {
  settings: EngineSettings;
  setSettings: React.Dispatch<React.SetStateAction<EngineSettings>>;
};

const defaultSettings: EngineSettings = {
  threshold: 95,
  sensitivityMode: "balanced",
  ignoreComments: true,
  ignoreVariableNames: true,
  ignoreFunctionNames: false,
  ignoreTypeNames: false,
  ignoreStringLiterals: true,
  ignoreNumericLiterals: true,
  functionSorting: false
};

const STORAGE_KEY = "mastergrader-engine-settings";

const SettingsContext = React.createContext<SettingsContextValue | undefined>(
  undefined
);

export function SettingsProvider({
  children
}: {
  children: React.ReactNode;
}) {
  const [settings, setSettings] =
    React.useState<EngineSettings>(defaultSettings);

  // Hydrate settings from localStorage on mount
  React.useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (!stored) return;

      const parsed = JSON.parse(stored) as Partial<EngineSettings>;
      if (!parsed || typeof parsed !== "object") return;

      setSettings((prev) => ({
        ...prev,
        ...parsed
      }));
    } catch {
      // Ignore malformed or unavailable localStorage
    }
  }, []);

  // Persist settings whenever they change
  React.useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
      // Ignore write errors (e.g. private mode)
    }
  }, [settings]);

  return (
    <SettingsContext.Provider value={{ settings, setSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const ctx = React.useContext(SettingsContext);
  if (!ctx) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return ctx;
}