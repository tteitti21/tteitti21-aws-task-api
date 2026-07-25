# AWS Task API

A learning-focused serverless task API built with AWS SAM, Python Lambda,
API Gateway, and DynamoDB.

The API supports:

- `POST /tasks` to create a task
- `GET /tasks` to list tasks
- A simple bearer token check inside the Lambda handler
- DynamoDB Local for development
- AWS DynamoDB for deployed environments

## How The Pieces Connect

Local development:

```text
Postman
  -> SAM Local HTTP API on localhost:3000
  -> Lambda runtime container
  -> DynamoDB Local container on localhost:8000
  -> Docker named volume
```

Deployed to AWS:

```text
Internet client
  -> API Gateway
  -> Lambda
  -> AWS DynamoDB
```

`template.yaml` describes the Lambda, API routes, DynamoDB table, environment
variables, and IAM permissions. `sam deploy` sends that description to
CloudFormation, which creates or updates the real AWS resources.

## Project Structure

```text
.
|-- docker-compose.yml
|-- docs/
|   `-- local-development-commands.md
|-- env.local.docker-network.json
|-- env.local.json
|-- events/
|   `-- create_task.json
|-- src/
|   `-- create_task/
|       |-- app.py
|       |-- config.py
|       `-- storage/
|           |-- aws_dynamodb.py
|           |-- local_dynamodb.py
|           `-- tasks_table.py
|-- tests/
|   |-- test_create_task.py
|   `-- test_dynamodb.py
|-- requirements-dev.txt
|-- samconfig.toml
`-- template.yaml
```

Generated directories such as `.venv/` and `.aws-sam/` are intentionally not
committed.

Source responsibilities are deliberately separated:

- `app.py` handles HTTP events, authentication, validation, and task behavior.
- `config.py` validates shared boolean environment variables.
- `storage/tasks_table.py` makes the explicit local-versus-AWS choice.
- `storage/local_dynamodb.py` owns the local endpoint and dummy credentials.
- `storage/aws_dynamodb.py` creates the normal AWS DynamoDB resource.

The request handler does not contain local endpoint or AWS resource setup.

## Requirements

Install these before using the repository:

- Git
- Python 3.12, matching the Lambda runtime
- Docker Desktop, or Docker Engine with Docker Compose
- AWS SAM CLI
- AWS CLI
- Postman, curl, or another HTTP client for API testing

Docker must be running before `docker compose` or `sam local` commands are
used. Internet access is required the first time Docker and SAM download their
images.

Real AWS credentials are required only for deployment and other commands that
contact AWS. Local development uses dummy credentials.

## Safety: Local Versus AWS

These commands stay on your computer:

```text
docker compose up
sam build
sam local invoke
sam local start-api
aws dynamodb ... --endpoint-url http://localhost:8000
```

This command creates or updates billable resources in the active AWS account:

```text
sam deploy
```

Always check for `--endpoint-url http://localhost:8000` before running an AWS
CLI DynamoDB command intended for the local database.

## Fresh Clone: Local Setup

### 1. Clone And Enter The Repository

```bash
git clone <repository-url>
cd aws-task-api
```

### 2. Create A Python Environment

The virtual environment is needed for tests. SAM runs the Lambda itself in a
Docker container.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

If PowerShell blocks activation, either allow it for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Or use the virtual environment without activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

If `python3.12` is not the installed command name, use the command that points
to Python 3.12.

### 3. Start DynamoDB Local

```bash
docker compose up -d
docker compose ps
```

The container exposes DynamoDB Local at `http://localhost:8000`. Starting or
stopping the container does not create AWS resources.

### 4. Set Dummy Credentials In The Host Terminal

SAM CLI reads host AWS credentials before it starts a Lambda container. An
expired `aws login` or SSO session can therefore break local execution even
though the Lambda is configured for DynamoDB Local.

Set dummy credentials in the same terminal used for local SAM and local AWS
CLI commands.

Windows PowerShell:

```powershell
$env:AWS_ACCESS_KEY_ID = "local"
$env:AWS_SECRET_ACCESS_KEY = "local"
$env:AWS_DEFAULT_REGION = "eu-north-1"
Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
```

macOS or Linux:

```bash
export AWS_ACCESS_KEY_ID=local
export AWS_SECRET_ACCESS_KEY=local
export AWS_DEFAULT_REGION=eu-north-1
unset AWS_SESSION_TOKEN
```

These values are deliberately fake. DynamoDB Local does not validate them.
They are separate from `env.local.json`, which configures the Lambda container.

Do not run `sam deploy` from a terminal using these dummy credentials.

### 5. Create The Local Table

This is required once for a new Docker volume.

Windows PowerShell:

```powershell
aws dynamodb create-table `
  --table-name TasksTable `
  --attribute-definitions AttributeName=id,AttributeType=S `
  --key-schema AttributeName=id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --endpoint-url http://localhost:8000
```

macOS or Linux:

```bash
aws dynamodb create-table \
  --table-name TasksTable \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8000
```

If the command reports `ResourceInUseException`, the table already exists and
can be reused. Confirm it with:

```bash
aws dynamodb describe-table --table-name TasksTable --endpoint-url http://localhost:8000
```

### 6. Build The Lambda

```bash
sam build
```

This creates or refreshes `.aws-sam/build/`. It does not start containers or
create AWS resources.

The message below is expected in this project:

```text
requirements.txt file not found. Continuing the build without dependencies.
```

The handler uses only the Python standard library and `boto3`, which is
provided by the Lambda Python runtime. Add `src/requirements.txt` if
third-party runtime packages are added later.

### 7. Start The Local HTTP API

Docker Desktop on Windows, macOS, or Linux:

```bash
sam local start-api --env-vars env.local.json
```

`env.local.json` tells the Lambda to connect to:

```text
http://host.docker.internal:8000
```

On a Linux Docker Engine installation where `host.docker.internal` is not
available, join the SAM container to the Compose network instead:

```bash
sam local start-api \
  --docker-network aws-task-network \
  --env-vars env.local.docker-network.json
```

Keep this terminal running. The API is normally available at:

```text
http://127.0.0.1:3000
```

If port `3000` is already in use:

```bash
sam local start-api --port 3001 --env-vars env.local.json
```

Use `http://127.0.0.1:3001` for requests in that case.

## Call The API

Local authentication is enabled with this learning token:

```text
local-learning-token
```

### Postman: Create A Task

```text
Method: POST
URL: http://127.0.0.1:3000/tasks
Headers:
  Content-Type: application/json
  Authorization: Bearer local-learning-token
Body type: raw JSON
```

```json
{
  "title": "Learn AWS Lambda",
  "description": "Created from Postman",
  "priority": "high"
}
```

The Lambda accepts additional JSON fields, but it always controls `id`,
`title`, `completed`, and `createdAt`.

### Postman: List Tasks

```text
Method: GET
URL: http://127.0.0.1:3000/tasks
Header:
  Authorization: Bearer local-learning-token
```

### curl: Create A Task

PowerShell:

```powershell
curl.exe -X POST http://127.0.0.1:3000/tasks `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer local-learning-token" `
  -d '{\"title\":\"Learn AWS Lambda\"}'
```

macOS or Linux:

```bash
curl -X POST http://127.0.0.1:3000/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-learning-token" \
  -d '{"title":"Learn AWS Lambda"}'
```

### curl: List Tasks

PowerShell:

```powershell
curl.exe http://127.0.0.1:3000/tasks `
  -H "Authorization: Bearer local-learning-token"
```

macOS or Linux:

```bash
curl http://127.0.0.1:3000/tasks \
  -H "Authorization: Bearer local-learning-token"
```

## Invoke The Lambda Without An HTTP Server

The sample event includes the local bearer token.

Windows PowerShell:

```powershell
sam local invoke CreateTaskFunction `
  --event events/create_task.json `
  --env-vars env.local.json
```

macOS or Linux:

```bash
sam local invoke CreateTaskFunction \
  --event events/create_task.json \
  --env-vars env.local.json
```

For Linux Docker Engine networking:

```bash
sam local invoke CreateTaskFunction \
  --docker-network aws-task-network \
  --event events/create_task.json \
  --env-vars env.local.docker-network.json
```

`sam local invoke` executes one Lambda event and exits. Use
`sam local start-api` for Postman or repeated HTTP requests.

## Inspect Local Data

List the local tables:

```bash
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

Read all local task items:

```bash
aws dynamodb scan --table-name TasksTable --endpoint-url http://localhost:8000
```

You can also use `GET /tasks` from Postman or curl.

## Everyday Local Workflow

After the first setup, the usual workflow is:

```bash
docker compose up -d
sam build
sam local start-api --env-vars env.local.json
```

Set the dummy host credentials first whenever a new terminal is opened.

Run `sam build` again after changing:

- Lambda source code
- A Lambda runtime `requirements.txt`
- The handler, runtime, `CodeUri`, layers, or related template configuration

A rebuild is generally unnecessary after changing only the README, tests,
Postman requests, or `env.local.json`. Restart `sam local start-api` after
changing local environment variables.

## Run Tests

With the virtual environment activated:

```bash
python -m pytest
```

Use `python -m pytest`, not the standalone `pytest` command. This ensures the
repository root is on Python's import path.

The tests mock DynamoDB and do not create local or AWS resources.

## Stop, Restart, Or Reset Local Services

Stop SAM with `Ctrl+C`.

Stop DynamoDB but keep its container and data:

```bash
docker compose stop
```

Start it again:

```bash
docker compose start
```

Remove the container and network while preserving the named data volume:

```bash
docker compose down
```

Recreate the container using the existing data:

```bash
docker compose up -d
```

Delete the container and the named volume, including all local tables and
items:

```bash
docker compose down -v
```

After `down -v`, create `TasksTable` again before invoking the Lambda.

## Deploy To AWS

Deployment requires real AWS credentials and creates or updates real AWS
resources.

First remove the dummy local credentials.

Windows PowerShell:

```powershell
Remove-Item Env:AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
Remove-Item Env:AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
```

macOS or Linux:

```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
```

Authenticate using the AWS CLI method used by your account, then verify the
account and identity before deploying:

```bash
aws sts get-caller-identity
```

For the first deployment:

```bash
sam build
sam deploy --guided
```

Suggested learning configuration:

```text
Stack name: aws-task-api-dev
Region: eu-north-1
Confirm changes before deploy: Yes
Allow SAM CLI IAM role creation: Yes
Disable rollback: No
Save arguments to configuration file: Yes
```

The `AuthToken` prompt may not display typed or pasted text because the
CloudFormation parameter uses `NoEcho: true`.

After the first guided deployment, `samconfig.toml` stores the normal deployment
choices, so later deployments can usually use:

```bash
sam build
sam deploy
```

`sam deploy` does not read `env.local.json`. The deployed template explicitly
sets `LOCAL_DYNAMODB_ENABLED=false`, so the deployed Lambda uses AWS DynamoDB.

Resources can be inspected in the AWS Console in the configured region:

- CloudFormation: stack and generated resources
- Lambda: function, logs, and environment variables
- API Gateway: HTTP API and invoke URL
- DynamoDB: table and items
- CloudWatch: Lambda execution logs

## Authentication Scope

The project checks a static bearer token inside the Lambda. API Gateway still
invokes the Lambda, and the Lambda returns `401` when the token is missing or
incorrect.

This is suitable for learning but not production authentication. A production
API should normally use an API Gateway JWT authorizer, Amazon Cognito, or
another identity provider, and should store secrets outside source control.

## Troubleshooting

### SAM Says The AWS Session Has Expired

This happens before Lambda starts when SAM tries to refresh host AWS
credentials. Set the dummy credentials from the local setup section in the
same terminal, stop SAM, and restart it.

### The API Returns `401 Unauthorized`

Include:

```text
Authorization: Bearer local-learning-token
```

The header name is case-insensitive, but the token value must match exactly.

### The API Returns `502 Internal Server Error`

Read the terminal running `sam local start-api`; the actual Lambda exception is
printed there. Common causes are a missing local table, DynamoDB not running,
or local environment variables not being loaded.

### DynamoDB Reports `ResourceNotFoundException`

The container is running, but `TasksTable` has not been created in the current
Docker volume. Run the local `create-table` command.

### DynamoDB Reports `ResourceInUseException`

`TasksTable` already exists. Continue using it; do not recreate it.

### Port `8000` Refuses Connections

Check Docker:

```bash
docker compose ps
docker compose logs dynamodb-local
```

The `dynamodb-local` service should be running with port `8000` published.

### Source Changes Do Not Appear

Stop SAM, rebuild, and restart:

```bash
sam build
sam local start-api --env-vars env.local.json
```

SAM runs the copy under `.aws-sam/build`, not necessarily the source file
directly.

### `pytest` Cannot Import `src`

Run:

```bash
python -m pytest
```

Also confirm the selected interpreter belongs to this repository's `.venv`.

### VS Code Reports A YAML Schema Download Error

This does not affect `sam build` or deployment. The included
`.vscode/settings.json` disables the unavailable remote schema and declares
CloudFormation tags such as `!Ref`.

Validate the template with SAM:

```bash
sam validate --template-file template.yaml
```

## Additional Command Reference

See [docs/local-development-commands.md](docs/local-development-commands.md)
for a shorter command-oriented reference.
