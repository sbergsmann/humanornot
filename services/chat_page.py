import flet as ft
from collections import deque, defaultdict
import uuid

# Define a message class to send messages between users
class Message:
    def __init__(self, user_id: str, user_name: str, text: str, message_type: str, room_id: str = None):
        self.user_id = user_id
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.room_id = room_id

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
rooms = defaultdict(list)
waiting_list = deque()
online_users = set()  # To track online users

def update_online_users(page):
    if hasattr(page, 'users_online_text') and page.users_online_text in page.controls:
        page.users_online_text.value = f"{len(online_users)} users online"
        page.users_online_text.update()

def chat_page(page: ft.Page, room_id: str):
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.title = f"HumanOrNot Chat - Room {room_id}"

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

    def on_message(message: Message):
        if isinstance(message, Message) and message.room_id == room_id:
            if message.message_type == "chat_message":
                m = ChatMessage(message)
            elif message.message_type == "login_message":
                m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
            chat.controls.append(m)
            page.update()

    page.pubsub.subscribe(on_message)

    # Function to return to the start page
    def return_to_start_click(e):
        # Erase the user_name when returning to the start page
        page.session.remove("user_name")
        page.go("/")

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

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
                new_message,
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Send message",
                    on_click=send_message_click,
                ),
            ]
        ),
        ft.Row(
            [
                ft.ElevatedButton(text="Vote AI", on_click=lambda e: None, height=50, width=150),
                ft.ElevatedButton(text="Vote Human", on_click=lambda e: None, height=50, width=150)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        ft.ElevatedButton(text="Return to Start", on_click=return_to_start_click)  # Add button to return to start
    )

# Start page to join the chat
def start_page(page: ft.Page):

    def join_chat_click(e):
        # User name is required to join the chat
        if not join_user_name.value:
            join_user_name.error_text = "Name cannot be blank!"
            join_user_name.update()
        # At least 2 users must be online to start a chat
        elif len(online_users) < 2:
            join_user_name.error_text = "At least 2 users must be online to start a chat."
            join_user_name.update()
        # Join the chat
        else:
            user_name = join_user_name.value
            assigned_room = None
            # Assign the user to a room with less than 2 users
            for room_id, users in rooms.items():
                if len(users) < 2:
                    assigned_room = room_id
                    break
            # If no room is available, create a new room
            if assigned_room is None:
                assigned_room = str(len(rooms) + 1)
                rooms[assigned_room] = []
            # Add the user to the room
            rooms[assigned_room].append(user_name)
            user_id = page.session.get("user_id")  # Retrieve the user_id from the session
            page.session.set("user_name", user_name)
            page.session.set("room_id", assigned_room)
            page.pubsub.send_all(
                Message(
                    user_id=user_id,
                    user_name=user_name,
                    text=f"{user_name} has joined the chat.",
                    message_type="login_message",
                    room_id=assigned_room
                )
            )
            page.go(f"/chat/{assigned_room}")  # Redirect to the chat page

    # User name entry field
    join_user_name = ft.TextField(
        label="Enter your name to join the chat",
        autofocus=True,
        on_submit=join_chat_click,
    )
    # Display the number of users online
    page.users_online_text = ft.Text(f"{len(online_users)} users online", size=16, weight="bold")

    # Add everything to the start page
    page.add(
        ft.Column(
            [
                ft.Text("Welcome to HumanOrNot!", size=20, weight="bold"),
                join_user_name,
                ft.ElevatedButton(text="Start Chat", on_click=join_chat_click),
                page.users_online_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

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
            print(online_users)

        page.pubsub.send_all(
            Message(
                user_id=user_id,
                user_name="",  # User name not needed for online user count
                text="",
                message_type="update_online_users",
                room_id=None
            )
        )  # Trigger update

        # Route handling
        if e.route.startswith("/chat/"):
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
                    room_id=None
                )
            )  # Trigger update
            print(f"User {user_id} disconnected")  # Add debug statement
            print(online_users)
        page.update()

    page.on_route_change = route_change
    page.on_disconnect = on_disconnect
    page.pubsub.subscribe(lambda msg: update_online_users(page))
    page.go(page.route)

ft.app(target=main)
