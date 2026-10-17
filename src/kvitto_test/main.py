from fastapi import FastAPI

from kvitto_test.api.router import api_router


app = FastAPI(title="Kvitto Payment API")
app.include_router(api_router)
