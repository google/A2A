/** @type {import('eslint').Linter.Config} */
module.exports = {
    root: true,
    parser: '@typescript-eslint/parser',
    plugins: ['@typescript-eslint', 'n'],
    extends: [
      'eslint:recommended',
      'plugin:@typescript-eslint/recommended',
      'plugin:n/recommended',
    ],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'n/no-unsupported-features/es-syntax': 'off',
    },
    overrides: [
      {
        files: ['*.ts', '*.tsx'],
        parserOptions: {
          ecmaVersion: 'latest',
          sourceType: 'module',
        },
      },
    ],
  };
