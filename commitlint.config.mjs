export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "feat",     // New feature
        "fix",      // Bug fix
        "docs",     // Documentation
        "style",    // Formatting (no code change)
        "refactor", // Code restructuring
        "perf",     // Performance improvement
        "test",     // Adding tests
        "chore",    // Maintenance tasks
        "ci",       // CI/CD changes
        "build",    // Build system changes
        "revert",   // Revert previous commit
      ],
    ],
    "subject-case": [2, "always", "lower-case"],
    "subject-empty": [2, "never"],
    "type-empty": [2, "never"],
  },
};