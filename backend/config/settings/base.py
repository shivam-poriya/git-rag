from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from main import app
import os
from config.settings.utils import load_env
from fastapi.staticfiles import StaticFiles

environment = os.getenv("ENVIRONMENT", "development")

load_env(environment)


def get_message(root: str, fields: list, error_message: str, return_message=None):
    return_message = return_message or {}

    if root not in return_message:
        return_message[root] = {}

    for i, field in enumerate(fields):
        if len(fields) == 1:
            return_message[root].update({field: error_message})
        else:
            new_fields = fields.copy()
            del new_fields[i]
            response = get_message(
                root=field,
                fields=new_fields,
                error_message=error_message,
                return_message=return_message[root],
            )
            return_message[root].update(response)
            break

    return return_message


@app.exception_handler(RequestValidationError)
async def validation_bad_request_exception_handler(request, exc):
    message = None
    for x in exc.errors():
        fields = [entry for entry in x["loc"] if entry != "body"]
        if len(fields) == 0:
            message = f"Please provide a body."
        elif len(fields) == 1:
            # message.update({fields[0]: x['msg']})
            message = f"{fields[0]} {x['msg']}"
            break
        else:
            # for dict / list with errors inside it
            message = f"{fields[1]} {x['msg']}"
            break
            # field_root = fields[0]
            # del fields[0]
            #
            # message = get_message(
            #     root=field_root,
            #     fields=fields,
            #     error_message=x["msg"],
            #     return_message=message,
            # )

    return JSONResponse(
        status_code=400,
        content={
            "detail": message,
        },
    )


# Secret key for JWT token
SECRET_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJSb2xlIjoiQWRtaW4iLCJJc3N1ZXIiOiJJc3N1ZXIiLCJVc2VybmFtZSI6IkphdmFJblVzZSIsImV4cCI6MTcxNTkzNDI5OCwiaWF0IjoxNzE1OTM0Mjk4fQ.thjmNb3vu101wTcfVW3xeo-iIZB4q4ZNK-DirfV_VMk"
REFRESH_TOKEN_SECRET_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJSb2xlIjoiQWRtaW4iLCJJc3N1ZXIiOiJJc3N1ZXIiLCJVc2VybmFtZSI6IkphdmFJblVzZSIsImV4cCI6MTcxNTkzODIwMCwiaWF0IjoxNzE1OTM4MjAwfQ.dB1sPvF-HfTutxb0YTv5Brz4OTmrlnLUGEt-WhrsXuA"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
REFRESH_TOKEN_EXPIRE_DAYS = 7

UPLOAD_DIR = "media"

app.mount("/media", StaticFiles(directory="media"), name="media")
