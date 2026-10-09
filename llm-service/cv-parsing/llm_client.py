"""
llm_client.py — Azure OpenAI call wrapper.

Supports:
- Azure AI Foundry endpoint:
  https://xxxx.services.ai.azure.com/openai/v1

Environment variables:
    CV_SCORING_PROVIDER
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_DEPLOYMENT
"""

from __future__ import annotations


import os
import time

from typing import List, Optional


from dotenv import load_dotenv





# ==================================================
# Load environment variables
# ==================================================

# Current file:
# llm-service/cv-parsing/llm_client.py
#
# Load service-local and backend-local config first, then the repository-wide
# .env. Existing process environment variables keep precedence.


load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "../../backend/.env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))





# ==================================================
# Constants
# ==================================================

LEGACY_AZURE_OPENAI_API_VERSION = (
    "2024-08-01-preview"
)






# ==================================================
# Errors
# ==================================================

class LLMConfigError(EnvironmentError):

    pass





class LLMCallError(RuntimeError):

    pass






# ==================================================
# Environment helper
# ==================================================

def _get_required_env(
    name: str
) -> str:


    value = os.environ.get(name)


    if not value:


        raise LLMConfigError(

            f"Missing required environment variable '{name}'. "
            "Check llm-service/.env"

        )


    return value






# ==================================================
# Build OpenAI Client
# ==================================================

def _build_client():


    provider = os.environ.get(

        "CV_SCORING_PROVIDER",

        "azure-openai-template"

    )




    supported = [

        "azure-openai-template",

        "azure_openai"

    ]




    if provider not in supported:


        raise LLMConfigError(

            f"Unsupported CV_SCORING_PROVIDER='{provider}'"

        )






    endpoint = _get_required_env(

        "AZURE_OPENAI_ENDPOINT"

    ).rstrip("/")



    api_key = _get_required_env(

        "AZURE_OPENAI_API_KEY"

    )



    deployment = _get_required_env(

        "AZURE_OPENAI_DEPLOYMENT"

    )








    # Azure AI Foundry / OpenAI compatible endpoint

    if "/openai/v1" in endpoint:


        try:

            from openai import OpenAI


        except ImportError as e:


            raise RuntimeError(

                "Install openai package: pip install openai"

            ) from e




        client = OpenAI(

            base_url=endpoint,

            api_key=api_key

        )






    else:


        try:

            from openai import AzureOpenAI


        except ImportError as e:


            raise RuntimeError(

                "Install openai package: pip install openai"

            ) from e





        client = AzureOpenAI(

            azure_endpoint=endpoint,

            api_key=api_key,

            api_version=
            LEGACY_AZURE_OPENAI_API_VERSION

        )




    return client, deployment







# ==================================================
# Call LLM
# ==================================================

def call_llm_json(

    messages: List[dict],

    *,

    max_retries: int = 1,

    temperature: int = 1,

    max_completion_tokens: int = 2000,

    retry_backoff_seconds: float = 1.5

) -> str:



    client, deployment = _build_client()






    last_error: Optional[Exception] = None





    for attempt in range(

        max_retries + 1

    ):


        try:



            response = client.chat.completions.create(


                model=deployment,


                messages=messages,


                response_format={

                    "type":"json_object"

                },


                temperature=temperature,


                max_completion_tokens=
                    max_completion_tokens


            )





            content = (

                response

                .choices[0]

                .message

                .content

            )





            if not content:


                raise LLMCallError(

                    "Empty response from model"

                )




            return content





        except Exception as e:


            last_error = e




            if attempt < max_retries:


                time.sleep(

                    retry_backoff_seconds

                    *

                    (attempt + 1)

                )






    raise LLMCallError(

        f"LLM call failed after retries: {last_error}"

    )
