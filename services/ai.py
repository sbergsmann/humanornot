from openai import AsyncClient

from services.chat import AIChatResponse, Chat


async def perform_openai_request(
    client: AsyncClient,
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
        temperature=.0,
        response_model=AIChatResponse  
    )
    return response