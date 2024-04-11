# Human or Not

## Install Environment

- install [Poetry](https://python-poetry.org/docs/#installation)
- If you need a `requirements.txt` file, run
```shell
poetry export --without-hashes --without dev -f requirements.txt -o requirements.txt
```
- **Tip:** Make sure that your environment is install in the local folder for better overview by running
```shell
poetry config virtualenvs.in-project true
```

- run `poetry install` in the cloned folder
