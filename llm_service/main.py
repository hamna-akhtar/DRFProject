"""FastAPI LLM microservice"""

from rest_framework import status
from fastapi import FastAPI, HTTPException, Header
from llama_cpp import Llama
from contextlib import asynccontextmanager

llm_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """load model only once on startup"""
    global llm_model
    print("Loading LLM model...")
    llm_model = Llama(
        model_path="llm_models/Phi-3-mini-4k-instruct-q4.gguf",
        n_ctx=4096,
        n_threads=4,
        # verbose=False,
    )
    print("Model loaded!")
    yield
    llm_model = None


app = FastAPI(lifespan=lifespan)


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "helloletmeaccessthefastapimicroserviceforllm":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
        )
    else:
        print("api key verified!")


@app.post("/generate")
async def generate(request: dict, x_api_key: str = Header(...)):
    global llm_model
    await verify_api_key(x_api_key)

    if llm_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded"
        )

    prompt = request.get("prompt")
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing prompt in request body",
        )

    try:
        print("llm service generating response...")
        response = llm_model(prompt, max_tokens=512, temperature=0.7)
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
