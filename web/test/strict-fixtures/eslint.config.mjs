import actual from '../../eslint.config.js';
export default [...actual, {
  files: ['**/*.ts'],
  languageOptions: { parserOptions: { projectService: false, project: './test/strict-fixtures/tsconfig.json', tsconfigRootDir: import.meta.dirname + '/../..' } },
}];
