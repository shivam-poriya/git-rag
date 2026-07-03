import os
from dotenv import load_dotenv


def load_env(env):
    dotenv_path = os.path.join(os.path.dirname(__file__), 'env', f'.env.{env}')
    load_dotenv(dotenv_path)
