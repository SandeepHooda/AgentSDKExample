# AI agent testing
- openAI client
- openAI agent


## Run Locally
`uvicorn main:app --port 8090`
## Test Endpoint
`
  'http://localhost:8090/'
`

## Docker
1. docker build -t ai-agents-adk .
2. docker rmi deed3463cbfc --force
2. docker rm ai-agents-adk
3. docker run -p 7000:7000     ai-agents-adk
4. docker stop ai-agents-adk
5. docker stats ai-agents-adk

## GCP Deployment
1. Create app.yaml and run `gcloud app create -- only for the first time`
2. `gcloud app deploy`
3. `gcloud app browse`

###### H6 Heading **Bold Text** *Italic Text* `Inline code`

- Item 1
  - Sub item
1. First item
- [x] Completed task
