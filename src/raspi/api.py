from fastapi import FastAPI
import uvicorn
from functions.database import DataBase
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database connection lifecycle."""
    db = DataBase()
    app.state.db = db
    print("FastAPI startup: Database connection opened.")
    yield
    db.close()
    print("FastAPI shutdown: Database connection closed.")


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/best")
def return_highscores():
    """Returns the top 10 scores of all time."""
    return app.state.db.get_best_alltime()


@app.get("/best-today")
def return_best_today():
    """Returns the top 10 scores from today."""
    return app.state.db.get_best_date(days_ago=0, offset=0)


@app.get("/best-weekly")
def return_best_weekly():
    """Returns the top 10 scores from the last 7 days."""
    return app.state.db.get_best_date(days_ago=7, offset=0)


@app.get("/best-monthly")
def return_best_monthly():
    """Returns the top 10 scores from the last 31 days."""
    # Changed offset from 10 to 0, as 10 seemed like a typo
    return app.state.db.get_best_date(days_ago=31, offset=0)


@app.get("/stats")
def return_stats():
    """Returns game count statistics."""
    return app.state.db.get_stats()


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0",port=50312, reload=True)

