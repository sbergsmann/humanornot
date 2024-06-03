import hashlib
import json
from logging import Logger
import logging
import os
import sys
from typing import Any, Dict
from urllib.parse import ParseResult, urlparse
from dotenv import load_dotenv, set_key
import instructor
from openai import AsyncOpenAI, BaseModel
from openai.types.chat.chat_completion import ChatCompletion

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from models.chat import AIChatResponse



class EndpointFactory:

    EXAMPLE_CHAT_HISTORY = """
    ###username: red
    ###message: hi
    ###username: green
    ###message: hey, whats up?
    ###username: red
    ###message: everything fine thanks
    """

    FALLBACK_ENDPOINT_CONFIG = {
        "ae3b202fcca81157b34f2d758a60293e2c4cce76980df1b660f781466a698bef": {
            "base_url": "https://api.openai.com/v1",
            "api_key_id": "api.openai.com",
            "model_name": "gpt-3.5-turbo-0125"
        }
    }

    def __init__(
        self,
        config_dir: str,
        config_file_name: str = "endpoint_config.json",
        dotenv_file_name: str = ".env"
    ) -> None:
        self.config_dir = config_dir
        self.config_path: str = os.path.join(self.config_dir, config_file_name)
        self.dotenv_path: str = os.path.join(self.config_dir, dotenv_file_name)

        self.logger = Logger("app.services.endpointfactory", level=logging.DEBUG)
        self._load_endpoint_config()
        self.logger.debug(f"Current User: {os.getlogin()}")


    async def validate_endpoint(
        self,
        endpoint_base_url: str,
        api_key: str,
        model_name: str
    ) -> bool:
        """Checks whether a given url meets the OpenAI API standard and is accessible.
        
        Parameters
        ----------
        endpoint_base_url: str
            The base url for the api, e.g. 'https://api.openai.com/v1'
        api_key: str
            The api key to make requests to the api
        model_name: str
            which model needs to be targeted on the endpoint

        Returns
        -------
        bool
            True, if the endpoint url meets all requirements, else False
        """
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=endpoint_base_url
        )
        
        # 1. Check if the URL is valid
        try:
            parsed_url: ParseResult = urlparse(endpoint_base_url)
            if not all([parsed_url.scheme, parsed_url.netloc, parsed_url.path]):
                self.logger.info("Invalid URL format.")
                return False
        except Exception as e:
            self.logger.exception(f"Error parsing URL: {e}")
            return False

        try:
            response: ChatCompletion = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant."
                    },
                    {
                        "role": "user",
                        "content": "Why is the sky blue?"
                    }
                ],
                max_tokens=3
            )

            # Check if the response contains the expected structure
            if isinstance(response.choices, list):
                if len(response.choices) < 1:
                    self.logger.info("Endpoint response has no content.")
                    return False
            else:
                self.logger.info("Invalid response structure.")
                return False

        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")
            return False
        
        try:        
            wrapped_client: AsyncOpenAI = instructor.patch(
                client, mode=instructor.Mode.JSON
            )
            response: AIChatResponse = await wrapped_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI agent that mimics a human and does not expose itself to be an AI. Your Player name is 'blue' and you adapt your talking style to that of the chat room."
                    },
                    {
                        "role": "user",
                        "content": f"You are given the following chat history. Reply accordingly. {self.EXAMPLE_CHAT_HISTORY}"
                    }
                ],
                response_model=AIChatResponse
            )
            self.logger.info(response)
        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")
            return False
        
        config = {
            "base_url": endpoint_base_url,
            "api_key_id": parsed_url.netloc,
            "model_name": model_name
        }
        config_id: str = self.generate_hash(config)
        try:
            self._add_api_key_to_env(api_key=api_key, key_name=parsed_url.netloc)
        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")

        self.endpoint_config = self._update_endpoint_config(config_id, config)
        return True
    
    @staticmethod
    def generate_hash(model: Dict[str, str]) -> str:
        # Serialize the model to a JSON string
        model_json: str = json.dumps(model)
        
        # Create a hash object
        hash_object: hashlib._Hash = hashlib.sha256()
        
        # Update the hash object with the bytes of the JSON string
        hash_object.update(model_json.encode('utf-8'))
        
        # Return the hexadecimal representation of the hash
        return hash_object.hexdigest()
    
    def _add_api_key_to_env(self, api_key: str, key_name: str) -> None:
        """Add or update the API key in the .env file."""
                
        # Load the .env file
        load_dotenv(self.dotenv_path)
        
        # Add or update the API key
        set_key(self.dotenv_path, key_name, api_key)
        self.logger.info(f"{key_name} added/updated successfully in {self.dotenv_path}.")


    def _update_endpoint_config(self, config_id: str, config: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """"""
        stored_config: Dict[str, Dict[str, str]] = {}
        with open(self.config_path, "r") as fh:
            stored_config: Dict[str, str] = json.load(fh)

        if config_id not in stored_config.keys():
            stored_config[config_id] = config
            self.logger.info(f"New config {config_id} successfully added")
        else:
            self.logger.info(f"New config {config_id} was not added because the hash already exists")
        
        with open(self.config_path, "w") as fh:
            json.dump(stored_config, fh)
            
        return stored_config


    def _load_endpoint_config(self) -> Dict[str, Dict[str, str]]:
        """Load Endpoint configs from a JSON file."""
        self.endpoint_config: Dict[str, Dict[str, str]] = {}
        if not os.path.exists(self.config_path):
            os.mkdir(self.config_dir)
            with open(self.config_path, "w") as fh:
                json.dump(self.FALLBACK_ENDPOINT_CONFIG, fh)
            self.logger.debug(f"File created: {self.config_path}")
            self.endpoint_config = self.FALLBACK_ENDPOINT_CONFIG
        else:
            try:
                with open(self.config_path, "r") as fh:
                    self.endpoint_config: Dict[str, Dict[str, str]] = json.load(fh)
            except Exception as e:
                self.logger.exception(f"Error loading endpoint configuration: {e}")

                # fallback
                self.logger.debug("Activating OpenAI fallback")
                self.endpoint_config = self.FALLBACK_ENDPOINT_CONFIG



if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(
        format='%(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )

    endpoint_base_url = "https://api.openai.com/v1"
    api_key: str = os.environ.get("OPENAI_API_KEY")
    model_name = "gpt-3.5-turbo-0125"

    endpoint_factory = EndpointFactory("data")

    is_success: bool = asyncio.run(
        endpoint_factory.validate_endpoint(
            endpoint_base_url=endpoint_base_url,
            api_key=api_key,
            model_name=model_name
        )
    )

    print(is_success)