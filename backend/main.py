from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "OSS-2026-10 백엔드 서버"}