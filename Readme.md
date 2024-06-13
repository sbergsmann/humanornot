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

## Running the Chat Interface

```shell
flet run --web services/chat_page.py
```

# Workflow

## Sprint 1
Deadline 4. June 2024
- Basic chat mechanism (UC1, UC2, SUC1)
- AI callback method (SUC2)
- AI Endpoint check (SUC5)

Temporary:
- "Back to Start Screen Button" for debugging purposes

Optional:
- Implement collecting and storing of chat messages

## Sprint 2
Deadline 11. June 2024
- Prompt Engineering for AI
- Waiting List for Users
- Show System Message when Claim was made
- Store current Claim Situation in the Chat model
