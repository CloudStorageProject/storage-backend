from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, status
from app.database import engine, Base
from app.auth.routes import auth_router
from app.folders.routes import folder_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unexpected error: {str(exc)}")

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Unexpected error."})

# should be removed in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(folder_router, prefix="/folders")
