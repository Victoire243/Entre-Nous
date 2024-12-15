# from flet import *
import flet as ft

# from PySock import client
from chat_view import MessageView
import unicodedata
import pickle
import socket
import threading
import os

# import logging

# logging.basicConfig(level=logging.DEBUG)


def remove_accents(phrase: str) -> str:
    phrase = phrase.lower().strip()
    nfkd_form = unicodedata.normalize("NFKD", phrase)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def main(page: ft.Page):

    def receive_messages(sock):
        """Function to receive messages from the server."""
        buffer = b""
        while True:
            try:
                message = sock.recv(2048)
                # print(f"Received message: {message}")
                if not message:
                    # print("Disconnected from the server.")
                    break
                buffer += message
                try:
                    data = pickle.loads(buffer)
                    buffer = b""
                    # print(f"Received: {data}")
                except pickle.UnpicklingError:
                    continue
                else:
                    # print(f"Received: {data}")
                    response_server(data)
                    continue
            except Exception as e:
                # print(f"Error receiving message: {e}")
                break
        # print("Exiting receive_messages thread.")

    def send_message(sock, message, user_matricule):
        """Function to send messages to the server."""
        # print(f"Sending message: {message}")
        # print(f"User matricule: {user_matricule}")
        # print(f"Socket: {sock}")
        try:
            data = {"sender_name": user_matricule, "data": message}
            serialized_data = pickle.dumps(data)
            sock.sendall(serialized_data)
        except Exception as e:
            # print(f"Error sending message: {e}")
            pass
        # else:
        #     #print("Message sent.")

    def exit_event(e):
        if e.data == "detach" and page.platform == ft.PagePlatform.ANDROID:
            os._exit(1)

    def shrink(e):
        page_chat.scale = ft.Scale(scale=0.35, alignment=ft.alignment.bottom_right)
        # page_2.margin = 20
        page_chat.opacity = 0.4
        page_chat.disabled = True
        page_chat.update()

    def change_chat_room(e):
        global client_sock
        chat_room_title.value = e.control.text
        # c.SEND(
        #     channel="entre_nous",
        #     data={"type_message": "get_messages", "room_name": e.control.data},
        # )
        send_message(
            client_sock,
            {"type_message": "get_messages", "room_name": e.control.data},
            global_user_matricule,
        )
        restore(None)
        page.update()

    def on_login(e):
        global global_user_matricule
        matricule = txt_field_matricule.value

        if matricule:
            global_user_matricule = matricule
            page.run_thread(connexion_server, matricule)

    def connexion_server(matricule):
        # global global_user_matricule
        global client_sock
        progress_bar_connexion_server.visible = True
        progress_bar_connexion_server.update()
        # try:
        #     c = client(client_name=matricule, debug=True)
        #     c.CLIENT(address=txt_field_address_server.value.strip(), port=1200)
        #     c.CREATE_CHANNEL(channels="entre_nous"),
        # except Exception as error:
        #     #print(f"Erreur connexion au serveur : {error}")
        #     txt_field_matricule.error_text = "Connexion impossible. Veuillez ressayer !"
        #     txt_field_matricule.update()
        # else:
        #     txt_field_matricule.error_text = ""
        #     c.SEND(channel="entre_nous", data={"type_message": "login"})
        #     txt_field_matricule.update()
        #     try:
        #         while True:
        #             c.LISTEN(channel="entre_nous", function=response_server)
        #     except Exception as error:
        #         #print(f"Erreur écoute du serveur : {error}")
        # finally:
        #     progress_bar_connexion_server.visible = False
        #     progress_bar_connexion_server.update()

        try:
            # Connect to the server
            server_address = (txt_field_address_server.value.strip(), 20002)
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(server_address)
            # print(f"Connected to server at {server_address}")

            # Start a thread to receive messages from the server
            threading.Thread(
                target=receive_messages, args=(client_sock,), daemon=True
            ).start()

            # while True:
            #     # Get user input and send it to the server
            #     message = input("Enter message to send (or 'exit' to quit): ")
            #     serialized_data = pickle.dumps(message)
            #     if message.lower() == "exit":
            #         #print("Exiting...")
            #         break
            #     client_sock.sendall(serialized_data)

        except Exception as e:
            # print(f"Error: {e}")
            txt_field_matricule.error_text = "Connexion impossible. Veuillez ressayer !"
            txt_field_matricule.update()
        else:
            txt_field_matricule.error_text = ""
            # c.SEND(channel="entre_nous", data={"type_message": "login"})
            send_message(
                client_sock,
                {"type_message": "login", "user_matricule": matricule},
                matricule,
            )
            txt_field_matricule.update()
        finally:
            progress_bar_connexion_server.visible = False
            progress_bar_connexion_server.update()
        #     client_sock.close()
        #     #print("Connection closed.")

    def response_server(data):
        global global_user_name, chat_view, body_chat_view, global_user_matricule, client_sock
        data = data["data"]
        keys_data = data.keys()
        if "login" in keys_data:
            # print(data["login"])
            if data["login"] != "null":
                global_user_name = data["login"]
                # c.SEND(
                #     channel="entre_nous",
                #     data={"type_message": "get_messages", "room_name": "entre nous"},
                # )
                # print("preparing to send message to server. . .")
                send_message(
                    client_sock,
                    {"type_message": "get_messages", "room_name": "entre nous"},
                    global_user_matricule,
                )
                page_profile.content.controls[1].controls[
                    1
                ].value = global_user_name.capitalize()
        elif "messages" in keys_data:
            chat_view = MessageView(
                user_name=global_user_name,
                on_send_message=on_send_new_message,
                page=page,
            )
            if data["messages"] != "null":
                # #print(data["messages"])
                for msg in data["messages"]:
                    chat_view.add_message(
                        {
                            "user_name": msg[3].upper(),
                            "text": msg[1],
                            "type_message": msg[2],
                            "is_owner": (
                                True
                                if msg[3].lower() == global_user_name.lower()
                                else False
                            ),
                        }
                    )

                page_login.visible = False
                page_chat.visible = True
                page_profile.visible = True
                body_chat_view = chat_view

            else:
                body_chat_view = chat_view

            page_chat.content.controls.pop()
            page_chat.update()
            page.update()
            progress_bar_connexion_server.visible = False
            progress_bar_connexion_server.update()
            page_chat.content.update()
            page_chat.content.controls.append(body_chat_view)
            page_chat.update()
            home.update()
            page.update()

        elif "text" in keys_data:
            if chat_view:
                chat_view.add_message(
                    {
                        "user_name": data["user_name"],
                        "text": data["text"],
                        "type_message": data["type_message"],
                        "is_owner": (
                            True
                            if data["user_name"].lower() == global_user_name.lower()
                            else False
                        ),
                    }
                )
                body_chat_view = chat_view
                # page_chat.content.controls.pop()
                # progress_bar_connexion_server.visible = False
                # progress_bar_connexion_server.update()
                # page_chat.content.controls.append(body_chat_view)
                page.update()

    def on_send_new_message(message: dict):
        global client_sock, global_user_matricule
        # #print(message)
        # c.SEND(
        #     channel="entre_nous",
        #     data={
        #         "user_name": message["user_name"].lower(),
        #         "type_message": "chat_message",
        #         "room_name": remove_accents(chat_room_title.value),
        #         "message": message["message"],
        #         "user_matricule": global_user_matricule,
        #     },
        # )
        send_message(
            client_sock,
            {
                "user_name": message["user_name"].lower(),
                "type_message": "chat_message",
                "room_name": remove_accents(chat_room_title.value),
                "message": message["message"],
                "user_matricule": global_user_matricule,
            },
            global_user_matricule,
        )

    def btn_chat_room(text: str, data: str):
        return ft.ElevatedButton(
            text=text,
            bgcolor="blue",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(15)),
            data=data,
            on_click=change_chat_room,
            width=170,
        )

    def progress_bar(text: str):
        return ft.Column(
            alignment="center",
            horizontal_alignment="center",
            visible=False,
            controls=[
                ft.Text(
                    text,
                    color="green",
                    size=9,
                    text_align="center",
                ),
                ft.ProgressBar(
                    color="green",
                    bgcolor="white",
                    width=225,
                ),
            ],
        )

    def restore(e):
        page_chat.scale = ft.Scale(scale=1, alignment=ft.alignment.bottom_right)
        page_chat.margin = 0
        page_chat.opacity = 1
        page_chat.disabled = False
        page_chat.update()

    page.title = "Entre Nous - Chat App"
    if page.platform == ft.PagePlatform.WINDOWS:
        page.window.center()
        page.window.icon = "assets/chat-icon.png"
        page.window.width = 400
        page.window.height = 700
    # VARIABLES - CONTROLS
    global_user_name = "User"  # global user name
    body_chat_view = ft.Container()  # global body content for chat_view
    client_sock = None  # global client socket
    chat_view = None  # global chat_view page
    chat_room_title = ft.Text(
        value="Entre Nous", text_align="center", color="white", size=16, weight="bold"
    )
    progress_bar_connexion_server = progress_bar("Connexion au serveur...")
    txt_field_matricule = ft.TextField(
        bgcolor="white",
        color="black",
        border_color="blue",
        prefix_icon=ft.icons.LOCK,
        label="Votre Matricule",
        hint_text="Votre matricule...",
        width=225,
    )
    txt_field_address_server = ft.TextField(
        bgcolor="white",
        color="black",
        border_color="blue",
        prefix_icon=ft.icons.CLOUD,
        label="Addresse du serveur",
        hint_text="Ex : 192.168.2.3",
        width=225,
    )

    page_login = ft.Container(
        gradient=ft.LinearGradient(
            colors=[ft.colors.BLACK, ft.colors.BLUE_900, ft.colors.BLUE],
            begin=ft.alignment.bottom_center,
            end=ft.alignment.top_center,
        ),
        padding=10,
        # border_radius=20,
        expand=True,
        content=ft.Column(
            horizontal_alignment="center",
            alignment="center",
            expand=True,
            controls=[
                ft.Row(
                    [
                        ft.Text("Entre Nous", color="white", size=26, weight="bold"),
                    ],
                    alignment="center",
                    vertical_alignment="start",
                    expand=1,
                ),
                ft.Image(
                    src="assets/chat-icon.png",
                    height=200,
                    width=200,
                    fit=ft.ImageFit.CONTAIN,
                ),
                ft.Text("CONNECTEZ-VOUS", color="white", size=20),
                progress_bar_connexion_server,
                ft.Column(
                    alignment="start",
                    horizontal_alignment="center",
                    controls=[
                        txt_field_matricule,
                        txt_field_address_server,
                        ft.ElevatedButton(
                            text="Se Connecter",
                            width=225,
                            height=40,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(2)),
                            bgcolor="blue",
                            color="white",
                            elevation=10,
                            on_click=on_login,
                        ),
                    ],
                    expand=3,
                ),
            ],
        ),
    )

    page_profile = ft.Container(
        bgcolor=ft.colors.BLUE_900,
        padding=15,
        # border_radius=20,
        visible=False,
        content=ft.Column(
            spacing=90,
            expand=True,
            controls=[
                ft.IconButton(
                    icon=ft.icons.ARROW_CIRCLE_LEFT_OUTLINED,
                    icon_color="white",
                    on_click=restore,
                ),
                ft.Column(
                    horizontal_alignment="center",
                    spacing=2,
                    controls=[
                        ft.Stack(
                            controls=[
                                ft.CircleAvatar(
                                    radius=50,
                                    content=ft.Stack(
                                        controls=[
                                            ft.Container(
                                                bgcolor="white",
                                                border_radius=50,
                                                height=200,
                                                width=200,
                                            ),
                                            ft.Image(
                                                src="assets/profile.png",
                                                height=200,
                                                width=200,
                                                fit=ft.ImageFit.COVER,
                                                border_radius=50,
                                                color_blend_mode=ft.BlendMode.COLOR_DODGE,
                                            ),
                                        ]
                                    ),
                                    badge=ft.Badge(small_size=20, bgcolor="green"),
                                ),
                            ]
                        ),
                        ft.Text(global_user_name, color="white", size=18),
                        ft.Column(
                            alignment="center",
                            expand=True,
                            controls=[
                                btn_chat_room("Entre Nous", "entre nous"),
                                btn_chat_room("Club Informatique", "club informatique"),
                                btn_chat_room("Club Mécanique", "club mecanique"),
                                btn_chat_room("Club Electricité", "club electricite"),
                                btn_chat_room("Club Anglais", "club anglais"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )

    page_chat = ft.Container(
        gradient=ft.LinearGradient(
            colors=[ft.colors.BLACK, ft.colors.BLUE_900, ft.colors.BLUE],
            begin=ft.alignment.bottom_center,
            end=ft.alignment.top_center,
        ),
        padding=10,
        animate_scale=ft.animation.Animation(
            duration=500, curve=ft.AnimationCurve.DECELERATE
        ),
        animate_opacity=ft.animation.Animation(
            duration=700, curve=ft.AnimationCurve.DECELERATE
        ),
        # border_radius=20
        visible=False,
        content=ft.Column(
            horizontal_alignment="center",
            expand=True,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.MENU, icon_color="white", on_click=shrink
                        ),
                        chat_room_title,
                        ft.IconButton(icon=ft.icons.NOTIFICATIONS, icon_color="white"),
                    ],
                ),
                ft.Column(
                    expand=True,
                    alignment="center",
                    controls=[body_chat_view],
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
        ),
    )

    home = ft.SafeArea(
        content=ft.Stack(
            controls=[
                page_profile,
                page_login,
                page_chat,
            ],
            fit=ft.StackFit.EXPAND,
        ),
        expand=True,
    )

    page.add(home)
    page.on_app_lifecycle_state_change = exit_event
    page.padding = ft.padding.all(0)
    page.update()


ft.app(target=main)
