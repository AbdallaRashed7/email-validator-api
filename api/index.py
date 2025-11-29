from fastapi import FastAPI

app = FastAPI()

@app.get("/api/python")
def hello_world():
    return {"message": "System is Online", "status": "Success"}

@app.get("/")
def root():
    return {"message": "Hello from Vercel!"}
