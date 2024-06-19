from datetime import datetime
import json
import os

CHAT_DATA_FOLDER = 'chat_data'
os.makedirs(CHAT_DATA_FOLDER, exist_ok=True)

def store_chat(room_id, chat_sessions):
    chat_messages = chat_sessions.get(room_id, {
        'chat_messages': [],
        'ai_claim_messages': [],
        'human_claim_messages': [],
        'active_ai_claims': set()
    })

    # dont save file if chat_messages is empty
    if not chat_messages['chat_messages']:
        print(f"No chat data to store for room {room_id}")
    else:
        # combine all messages with timestamps and sort
        all_messages = (
            chat_messages['chat_messages'] +
            chat_messages['ai_claim_messages'] +
            chat_messages['human_claim_messages']
        )
        all_messages.sort(key=lambda x: x['timestamp'])

        # format chat data
        chat_data = {
            'messages': all_messages,
            'active_ai_claims': list(chat_messages['active_ai_claims'])
        }
        
        # store chat data in a json file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f'{CHAT_DATA_FOLDER}/{room_id}_{timestamp}.json'
        with open(file_path, 'w') as f:
            json.dump(chat_data, f, default=str)
        print(f"Chat data from room {room_id} stored in {file_path}")

def display_results():
    pass