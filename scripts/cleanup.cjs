const fs = require("fs");
const path = require("path");

function remove(targetPath) {
  const fullPath = path.join(process.cwd(), targetPath);
  if (fs.existsSync(fullPath)) {
    fs.rmSync(fullPath, { recursive: true, force: true });
    console.log(`[clean] Removed ${targetPath}`);
  }
}

const mode = process.argv[2];

if (mode === "preinstall") {
  // Before each `npm install`, ensure old modules and caches are removed
  remove("node_modules");
  remove(".next");
  remove(".turbo");
  remove("node_modules/.cache");
} else if (mode === "predev") {
  // Before each `npm run dev`, clear build caches (but keep node_modules)
  remove(".next");
  remove(".turbo");
  remove("node_modules/.cache");
} else {
  console.log('[clean] No mode specified (expected "preinstall" or "predev").');
}