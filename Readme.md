# Human or Not

[Video Link](https://drive.google.com/file/d/1-4VbuQw8aGQjahIwJrtBQHgPW7zBGmJr/view?usp=sharing)

## Install Environment

either with poetry or the given `requirements.txt` file

### Poetry
- install [Poetry](https://python-poetry.org/docs/#installation)
- **Tip:** Make sure that your environment is install in the local folder for better overview by running
```shell
poetry config virtualenvs.in-project true
```
- run `poetry install` in the cloned folder

### Pip
- make a new environment and run `pip install -r requirements.txt`

## Running HumanOrNot

```shell
flet run --web services/chat_page.py
```

### Endpoints
the most easy way is to register on [OpenAI](https://platform.openai.com/) and create an API key.

### Example Endpoint Config for OpenAI:
- endpoint_base_url: https://api.openai.com/v1
- model_name: "gpt-3.5-turbo-0125"
- your api key from the OpenAI API

Add the enpoint using the interface. The Api-key handling and save storage is all handled automatically.

### Simulate multiple users

When running the shell command above, a browser window should pop up. To simulate multiple users, you can easily just duplicate the browser window with the same url and port (see video).
