export default {
  // Frontend files: run eslint inside the 'web' workspace
  "apps/web/**/*.{js,jsx,ts,tsx}": [
    "pnpm --filter web exec eslint --fix"
  ],

  // Backend files: pointed to the local venv
  "apps/api/**/*.py": [
    "apps/api/.venv/Scripts/ruff check --fix", 
    "apps/api/.venv/Scripts/ruff format"
  ],

  // JSON, YAML, Markdown: run prettier from the root
  "*.{json,yaml,yml,md}": [
    "pnpm exec prettier --write"
  ],
};