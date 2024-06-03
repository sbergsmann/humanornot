import json
import os
import sys

import instructor
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from typing import Any, Dict
from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion

from models.chat import AIChatResponse, Chat


async def perform_openai_request(
    client: AsyncOpenAI,
    chat: Chat
) -> AIChatResponse:
    """"""
    
    response: AIChatResponse = await client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
                "role": "system",
                "content": chat.system_prompt
            },
            {
                "role": "user",
                "content": chat.format()
            }      
        ],
        temperature=.1,
        response_model=AIChatResponse  
    )
    return response