from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.router import auth, documents, search
from app.tasks import test_task


app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/")
def root():
    test_task.delay(3, 5)
    return RedirectResponse(app.openapi_url)
