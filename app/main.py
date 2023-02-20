from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.router import auth


app = FastAPI()

app.include_router(auth.router)


@app.get("/")
def root():
    return RedirectResponse(app.openapi_url)
