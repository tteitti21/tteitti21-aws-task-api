# AWS Task API

A small AWS SAM learning project that builds a serverless task creation API.

The application exposes `POST /tasks`, validates a JSON request body, creates a task object, and stores it in DynamoDB.

## What Is Included

- AWS SAM template in `template.yaml`
- Python Lambda handler in `src/create_task/app.py`
- DynamoDB table managed by CloudFormation/SAM
- HTTP API event wired to `POST /tasks`
- Local DynamoDB option through Docker Compose
- Sample event payload in `events/create_task.json`
- Unit tests in `tests/test_create_task.py`

## Project Structure

```text
.
|-- docker-compose.yml
|-- env.local.json
|-- events/
|   `-- create_task.json
|-- src/
|   `-- create_task/
|       `-- app.py
|-- tests/
|   `-- test_create_task.py
|-- requirements-dev.txt
`-- template.yaml
```

## Requirements

- Python 3.12
- AWS SAM CLI
- AWS CLI configured with credentials for deploys
- Docker, only if using DynamoDB Local or `sam local invoke`

For local tests, install the development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Local Versus AWS DynamoDB

The app is explicit about which DynamoDB it uses.

By default, it uses real AWS DynamoDB:

```text
LOCAL_DYNAMODB_ENABLED is missing or false
```

It only uses DynamoDB Local when this is set:

```text
LOCAL_DYNAMODB_ENABLED=true
DYNAMODB_ENDPOINT=http://host.docker.internal:8000
```

If `LOCAL_DYNAMODB_ENABLED=true` but `DYNAMODB_ENDPOINT` is missing, the app raises an error. This prevents accidentally thinking you are using local DynamoDB when the endpoint was not configured.

Important resource behavior:

```text
sam deploy
  Creates or updates real AWS resources through CloudFormation.

docker compose up
  Starts a local DynamoDB container only. It does not create AWS resources.

sam build
  Builds local artifacts only. It does not create AWS resources.
```

## Run Tests

```powershell
python -m pytest
```

The tests mock DynamoDB, so they do not create local or AWS resources.

## Build With SAM

```powershell
sam build
```

This project currently does not need a runtime `requirements.txt` inside `src/create_task/` because the Lambda handler only uses the Python standard library and `boto3`. AWS Lambda includes `boto3` in the Python runtime.

If the function later imports third-party packages that Lambda does not include, add them to:

```text
src/create_task/requirements.txt
```

## Run DynamoDB Local

Start the local DynamoDB container:

```powershell
docker compose up
```

This starts DynamoDB Local at:

```text
http://localhost:8000
```

The container does not automatically create the `TasksTable` table. Create it locally with:

```powershell
aws dynamodb create-table `
  --table-name TasksTable `
  --attribute-definitions AttributeName=id,AttributeType=S `
  --key-schema AttributeName=id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --endpoint-url http://localhost:8000
```

## Invoke Locally Against DynamoDB Local

After DynamoDB Local is running and the local table exists:

```powershell
sam local invoke CreateTaskFunction `
  --event events/create_task.json `
  --env-vars env.local.json
```

`env.local.json` enables local mode and points the Lambda container at DynamoDB Local.

## Deploy To AWS

```powershell
sam deploy --guided
```

SAM will package the Lambda function, create the DynamoDB table, and deploy the HTTP API through CloudFormation.

After the first guided deploy, future deploys can usually use:

```powershell
sam deploy
```

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

- `TASKS_TABLE` is provided to the deployed Lambda function from the DynamoDB table reference in `template.yaml`.
- `LOCAL_DYNAMODB_ENABLED` is set to `false` in the deployed AWS template, so `DYNAMODB_ENDPOINT` is ignored in AWS unless local mode is explicitly enabled.
- `.aws-sam/`, `.venv/`, test caches, and Python bytecode are ignored because they are generated locally.
- `.vscode/settings.json` is included to help VS Code understand CloudFormation YAML tags like `!Ref`.
