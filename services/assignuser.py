import random

def assign_user(page, Message, rooms, waiting_list):
    """Assign a human user to a room with another human user or an AI user.
    Assumes that there are already 2 users in the waiting list."""
    # add user to waiting list
    if random.choice([False, False]): # 50/50 chance
        # assign to AI
        user_id, user_name = waiting_list.popleft()
        room_id = str(len(rooms)+1)
        rooms[room_id] = {"users": [user_name], "has_ai": True}
        # notify the user they are paired to a room
        page.pubsub.send_all(
            Message(
                user_id=user_id,
                user_name=user_name,
                text=f"{user_name}, you have been assigned to room {room_id}.",
                message_type="join_chat",
                room_id=room_id
            )
        )
    else:
        # assign to human user
        user1_id, user1_name = waiting_list.popleft()
        user2_id, user2_name = waiting_list.popleft()
        room_id = str(len(rooms)+1)
        rooms[room_id] = {"users": [user1_name, user2_name], "has_ai": False}
        # notify the users that they have been assigned to a room
        page.pubsub.send_all(
            Message(
                user_id=user1_id,
                user_name=user1_name,
                text=f"{user1_name}, you have been assigned to room {room_id}.",
                message_type="join_chat",
                room_id=room_id
            )
        )
        page.pubsub.send_all(
            Message(
                user_id=user2_id,
                user_name=user2_name,
                text=f"{user2_name}, you have been assigned to room {room_id}.",
                message_type="join_chat",
                room_id=room_id
            )
        )
