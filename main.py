from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from orquesta_sdk import Orquesta, OrquestaClientOptions

# Load environment variables
load_dotenv()
orquesta_api_key = os.getenv("ORQUESTA_API_KEY")

# Initialize Orquesta client
options = OrquestaClientOptions(
    api_key=orquesta_api_key,
    environment="production"
)
client = Orquesta(options)

# Initialize FastAPI app
app = FastAPI()

# Define the request model
class OrquestaRequest(BaseModel):
    content: str
    keywords: str
    chat_history: str

@app.post("/invoke-orquesta")
async def invoke_orquesta(req_body: OrquestaRequest):
    try:
        # Invoke the Orquesta deployment
        deployment = client.deployments.invoke(
            key="spacewell-blog",
            context={
                "environments": []
            },
            inputs={
                "content": req_body.content,
                "keywords": req_body.keywords,
                "history": req_body.chat_history
            },
            metadata={
                "custom-field-name": "custom-metadata-value"
            }
        )

        # Process the response as needed
        # For now, just return a simple acknowledgment
        return {"status": "processing", "message": "Request is being processed", "deployment_id": deployment.id}

    except Exception as e:
        # Handle errors
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
