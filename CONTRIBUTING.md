# How to contribute

We'd love to accept your patches and contributions to this project.

## Before you begin

### Sign our Contributor License Agreement (CLA)

Contributions to this project must be accompanied by a Contributor License Agreement (CLA).
You (or your employer) retain the copyright to your contribution; this simply
gives us permission to use and redistribute your contributions as part of the
project.

If you or your current employer have already signed the Google CLA (even if it
was for a different project), you probably don't need to do it again.

Visit https://cla.developers.google.com/ to see your current agreements or to
sign a new one.

### Review our community guidelines

This project follows
Google's Open Source Community Guidelines (https://opensource.google/conduct/).

## Contribution process

### Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
GitHub Help (https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.

### Contributor Guide

You may follow these steps to contribute:

1. **Fork the official repository.** This will create a copy of the official repository in your own account.
2. **Sync the branches.** This will ensure that your copy of the repository is up-to-date with the latest changes from the official repository.
3. **Work on your forked repository's feature branch.** This is where you will make your changes to the code.
4. **Commit your updates on your forked repository's feature branch.** This will save your changes to your copy of the repository.
5. **Submit a pull request to the official repository's main branch.** This will request that your changes be merged into the official repository.
6. **Resolve any lint errors.** This will ensure that your changes are formatted correctly.
7. **If your PR changes `types/src/types.ts`, you must also update the generated JSON schema:**
   - Run:
     ```sh
     npx typescript-json-schema ./types/src/types.ts '*' --required --noExtraProps --out specification/json/a2a.json
     npx prettier --write specification/json/a2a.json
     ```
   - Commit the updated `specification/json/a2a.json` file with your PR.
   - If you forget, CI will fail and you will need to update and re-push.

Here are some additional things to keep in mind during the process:

- **Test your changes.** Before you submit a pull request, make sure that your changes work as expected.
- **Be patient.** It may take some time for your pull request to be reviewed and merged.

---

## Keeping the JSON Schema in Sync

If you make any changes to `types/src/types.ts`, you must also update the generated JSON schema (`specification/json/a2a.json`).

### Step-by-step guide

1. **Regenerate the schema:**
   In the project root, run:
   ```sh
   cd types
   npm install # if you haven't already
   npm run generate
   cd ..
   ```
   This will update `specification/json/a2a.json` based on the latest TypeScript types.

2. **Format the schema:**
   Run:
   ```sh
   npx prettier --write specification/json/a2a.json
   ```

3. **Check for uncommitted changes:**
   Run:
   ```sh
   git diff specification/json/a2a.json
   ```
   If there is no output, your schema is in sync. If there is output, commit the changes:
   ```sh
   git add specification/json/a2a.json
   git commit -m "Update a2a.json schema after types change"
   ```

4. **Push your changes and update your PR.**

### Troubleshooting persistent CI failures

- If CI fails with a schema sync error, repeat the steps above to ensure `a2a.json` is up-to-date and formatted.
- If you see a diff in CI but not locally, ensure you are using the correct Node.js and npm versions (see `.nvmrc` or `engines` in `package.json`).
- If the error persists, try deleting `node_modules` and reinstalling dependencies:
  ```sh
  rm -rf node_modules package-lock.json
  npm install
  ```
- If you are still stuck, check the CI logs for a diff or error message, and ask for help in the repository.

---

## For Google Employees

If you are a Google employee, please follow internal onboarding instructions to register your GitHub account and be added as a contributor to this repository. (Internal link removed for public documentation.)
