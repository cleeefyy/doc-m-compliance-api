from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Doc M Compliance Checker is running!"}

