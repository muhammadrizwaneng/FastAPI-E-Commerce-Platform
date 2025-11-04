import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)

# import asynciozz
# from uvicorn import Config, Server
# import uvicorn

# if __name__ == "__main__":
#     async def main():
#         # Configure the Uvicorn server
#         config = Config(
#             app="app:app",
#             host="0.0.0.0",
#             port=8080,
#             reload=True,
#         )
#         server = Server(config)

#         try:
#             # Start the server
#             await server.serve()
#         except KeyboardInterrupt:
#             # Handle graceful shutdown
#             print("Shutting down gracefully...")

#     # Run the main coroutine
#     uvicorn.run(main())
