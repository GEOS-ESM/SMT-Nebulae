# Python ecosystem

- Any tests should be run within the `.venv` virtual environment.
- Once a task is finished, `pre-commit` should be run to lint the code. It _must_ be run selectively, e.g. onlye against the files that have changed. If after a 3 attempts at fixing errors are still present, do not continue, feedback to the user and stop linting.