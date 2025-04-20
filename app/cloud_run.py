import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    # Cloud Run sets PORT environment variable
    port = int(os.environ.get("PORT", 8001))
    # Use 0.0.0.0 to listen on all interfaces
    uvicorn.run(app, host="0.0.0.0", port=port)
