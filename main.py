import datetime
import random
from threading import Thread
import threading
import time
import flet as ft
from collections import deque, defaultdict
import datetime
import uuid
import json
from dotenv import load_dotenv
load_dotenv()

import instructor
from openai import AsyncClient
from models.chat import AIChatResponse, Chat, AIChatMessage
from services.ai import perform_openai_request
from services.prompt import generate_system_prompt
from services.timer import Timer
from services.assignuser import assign_user
from services.chatend import store_chat
from services.message import append_message
from services.results import update_results_display

RESULTS_JSON = "results/results.json"

# Define a message class to send messages between users
class Message:
    def __init__(self, 
                 user_id: str, 
                 user_name: str, 
                 text: str, 
                 message_type: str, 
                 room_id: str = None,
                 user_count: int = None):
        self.user_id = user_id
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.room_id = room_id
        self.user_count = user_count # to display the number of users online
        self.message_id = str(uuid.uuid4())
        self.message_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Define a chat message class to display messages in the chat
class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(message.user_name)),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name),
            ),
            ft.Column(
                [
                    ft.Text(message.user_name, weight="bold"),
                    ft.Text(message.text),
                ],
                tight=True,
                spacing=5,
            ),
        ]

    def get_initials(self, user_name: str):
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]

# Track rooms and waiting list
rooms = defaultdict(lambda: {'users': [], 'has_ai': False})
waiting_list = deque()
online_users = set()  # To track online users
user_id_to_name = {}
chat_sessions = defaultdict(lambda: {'chat_messages': [],
                                     'ai_claim_messages':[],
                                     'human_claim_messages':[],
                                     'active_ai_claims':set(),
                                     'active_human_claim':set(),
                                     'is_stored': False})
processed_messages = set()

def update_online_users(page):
    if hasattr(page, 'users_online_text') and page.route == "/":
        page.users_online_text.value = f"{len(online_users)} users online"
        page.users_online_text.update()

ai_thread = None
def chat_page(page: ft.Page, room_id: str):
    global ai_thread
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.title = f"HumanOrNot Chat - Room {room_id}"

    sys_prompt, ai_name = generate_system_prompt()
    ai_context: Chat = Chat(
        id=uuid.uuid4(),
        created_at=datetime.datetime.now(),
        system_prompt=sys_prompt,
        messages=[]
    )
    if rooms[room_id]['has_ai']:
        oai_client: AsyncClient = instructor.patch(
            AsyncClient(),
            mode=instructor.Mode.JSON
        )
        

    def send_message_click(e):
        # Send a non-empty message to the chat
        if new_message.value != "":
            page.pubsub.send_all(
                Message(
                    user_id=page.session.get("user_id"),
                    user_name=page.session.get("user_name"),
                    text=new_message.value,
                    message_type="chat_message",
                    room_id=room_id
                )
            )
            # Clear the message field and focus on it
            new_message.value = ""
            new_message.focus()
            page.update()
    
    async def on_message(message: Message):
        global ai_thread
        if isinstance(message, Message) and message.room_id == room_id:
            # actively store chat data in chat_sessions dictionary
            if message.message_id not in processed_messages:
                processed_messages.add(message.message_id)
                append_message(room_id, message, chat_sessions)

            if (
                message.message_type == "chat_message" or
                message.message_type == "ai_message"
            ):
                m = ChatMessage(message)
                ai_context.messages.append(
                    AIChatMessage(
                        id=uuid.uuid4(),
                        created_at=datetime.datetime.now(),
                        username=message.user_name if message.message_type == "chat_message" else "AI",
                        message=message.text
                    )
                )
                chat.controls.append(m)
            elif message.message_type == "login_message":
                m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
                ai_context.messages.append(
                    AIChatMessage(
                        id=uuid.uuid4(),
                        created_at=datetime.datetime.now(),
                        username="System",
                        message=m.value
                    )
                )
                chat.controls.append(m)
            elif message.message_type == "human_claim_message":
                return_to_start_click()
            elif message.message_type == "ai_claim_message":
                m = ft.Text(message.text, italic=True, color=ft.colors.RED, size=12)
                chat.controls.append(m)
                ai_claim_timer.visible = True
                ai_claim_timer.start()
                ai_context.messages.append(
                    AIChatMessage(
                        id=uuid.uuid4(),
                        created_at=datetime.datetime.now(),
                        username="System",
                        message=m.value
                    )
                )
            elif message.message_type == "end_chat":
                return_to_start_click()
                
            page.update()
            last_msg: AIChatMessage = ai_context.messages[-2] if len(ai_context.messages) >= 2 else ai_context.messages[-1]
            print(len(ai_context.messages))
            print(rooms[room_id])
            if (
                rooms[room_id]['has_ai'] and
                not message.message_type == "ai_message" and
                (
                    True or #datetime.datetime.now() - last_msg.created_at > datetime.timedelta(milliseconds=2000) or
                    len(ai_context.messages) == 1
                )
            ):
                print("PERFORMING AI REQUEST")
                response: AIChatResponse = await perform_openai_request(
                    client=oai_client,
                    chat=ai_context
                )
                print("RESPONSE")
                print(response)   
                # Check if the thread is already running
                if ai_thread is not None:
                    if ai_thread.is_alive():
                        # If it is, we need to stop it
                        ai_thread.cancel()  # Only works if the thread is a Timer and hasn't started yet
                        # ai_thread.join()  # Ensure the thread has finished running
                # send response after certain amount of time
                ai_thread = threading.Timer(
                    len(response.message)/9,
                    ai_response,
                    args=(response,)
                )
                ai_thread.start()
                
    def ai_response(response):
        if response.is_response_required:
            page.pubsub.send_all(
                Message(
                    user_id='GPT3.5',
                    user_name=ai_name,
                    text=response.message,
                    message_type="ai_message",
                    room_id=room_id
                )
            )

    def on_ai_claim(e):
        page.pubsub.send_all(
            Message(
                user_id=page.session.get("user_id"),
                user_name=page.session.get("user_name"),
                text=f"{page.session.get('user_name')} raised the claim AI",
                message_type="ai_claim_message",
                room_id=room_id
            )
        )
        page.update()

    def on_human_claim(e):
        page.pubsub.send_all(
            Message(
                user_id=page.session.get("user_id"),
                user_name=page.session.get("user_name"),
                text=f"{page.session.get('user_name')} raised the claim HUMAN",
                message_type="human_claim_message",
                room_id=room_id
            )
        )
        page.update()

    page.pubsub.subscribe(on_message)

    # Function to return to the start page
    def return_to_start_click(e=None):
        # Erase the user_name when returning to the start page
        # try:
        #     page.session.remove("user_id")
        # except KeyError as e:
        #     pass
        page.go("/")

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    ## claim row
    claims = ft.Row(
        [
            ft.ElevatedButton(text="Vote AI", on_click=on_ai_claim, height=50, width=150),
            ft.ElevatedButton(text="Vote Human", on_click=on_human_claim, height=50, width=150)
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    claims.controls[0].disabled = True
    claims.controls[1].disabled = True
    claims.controls[0].opacity = 50
    claims.controls[1].opacity = 50

    ### Timer setup
    def show_claims_callback():
        claims.controls[0].disabled = False
        claims.controls[1].disabled = False
        claims.controls[0].opacity = 100
        claims.controls[1].opacity = 100
        page.update()

    def end_game_after_ai_countdown_ends():
        if not chat_sessions[room_id]['is_stored']:
            chat_sessions[room_id]['is_stored'] = True
            store_chat(room_id, chat_sessions, rooms)
        # TODO: ask Severin if this served another purpose
        page.pubsub.send_all(
            Message(
                user_id=page.session.get("user_id"),
                user_name=page.session.get("user_name"),
                text="",
                message_type="end_chat",
                room_id=room_id
            )
        )
        page.update()


    ai_claim_timer = Timer(name="AI Callback Timer", duration=10, callback=end_game_after_ai_countdown_ends)
    ai_claim_timer.visible = False
    claims_visible_timer = Timer(name="Claims Visible Timer", duration=7, callback=show_claims_callback)
    claims_visible_timer.visible = False

    # New message entry form
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    # Add everything to the chat page
    page.add(
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,
        ),
        ft.Row(
            [
                ai_claim_timer, claims_visible_timer
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        ft.Row(
            [
                new_message,
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Send message",
                    on_click=send_message_click,
                ),
            ]
        ),
        claims,
        ft.ElevatedButton(text="Return to Start", on_click=return_to_start_click)  # Add button to return to start
    )
    claims_visible_timer.start()

def start_page(page: ft.Page):
    page.title = "HumanOrNot"

    results_label = ft.Text("", size=16, weight="bold")

    def join_chat_click(e):
        # User name is required to join the chat
        if not join_user_name.value:
            join_user_name.error_text = "Name cannot be blank!"
            join_user_name.update()
        elif len(online_users) < 2:
            join_user_name.error_text = "At least 2 users must be online to start a chat."
            join_user_name.update()
        else:
            user_name = join_user_name.value
            user_id = page.session.get("user_id")
            # Add user to waiting list
            waiting_list.append((user_id, user_name))
            print(waiting_list)
            page.session.set("user_name", user_name)
            page.session.set("user_id", user_id)
            join_chat_button.text = "Loading..."
            join_chat_button.disabled = True
            join_chat_button.update()
            # Check and pair users
            if len(waiting_list) >= 2:
                # add assign_user function below
                assign_user(page, Message, rooms, waiting_list, user_id_to_name)

    # User name entry field
    join_user_name = ft.TextField(
        label="Enter your name to join the chat",
        autofocus=True,
        on_submit=join_chat_click,
    )
    # Display the number of users online
    page.users_online_text = ft.Text(f"{len(online_users)} users online", size=16, weight="bold")

    # Start chat button with loading functionality
    join_chat_button = ft.ElevatedButton(text="Start Chat", on_click=join_chat_click)
    
    def on_message(message: Message):
        if message.message_type == "join_chat":
            if page.session.get("user_id") in [message.user_id, message.user_id]:
                page.go(f"/chat/{message.room_id}")
        elif message.message_type == "update_online_users":
            update_online_users(page)
    page.pubsub.subscribe(on_message)

    # Add everything to the start page
    page.add(
        ft.Column(
            [
                ft.Text("Welcome to HumanOrNot!", size=20, weight="bold"),
                join_user_name,
                join_chat_button,
                page.users_online_text,
                results_label
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    update_results_display(results_label)
    

def main(page: ft.Page):
    def route_change(e):
        page.controls.clear()  # Clear the current page content
        user_id = page.session.get("user_id")
        if user_id is None:
            user_id = str(uuid.uuid4())  # Generate a unique user_id
            page.session.set("user_id", user_id)

        # Add the user_id to the online users set if not already added
        if user_id not in online_users:
            online_users.add(user_id)
            print(f"User {user_id} connected")

        page.pubsub.send_all(
            Message(
                user_id=user_id,
                user_name="",  # User name not needed for online user count
                text="",
                message_type="update_online_users",
                room_id=None,
                user_count=len(online_users)
            )
        )  # Trigger update
        print(online_users)

        # Route handling
        if e.route.startswith("/chat/"):
            print("ENTERED ROUTE CHANGE CHAT PAGE")
            room_id = e.route.split("/chat/")[1]
            chat_page(page, room_id)
        else:
            start_page(page)
        page.update()

    # Handle user disconnection
    def on_disconnect(e):
        user_id = page.session.get("user_id")
        # Remove the user_id from the online users list
        if user_id and user_id in online_users:
            online_users.remove(user_id)
            page.pubsub.send_all(
                Message(
                    user_id=user_id,
                    user_name="",  # User name not needed for online user count
                    text="",
                    message_type="update_online_users",
                    room_id=None,
                    user_count=len(online_users)
                )
            )  # Trigger update
            print(f"User {user_id} disconnected")  # Add debug statement
            # print(online_users)
        page.update()

    page.on_route_change = route_change
    page.on_disconnect = on_disconnect
    # page.pubsub.subscribe(lambda msg: update_online_users(page))
    page.go(page.route)

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
