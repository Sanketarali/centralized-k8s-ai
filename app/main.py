from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from kubernetes import client, config
from openai import OpenAI
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

# Initialize OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not set")
client_openai = OpenAI(api_key=openai_api_key)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/prompt")
async def process_prompt(prompt: str = Form(...)):
    try:
        # Call OpenAI API
        response = client_openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Kubernetes expert."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_reply = response.choices[0].message.content

        # List pods in kube-system
        pods = v1.list_namespaced_pod(namespace="kube-system")
        pod_names = [pod.metadata.name for pod in pods.items]

        return {"ai_reply": ai_reply, "pods": pod_names}

    except Exception as e:
        logging.error(f"Error processing prompt: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
