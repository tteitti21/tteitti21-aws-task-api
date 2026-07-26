# Cognito JWT Authentication

The deployed API uses an Amazon Cognito user pool and an API Gateway HTTP API
JWT authorizer.

```text
User signs in to Cognito
  -> Cognito returns an access token
  -> Client sends Authorization: Bearer <access-token>
  -> API Gateway validates the JWT and required access-token scope
  -> Lambda runs only for an authorized request
```

Local development remains separate. `sam local start-api` uses the learning
token from `env.local.json`; it does not require a real Cognito user.

## Deploy The Authentication Resources

Remove local dummy AWS credentials, authenticate to the intended AWS account,
and deploy the existing stack:

```powershell
Remove-Item Env:AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
Remove-Item Env:AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue

aws login
aws sts get-caller-identity
sam build
sam deploy
```

The deployment creates:

- A Cognito user pool
- A public user pool app client without a client secret
- A JWT authorizer on the existing HTTP API
- Outputs for the API URL, user pool ID, and app client ID

The existing DynamoDB table and its items are not replaced by this change.

## Read The Stack Outputs

PowerShell:

```powershell
$stackName = "aws-task-api-dev"

$apiUrl = aws cloudformation describe-stacks `
  --stack-name $stackName `
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue | [0]" `
  --output text

$userPoolId = aws cloudformation describe-stacks `
  --stack-name $stackName `
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue | [0]" `
  --output text

$userPoolClientId = aws cloudformation describe-stacks `
  --stack-name $stackName `
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue | [0]" `
  --output text
```

Inspect the values without printing any token:

```powershell
$apiUrl
$userPoolId
$userPoolClientId
```

## Create A Test User

Choose a real email address for `$email`. The password must contain uppercase,
lowercase, number, and symbol characters and be at least eight characters.
Do not commit the password.

```powershell
$email = "learner@example.com"
$password = "Replace-With-A-Strong-Password1!"

aws cognito-idp admin-create-user `
  --user-pool-id $userPoolId `
  --username $email `
  --user-attributes "Name=email,Value=$email" "Name=email_verified,Value=true" `
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password `
  --user-pool-id $userPoolId `
  --username $email `
  --password $password `
  --permanent
```

These admin commands are convenient for a development user. A real client
application would normally implement sign-up, email verification, sign-in,
password reset, and token refresh through an AWS SDK or Amplify.

## Obtain An Access Token

```powershell
$authResult = aws cognito-idp initiate-auth `
  --client-id $userPoolClientId `
  --auth-flow USER_PASSWORD_AUTH `
  --auth-parameters "USERNAME=$email,PASSWORD=$password" `
  | ConvertFrom-Json

$accessToken = $authResult.AuthenticationResult.AccessToken
```

Treat `$accessToken` and the refresh token as secrets. Do not commit them or
paste them into logs. Use the access token, not the ID token, when calling the
API. The API requires the `aws.cognito.signin.user.admin` scope that Cognito
includes in access tokens issued through `InitiateAuth`.

## Call The Deployed API

PowerShell:

```powershell
$headers = @{ Authorization = "Bearer $accessToken" }

Invoke-RestMethod `
  -Method Get `
  -Uri "$apiUrl/tasks" `
  -Headers $headers
```

Create a task:

```powershell
$body = @{ title = "Authenticated AWS task" } | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "$apiUrl/tasks" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

In Postman, choose **Bearer Token** authorization and paste the access token.
Do not include the local value `local-learning-token` when calling AWS.

## Token And Data Behavior

Access tokens expire. Sign in again or implement the refresh-token flow when
that happens. API Gateway returns `401` when the token is missing, expired,
has the wrong issuer or audience, or fails signature validation. It returns
`403` when the token is valid but lacks the required authorization scope.

Cognito authentication identifies the caller, but the current task data model
does not yet enforce ownership. Every authenticated user can currently list or
fetch every task. The next authorization step should store the JWT `sub` claim
as an owner ID and restrict all reads and writes to that owner.

## Local Versus AWS Tokens

```text
Local SAM API:
  Authorization: Bearer local-learning-token
  Checked by create_task/local/auth.py

Deployed AWS API:
  Authorization: Bearer <Cognito access token>
  Validated by API Gateway before Lambda runs
```