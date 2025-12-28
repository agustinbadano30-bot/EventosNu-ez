import azure.functions as func
from api.main import app as fastapi_app

# The ASGI Function App wrapper allows us to run standard FastAPI on Azure Functions
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
