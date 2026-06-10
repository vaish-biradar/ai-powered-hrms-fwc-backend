from fastapi import HTTPException, APIRouter

# Utility functions
from utils.database import db  # Directly import db


# Define the router
cleardb = APIRouter()

@cleardb.delete("/clear-db")
def clear_database(collection: str = None):
    """
    API endpoint to clear the database.
    - If `collection` is provided (e.g., 'resumes' or 'jds'), only that collection is cleared.
    - If `collection` is not provided, the entire database is cleared.
    """
    try:
        db.clear_db(collection)  # Clear the specified collection or the entire database
        
        if collection:
            return {"message": f"Collection '{collection}' cleared successfully."}
        return {"message": "Database cleared successfully."}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
