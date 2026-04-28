from fastapi import APIRouter

router = APIRouter()

@router.get("/", include_in_schema=False)
def root():
    return {"message": "Welcome to the JavaRushAIBot!"}

@router.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
