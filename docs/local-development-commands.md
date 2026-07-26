# Local Development Commands

This file explains the common commands for working with this AWS SAM project locally.

## Quick Safety Rule

These commands do not create real AWS resources:

```text
sam build
sam local invoke
sam local start-api
docker compose up
aws dynamodb ... --endpoint-url http://localhost:8000
```

This command creates or updates real AWS resources:

```text
sam deploy --guided
```

## PowerShell Commands

Use these commands on Windows PowerShell.

### Start DynamoDB Local

```powershell
docker compose up
```

This starts a local DynamoDB container on your machine.

### Create The Local Table

```powershell
aws dynamodb create-table `
  --table-name TasksTable `
  --attribute-definitions AttributeName=id,AttributeType=S `
  --key-schema AttributeName=id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --endpoint-url http://localhost:8000
```

This creates the `TasksTable` table inside DynamoDB Local only.

### Build The SAM App

```powershell
sam build
```

This updates the local build output in `.aws-sam/build/`.

### Invoke The Lambda Locally

```powershell
sam local invoke CreateTaskFunction `
  --event events/create_task.json `
  --env-vars env.local.json
```

This runs the Lambda locally and uses `env.local.json` to point the function at DynamoDB Local.

### Run The Local HTTP API

```powershell
sam local start-api --env-vars env.local.json
```

This starts a local HTTP API, usually at:

```text
http://127.0.0.1:3000
```

Keep this terminal running while you use Postman.

### View Local Table Items With AWS CLI

```powershell
aws dynamodb scan `
  --table-name TasksTable `
  --endpoint-url http://localhost:8000
```

This reads items from the local DynamoDB table.

## macOS And Linux Commands

Use these commands in bash, zsh, or another POSIX-style shell.

### Start DynamoDB Local

```bash
docker compose up
```

### Create The Local Table

```bash
aws dynamodb create-table \
  --table-name TasksTable \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8000
```

### Build The SAM App

```bash
sam build
```

### Invoke The Lambda Locally

```bash
sam local invoke CreateTaskFunction \
  --event events/create_task.json \
  --env-vars env.local.json
```

### Run The Local HTTP API

```bash
sam local start-api --env-vars env.local.json
```

### View Local Table Items With AWS CLI

```bash
aws dynamodb scan \
  --table-name TasksTable \
  --endpoint-url http://localhost:8000
```

## Postman

Postman sends HTTP requests, so use `sam local start-api` instead of `sam local invoke`.

Start the local API:

```bash
sam local start-api --env-vars env.local.json
```

### Create A Task In Postman

```text
Method: POST
URL: http://127.0.0.1:3000/tasks
Headers:
  Content-Type: application/json
  Authorization: Bearer local-learning-token
Body: raw JSON
```

Body:

```json
{
  "title": "Learn AWS Lambda from Postman"
}
```

### List Tasks In Postman

```text
Method: GET
URL: http://127.0.0.1:3000/tasks
Header:
  Authorization: Bearer local-learning-token
```

This calls the app's `GET /tasks` route. The Lambda scans the task table and returns:

```json
{
  "tasks": []
}
```

After creating tasks, the array should contain saved task objects.


## Local Authentication

Local SAM uses a simple bearer token check inside the Lambda function. The deployed AWS API uses a Cognito JWT authorizer instead.

For local development, `env.local.json` sets:

```text
LOCAL_AUTH_ENABLED=true
LOCAL_AUTH_TOKEN=local-learning-token
```

So every Postman request needs this header:

```text
Authorization: Bearer local-learning-token
```

If the header is missing or the token is wrong, the API returns:

```json
{
  "error": "Unauthorized"
}
```

This learning token is local-only. In AWS, API Gateway validates a Cognito access token before invoking Lambda. See `docs/cognito-authentication.md`.

## One-Line Versions

These work in both PowerShell and macOS/Linux shells.

```bash
aws dynamodb create-table --table-name TasksTable --attribute-definitions AttributeName=id,AttributeType=S --key-schema AttributeName=id,KeyType=HASH --billing-mode PAY_PER_REQUEST --endpoint-url http://localhost:8000
```

```bash
sam local invoke CreateTaskFunction --event events/create_task.json --env-vars env.local.json
```

```bash
sam local start-api --env-vars env.local.json
```

```bash
aws dynamodb scan --table-name TasksTable --endpoint-url http://localhost:8000
```
