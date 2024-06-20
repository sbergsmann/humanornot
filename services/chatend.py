from datetime import datetime
import json
import os

CHAT_DATA_FOLDER = 'chat_data'
RESULTS_JSON = 'results/results.json'

os.makedirs(CHAT_DATA_FOLDER, exist_ok=True)

def store_chat(room_id, chat_sessions, rooms):
    try:
        chat_messages = chat_sessions.get(room_id, {
            'chat_messages': [],
            'ai_claim_messages': [],
            'human_claim_messages': [],
            'active_ai_claims': set(),
            'active_human_claim': set()
        })

        room_data = rooms[room_id]

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
                'active_ai_claims': list(chat_messages['active_ai_claims']),
                'active_human_claim': list(chat_messages['active_human_claim']),
                'room_data': room_data,
            }
            
            # store chat data in a json file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f'{CHAT_DATA_FOLDER}/{room_id}_{timestamp}.json'
            with open(file_path, 'w') as f:
                json.dump(chat_data, f, default=str)
            print(f"Chat data from room {room_id} stored in {file_path}")
            store_results(room_data, 
                          chat_messages['active_ai_claims'], 
                          chat_messages['active_human_claim'])
    except Exception as e:
        print(f"Failed to store chat data for room {room_id}: {e}")

def store_results(room_data, active_ai_claims, active_human_claim):
    correctly_identified_ai = 0 # number of times a human correctly identified an AI
    incorrectly_identified_ai = 0 # number of times a human incorrectly identified an AI as a human
    correctly_identified_human = 0 # number of times any user correctly identified a human
    incorrectly_identified_human = 0 # number of times any user incorrectly identified a human as an AI
    
    users = room_data['users']
    has_ai = room_data['has_ai']

    if len(users) == 2: # both humans
        correctly_identified_human += len(active_human_claim)
        incorrectly_identified_human += len(active_ai_claims)
    elif has_ai: # one human, one AI
        # human vote
        if users[0] in active_ai_claims:
            print(len(active_ai_claims))
            correctly_identified_ai += 1
        elif users[0] in active_human_claim:
            incorrectly_identified_ai += 1
        # AI vote, assuming it can only make a human claim when the user is not behaving properly
        if len(active_human_claim) == 1 and users[0] not in active_human_claim:
            correctly_identified_human += 1

    # update results in results.json
    with open(RESULTS_JSON, 'r') as f:
        data = json.load(f)
    
    data['results']['correctly_identified_AI'] += correctly_identified_ai
    data['results']['incorrectly_identified_AI'] += incorrectly_identified_ai
    data['results']['correctly_identified_human'] += correctly_identified_human
    data['results']['incorrectly_identified_human'] += incorrectly_identified_human
    data['results']['total_games'] += 1 # increment total games

    with open(RESULTS_JSON, 'w') as f:
        json.dump(data, f, indent=4)