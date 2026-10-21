import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const envPath = resolve(root, ".env");
const outputPath = resolve(root, "env.local.js");

const values = {
  BLAGUES_API_TOKEN: ""
};

if (existsSync(envPath)) {
  const content = readFileSync(envPath, "utf8");

  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separatorIndex = trimmed.indexOf("=");

    if (separatorIndex === -1) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    let value = trimmed.slice(separatorIndex + 1).trim();

    if (
      (value.startsWith("\"") && value.endsWith("\""))
      || (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    if (Object.hasOwn(values, key)) {
      values[key] = value;
    }
  }
}

const fileContent = [
  "// Fichier généré automatiquement depuis .env — ne pas committer.",
  `window.BLAGUES_API_TOKEN = ${JSON.stringify(values.BLAGUES_API_TOKEN)};`,
  ""
].join("\n");

writeFileSync(outputPath, fileContent, "utf8");
console.log(`env.local.js généré depuis ${existsSync(envPath) ? ".env" : ".env (absent, valeurs vides)"}.`);
