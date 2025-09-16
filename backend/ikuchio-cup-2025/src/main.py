from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from routers import users, rooms

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"message": "Hello!"}


app.include_router(users.users_router)
app.include_router(rooms.rooms_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
