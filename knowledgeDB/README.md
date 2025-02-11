# Knowledge Database

This folder contains the source of the knowledge database of the Software Modernization Team (SMT) of NASA's Advanced Software Technology Group (ASTG). The online version is deployed to <https://geos-esm.github.io/SMT-Nebulae/>.

## Contributing

Contributing to this documentation is straight forward.

1. Add or change files in the [docs/](docs/) folder as necessary.
2. [Optional] If you have changes the (side) navigation, modify [mkdocs.yml](mkdocs.yml).
3. [Optional] To look at you changes locally, follow our [local setup guide](#local-setup).
4. Push your changes.
    - Changes can be pushed directly to the `main` branch.
    - If you want someone else to have a look, consider making a pull request.

## Deployment

Deployment is automated with GitHub Actions. The [online version](https://geos-esm.github.io/SMT-Nebulae/) is updated for every push to the `main` branch.

## Local setup

A minimalistic local setup could look like this:

```bash
# Setup a virtual environment (in this folder) and activate it
python -m venv .venv
source .venv/bin/activate

# Install mkdocs-material into that virtual environment
pip install mkdocs-material

# Run the built-in development server to look at the documentation locally
mkdocs serve
```
