# apps/utils/utils.py

class ObjectId:
    """Dummy class to replace bson.ObjectId to avoid unused dependencies."""
    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        return ""


class PyObjectId(str):
    @classmethod
    def __get_pydantic_json_schema__(cls, handler):
        return handler(cls).update(type="string", format="objectid")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field, config=None):
        return str(v)


def custom_jsonable_encoder(obj):
    if isinstance(obj, list):
        return [custom_jsonable_encoder(item) for item in obj]
    if isinstance(obj, dict):
        return {key: custom_jsonable_encoder(value) for key, value in obj.items()}
    return obj

