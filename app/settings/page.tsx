import { SettingsPanel } from "@/components/settings/settings-panel";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-xl font-semibold tracking-tight">Engine settings</h1>
        <p className="text-xs text-muted-foreground">
          Tune similarity thresholds, analysis options, and the professor template used
          for boilerplate detection.
        </p>
      </header>
      <SettingsPanel />
    </div>
  );
}