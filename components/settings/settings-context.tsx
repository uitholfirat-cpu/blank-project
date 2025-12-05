"use client";

import * as React from "react";

export type EngineSettings = {
  threshold: number;
  ignoreComments: boolean;
  ignoreVariableNames: boolean;
  functionSorting: boolean;
};

type SettingsContextValue = {
  settings: EngineSettings;
  setSettings: React.Dispatch<React.SetStateAction<EngineSettings>>;
};

const defaultSettings: EngineSettings = {
  threshold: 95,
  ignoreComments: true,
  ignoreVariableNames: false,
  functionSorting: false
};

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