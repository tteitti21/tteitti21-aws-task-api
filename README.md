# AWS Task API

A small AWS SAM learning project that builds a serverless task creation API.

The application exposes `POST /tasks`, validates a JSON request body, creates a task object, and stores it in DynamoDB.

## What Is Included

- AWS SAM template in `template.yaml`
- Python Lambda handler in `src/create_task/app.py`
- DynamoDB table managed by CloudFormation/SAM
- HTTP API event wired to `POST /tasks`
- Sample event payload in `events/create_task.json`
- Unit tests in `tests/test_create_task.py`

## Project Structure

```text
.
├── events/
│   └── create_task.json
├── src/
│   └── create_task/
│       └── app.py
├── tests/
│   └── test_create_task.py
├── requirements-dev.txt
└── template.yaml
```

## Requirements

- Python 3.12
- AWS SAM CLI
- AWS CLI configured with credentials for deploys

For local tests, install the development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Run Tests

```powershell
pytest
```

The tests mock DynamoDB, so they do not create AWS resources.

## Build With SAM

```powershell
sam build
```

This project currently does not need a runtime `requirements.txt` inside `src/create_task/` because the Lambda handler only uses the Python standard library and `boto3`. AWS Lambda includes `boto3` in the Python runtime.

If the function later imports third-party packages that Lambda does not include, add them to:

```text
src/create_task/requirements.txt
```

## Invoke Locally

```powershell
sam local invoke CreateTaskFunction --event events/create_task.json
```

Local invocation needs Docker running. Because the function writes to DynamoDB, local invocation also needs AWS credentials and a real table name supplied through the `TASKS_TABLE` environment variable or a SAM environment file.

## Deploy

```powershell
sam deploy --guided
```

SAM will package the Lambda function, create the DynamoDB table, and deploy the HTTP API through CloudFormation.

## API Request

`POST /tasks`

```json
{
  "title": "Learn AWS Lambda"
}
```

Successful response:

```json
{
  "id": "generated-uuid",
  "title": "Learn AWS Lambda",
  "completed": false,
  "createdAt": "2026-07-12T00:00:00+00:00"
}
```

## Notes

- `TASKS_TABLE` is provided to the Lambda function from the DynamoDB table reference in `template.yaml`.
- `.aws-sam/`, `.venv/`, test caches, and Python bytecode are ignored because they are generated locally.
- `.vscode/settings.json` is included to help VS Code understand CloudFormation YAML tags like `!Ref`.
