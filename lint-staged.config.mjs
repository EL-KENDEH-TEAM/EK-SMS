export default {
  // Frontend files
  "apps/web/**/*.{js,jsx,ts,tsx}": ["eslint --fix"],
  
  // Backend files
  "apps/api/**/*.py": ["ruff check --fix", "ruff format"],
  
  // JSON, YAML, Markdown
  "*.{json,yaml,yml,md}": ["prettier --write"],
};