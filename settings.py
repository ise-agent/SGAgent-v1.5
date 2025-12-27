from datetime import datetime
from pydantic import Field
from pydantic_settings import BaseSettings
import pandas as pd
import os
import subprocess
from pathlib import Path


class Settings(BaseSettings):
    """Configuration settings with support for environment variables."""

    api_key: str = Field(default="", env="API_KEY")
    base_url: str = Field(
        default="",
        env="BASE_URL",
    )
    model: str = Field(default="", env="MODEL")

    TEST_BED: str = Field(default="", env="TEST_BED")
    PROJECT_NAME: str = Field(default="", env="PROJECT_NAME")
    INSTANCE_ID: str = Field(default="", env="INSTANCE_ID")
    DATASET: str = Field(default="lite", env="DATASET")
    PROBLEM_STATEMENT: str = Field(default="", env="PROBLEM_STATEMENT")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    )
    LOG_DIR: str = Field(default="results/logs", env="LOG_DIR")
    
    DOCKER_IMAGE:str = Field(default="",env="DOCKER_IMAGE")
    def load_problem_statement(self) -> None:
        try:
            dataset_file = f"dataset/{self.DATASET}.parquet"
            if not os.path.exists(dataset_file):
                return
            df = pd.read_parquet(dataset_file)
            filtered_df = df[df["instance_id"] == self.INSTANCE_ID]
            problem_dict = filtered_df.iloc[0].to_dict()
            self.PROBLEM_STATEMENT = problem_dict.get(
                "problem_statement", str(problem_dict)
            )
            self.DOCKER_IMAGE = f"sweb.eval.x86_64.{self.INSTANCE_ID}:latest"

            return

        except Exception as e:
            print(f"{e=}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
if not settings.PROBLEM_STATEMENT:
    settings.load_problem_statement()
