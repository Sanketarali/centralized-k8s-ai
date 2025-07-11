from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from kubernetes import client, config
import google.generativeai as genai
import os
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Load kube config
if os.getenv("KUBERNETES_SERVICE_HOST"):
    config.load_incluster_config()
else:
    config.load_kube_config()

v1 = client.CoreV1Api()

# Initialize Gemini
genai_api_key = os.getenv("GEMINI_API_KEY")
if not genai_api_key:
    raise ValueError("GEMINI_API_KEY not set")
genai.configure(api_key=genai_api_key)
model = genai.GenerativeModel('gemini-pro')

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/prompt")
async def process_prompt(prompt: str = Form(...)):
    try:
        # Call Gemini API
        response = model.generate_content(prompt)
        ai_reply = response.text

        # List pods in kube-system
        pods = v1.list_namespaced_pod(namespace="kube-system")
        pod_names = [pod.metadata.name for pod in pods.items]

        return {"ai_reply": ai_reply, "pods": pod_names}

    except Exception as e:
        logging.error(f"Error processing prompt: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
