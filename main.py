from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from orquesta_sdk import Orquesta, OrquestaClientOptions
import asyncio

# Load environment variables
load_dotenv()
orquesta_api_key = os.getenv("ORQUESTA_API_KEY")

# Initialize Orquesta client
options = OrquestaClientOptions(
    api_key=orquesta_api_key,
    environment="production"
)
client = Orquesta(options)

# In-memory cache and expiration settings
cache = {}
cache_lifetime = timedelta(minutes=10)  # Cache entry lifetime

# Define the request model
class OrquestaRequest(BaseModel):
    content: str
    keywords: str
    history: str

# Background task function
def orquesta_task(request_id: str, content: str, keywords: str, history: str):
    try:
        deployment = client.deployments.invoke(
            key="spacewell-blog",
            context={"environments": []},
            inputs={
                "content": content,
                "keywords": keywords,
                "history": history
            },
            metadata={"custom-field-name": "custom-metadata-value"}
        )
        # Store the result with a timestamp
        cache[request_id] = (datetime.now(), deployment.choices[0].message.content)
    except Exception as e:
        cache[request_id] = (datetime.now(), f"Error: {str(e)}")

# Cache maintenance coroutine
async def maintain_cache():
    while True:
        await asyncio.sleep(60)  # Run maintenance every minute
        now = datetime.now()
        expired_keys = [key for key, (timestamp, _) in cache.items() if now - timestamp > cache_lifetime]
        for key in expired_keys:
            del cache[key]

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Start up logic (e.g., cache maintenance)
    cache_maintenance_task = asyncio.create_task(maintain_cache())
    yield  # Start the application
    # Shutdown logic
    cache_maintenance_task.cancel()

app = FastAPI(lifespan=app_lifespan)

@app.post("/invoke-orquesta/{request_id}")
async def invoke_orquesta(request_id: str, background_tasks: BackgroundTasks, req_body: OrquestaRequest):
    background_tasks.add_task(orquesta_task, request_id, req_body.content, req_body.keywords, req_body.history)
    return {"status": "accepted", "message": "Request is being processed in the background"}

@app.get("/get-result/{request_id}")
async def get_result(request_id: str):
    if request_id in cache:
        timestamp, result = cache.pop(request_id)
        return {"result": result}
    else:
        raise HTTPException(status_code=404, detail="Result not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
