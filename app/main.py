from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.router import auth, documents, search
from app.tasks import test_task


app = FastAPI()

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/")
def root():
    test_task.delay(3, 5)
    return RedirectResponse(app.openapi_url)
