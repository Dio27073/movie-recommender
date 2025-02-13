import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"Starting server on port {port}")
    uvicorn.run(
        "app.main:app",  # Changed from backend.app.main:app
        host="0.0.0.0",
        port=port,
        workers=1,  # Reduced workers to minimize complexity
        timeout_keep_alive=75,
        log_level="info"
    )