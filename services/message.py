def append_message(room_id, message, chat_sessions):
    if message.message_type == 'chat_message' or message.message_type == 'ai_message':
        chat_sessions[room_id]['chat_messages'].append({
            'timestamp': message.message_timestamp,
            'user_id': message.user_id,
            'user_name': message.user_name,
            'text': message.text,
        })
    elif message.message_type == 'human_claim_message':
        chat_sessions[room_id]['human_claim_messages'].append({
            'timestamp': message.message_timestamp,
            'user_id': message.user_id,
            'user_name': message.user_name,
            'message_type': message.message_type,
        })
        # remove the user_id from the active_ai_claims set
        # using discard wont raise an error if the user_id is not in the set
        chat_sessions[room_id]['active_ai_claims'].discard(message.user_id)
        chat_sessions[room_id]['active_human_claim'].add(message.user_id)
    
    elif message.message_type == 'ai_claim_message':
        chat_sessions[room_id]['ai_claim_messages'].append({
            'timestamp': message.message_timestamp,
            'user_id': message.user_id,
            'user_name': message.user_name,
            'message_type': message.message_type,
        })
        # add the user_id to the active_ai_claims set
        chat_sessions[room_id]['active_ai_claims'].add(message.user_id)