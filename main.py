# Importation des modules nécessaires
import flet as ft
from chat_view import MessageView
import unicodedata
import pickle
import socket
import threading
import os
from cryptage import encrypt_message, decrypt_message


# Fonction pour supprimer les accents d'une phrase
def remove_accents(phrase: str) -> str:
    """
    Supprime les accents d'une phrase.

    Args:
        phrase (str): La phrase à traiter.

    Returns:
        str: La phrase sans accents.
    """
    phrase = phrase.lower().strip()
    nfkd_form = unicodedata.normalize("NFKD", phrase)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


# Fonction principale de l'application
def main(page: ft.Page):
    """
    Fonction principale de l'application.

    Args:
        page (ft.Page): La page principale de l'application.
    """

    def receive_messages(sock):
        """
        Fonction pour recevoir des messages du serveur.

        Args:
            sock (socket.socket): Le socket de connexion au serveur.
        """
        buffer = b""
        while True:
            try:
                message = sock.recv(2048)
                if not message:
                    break
                buffer += message
                try:
                    data = buffer
                    data = decrypt_message(buffer)
                    buffer = b""
                except Exception as error:
                    continue
                else:
                    response_server(data)
                    continue
            except Exception as e:
                break

    def send_message(sock: socket.socket, message, user_matricule):
        """
        Fonction pour envoyer des messages au serveur.

        Args:
            sock (socket.socket): Le socket de connexion au serveur.
            message (str): Le message à envoyer.
            user_matricule (str): Le matricule de l'utilisateur.
        """
        try:
            data = {"sender_name": user_matricule, "data": message}
            serialized_data = pickle.dumps(data)
            serialized_encrypted_data = encrypt_message(serialized_data)
            sock.sendall(serialized_encrypted_data)
        except Exception as e:

            def reconnecter(e):
                page.close(alerte)
                page_chat.visible = False
                page_profile.visible = False
                page_login.visible = True
                page.update()

            def close_dialog(e):
                page.close(alerte)
                page.update()

            alerte = ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    "Alerte",
                    color="red",
                    weight="bold",
                ),
                content=ft.Text(
                    "Message non envoyé, Veuillez ressayer !\nSi ça persiste, veuillez vous réconnecter au serveur.",
                ),
                actions=[
                    ft.TextButton(
                        text="OK",
                        on_click=close_dialog,
                    ),
                    ft.TextButton(
                        text="Se reconnecter",
                        on_click=reconnecter,
                    ),
                ],
            )
            page.overlay.clear()
            page.overlay.append(alerte)
            page.update()
            page.open(alerte)

    def exit_event(e):
        """
        Fonction pour gérer l'événement de sortie de l'application.

        Args:
            e (ft.Event): L'événement de sortie.
        """
        if e.data == "detach" and page.platform == ft.PagePlatform.ANDROID:
            os._exit(1)

    def shrink(e):
        """
        Fonction pour réduire la taille de la fenêtre de chat.

        Args:
            e (ft.Event): L'événement de réduction.
        """
        page_chat.scale = ft.Scale(scale=0.35, alignment=ft.alignment.bottom_right)
        page_chat.opacity = 0.4
        page_chat.disabled = True
        page_chat.update()

    def change_chat_room(e):
        """
        Fonction pour changer de salle de chat.

        Args:
            e (ft.Event): L'événement de changement de salle.
        """
        global client_sock
        chat_room_title.value = e.control.text
        send_message(
            client_sock,
            {"type_message": "get_messages", "room_name": e.control.data},
            global_user_matricule,
        )
        restore(None)
        page.update()

    def on_login(e):
        """
        Fonction pour gérer la connexion de l'utilisateur.

        Args:
            e (ft.Event): L'événement de connexion.
        """
        global global_user_matricule
        matricule = txt_field_matricule.value

        if matricule:
            global_user_matricule = matricule
            page.run_thread(connexion_server, matricule)

    def connexion_server(matricule):
        """
        Fonction pour se connecter au serveur.

        Args:
            matricule (str): Le matricule de l'utilisateur.
        """
        global client_sock
        progress_bar_connexion_server.visible = True
        progress_bar_connexion_server.update()

        try:
            # Connexion au serveur
            server_address = (txt_field_address_server.value.strip(), 20002)
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(server_address)

            # Démarrer un thread pour recevoir des messages du serveur
            threading.Thread(
                target=receive_messages, args=(client_sock,), daemon=True
            ).start()

        except Exception as e:
            txt_field_matricule.error_text = "Connexion impossible. Veuillez ressayer !"
            txt_field_matricule.update()
        else:
            txt_field_matricule.error_text = ""
            send_message(
                client_sock,
                {
                    "type_message": "login",
                    "user_matricule": matricule,
                },
                matricule,
            )
            txt_field_matricule.update()
        finally:
            progress_bar_connexion_server.visible = False
            progress_bar_connexion_server.update()

    def response_server(data):
        """
        Fonction pour traiter les réponses du serveur.

        Args:
            data (dict): Les données reçues du serveur.
        """
        global global_user_name, chat_view, body_chat_view, global_user_matricule, client_sock

        data = data["data"]
        keys_data = data.keys()
        if "login" in keys_data:
            if data["login"] != "null":
                global_user_name = data["login"]
                send_message(
                    client_sock,
                    {"type_message": "get_messages", "room_name": "entre nous"},
                    global_user_matricule,
                )
                page_profile.content.controls[1].controls[
                    1
                ].value = global_user_name.capitalize()
            else:
                client_sock.close()
        elif "messages" in keys_data:
            chat_view = MessageView(
                user_name=global_user_name,
                on_send_message=on_send_new_message,
                page=page,
            )
            if data["messages"] != "null":
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
                page.update()

    def on_send_new_message(message: dict):
        """
        Fonction pour envoyer un nouveau message.

        Args:
            message (dict): Le message à envoyer.
        """
        global client_sock, global_user_matricule
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
        """
        Fonction pour créer un bouton de salle de chat.

        Args:
            text (str): Le texte du bouton.
            data (str): Les données associées au bouton.

        Returns:
            ft.ElevatedButton: Le bouton de salle de chat.
        """
        return ft.ElevatedButton(
            text=text,
            bgcolor="blue",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(50)),
            data=data,
            on_click=change_chat_room,
            width=170,
        )

    def progress_bar(text: str):
        """
        Fonction pour créer une barre de progression.

        Args:
            text (str): Le texte associé à la barre de progression.

        Returns:
            ft.Column: La colonne contenant la barre de progression.
        """
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
        """
        Fonction pour restaurer la taille de la fenêtre de chat.

        Args:
            e (ft.Event): L'événement de restauration.
        """
        page_chat.scale = ft.Scale(scale=1, alignment=ft.alignment.bottom_right)
        page_chat.margin = 0
        page_chat.opacity = 1
        page_chat.disabled = False
        page_chat.update()

    def se_deconnecter(e):
        """
        Fonction pour déconnecter l'utilisateur.

        Args:
            e (ft.Event): L'événement de déconnexion.
        """
        page_chat.visible = False
        page_profile.visible = False
        page_login.visible = True
        restore(None)
        page.update()

    # Configuration de la page principale
    page.title = "Entre Nous - Chat App"
    if page.platform == ft.PagePlatform.WINDOWS:
        page.window.center()
        page.window.icon = "assets/icon.png"
        page.window.width = 400
        page.window.height = 700

    # Variables globales et contrôles
    global_user_name = "User"  # Nom d'utilisateur global
    body_chat_view = ft.Container()  # Contenu global pour la vue de chat
    client_sock = None  # Socket client global
    chat_view = None  # Vue de chat globale
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

    # Conteneur de la page de connexion
    page_login = ft.Container(
        gradient=ft.LinearGradient(
            colors=[ft.colors.BLACK, ft.colors.BLUE_900, ft.colors.BLUE],
            begin=ft.alignment.bottom_center,
            end=ft.alignment.top_center,
        ),
        padding=10,
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
                    vertical_alignment="center",
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
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(2),
                                text_style=ft.TextStyle(size=18),
                            ),
                            bgcolor="blue",
                            color="white",
                            elevation=10,
                            on_click=on_login,
                            height=50,
                        ),
                    ],
                    expand=3,
                ),
                ft.Text("© Victoire & Pascal", size=10, color="white"),
            ],
        ),
    )

    # Conteneur de la page de profil
    page_profile = ft.Container(
        bgcolor=ft.colors.BLUE_900,
        padding=15,
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
                            spacing=4,
                            controls=[
                                btn_chat_room("Entre Nous", "entre nous"),
                                btn_chat_room("Club Informatique", "club informatique"),
                                btn_chat_room("Club Mécanique", "club mecanique"),
                                btn_chat_room("Club Electricité", "club electricite"),
                                btn_chat_room("Club Anglais", "club anglais"),
                                ft.ElevatedButton(
                                    text="Deconnexion",
                                    bgcolor="red",
                                    color="white",
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(50)
                                    ),
                                    on_click=se_deconnecter,
                                    width=170,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )

    # Conteneur de la page de chat
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
                        ft.IconButton(
                            icon=ft.icons.NOTIFICATIONS,
                            icon_color="white",
                            disabled=True,
                        ),
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

    # Conteneur principal de l'application
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

    # Ajout du conteneur principal à la page
    page.add(home)
    page.on_app_lifecycle_state_change = exit_event
    page.padding = ft.padding.all(0)
    page.update()


# Démarrage de l'application
ft.app(target=main)
