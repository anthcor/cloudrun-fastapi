import logging
import os
import sys
import time

from fastapi.security import OAuth2PasswordBearer
from google.cloud import secretmanager_v1beta1 as secretmanager

from v1.schemas.secrets_config import SecretsConfig


class Config:
    def get_logger(self, level: int = logging.INFO) -> logging.Logger:
        tz = time.strftime("%z")
        logging.config = logging.basicConfig(
            format=(
                f"[%(asctime)s.%(msecs)03d {tz}] "
                "[%(process)s] [%(pathname)s L%(lineno)d] "
                "[%(levelname)s] %(message)s"
            ),
            level=level,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logger = logging.getLogger(__name__)
        return logger

    def build_secrets_config(self, project_id: str = "") -> SecretsConfig:
        result = SecretsConfig()
        if not project_id:
            return result
        for secret_id in result.dict().keys():
            version_path = secrets_client.secret_version_path(
                project_id, secret_id, "latest"
            )
            secret_version = secrets_client.access_secret_version(name=version_path)
            secret_data = secret_version.payload.data.decode("UTF-8")
            setattr(result, secret_id, secret_data)
        return result


c = Config()
logger = c.get_logger()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/login")
project_id = os.getenv("PROJECT_ID")

# if running in a project, cloud run or cloud build
if project_id:
    secrets_client = secretmanager.SecretManagerServiceClient()
    apisecrets = c.build_secrets_config(project_id)
    if "pytest" in "".join(sys.argv):
        # use the container in cloudbuild
        url = "postgresql+psycopg2://postgres@postgres:5432/cloudrunfastapi_test"
        apisecrets.DATABASE_URL = url

# if running locally
else:
    apisecrets = c.build_secrets_config()
    if "pytest" in "".join(sys.argv):
        # use localhost in local env
        url = "postgresql+psycopg2://postgres@localhost:5432/cloudrunfastapi_test"
        apisecrets.DATABASE_URL = url
