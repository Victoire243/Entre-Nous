import flet as ft


# Classe représentant un message
class Message:
    """
    Classe représentant un message.
    Attributs:
        user_name (str): Nom de l'utilisateur.
        text (str): Texte du message.
        message_type (str): Type de message.
        message_id (int): Identifiant du message.
        is_owner (bool): Indique si l'utilisateur est le propriétaire du message.
    """

    def __init__(
        self,
        user_name: str,
        text: str,
        message_type: str,
        message_id: int,
        is_owner: bool,
    ):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.message_id = message_id
        self.is_owner = is_owner


# Classe représentant un message de connexion
class MessageJoin(ft.Row):
    """
    Classe représentant un message de connexion.
    """

    def __init__(self, user_name: str):
        """
        Initialise une nouvelle instance de MessageJoin.
        Args:
            user_name (str): Nom de l'utilisateur.
        """
        super().__init__()
        self.controls = [
            ft.Text(
                f"{user_name} a rejoint le salon",
                color="#6D6D6D",
                size=12,
                text_align=ft.TextAlign.CENTER,
            )
        ]
        self.alignment = ft.MainAxisAlignment.CENTER


# Classe représentant un message de chat
class ChatMessage(ft.Row):
    """
    Représente un message de chat dans une interface utilisateur.
    Attributs:
        vertical_alignment (ft.CrossAxisAlignment): Alignement vertical des éléments de la ligne.
        alignment (MainAxisAlignment): Alignement horizontal des éléments de la ligne, dépend de si le message appartient à l'utilisateur ou non.
        bg_color (str): Couleur de fond du message, dépend de si le message appartient à l'utilisateur ou non.
        controls (list): Liste des contrôles UI à afficher dans le message, dépend du type de message.
    Méthodes:
        __init__(message: Message): Initialise une nouvelle instance de ChatMessage avec les informations du message donné.
        get_initials(user_name: str) -> str: Retourne les initiales du nom d'utilisateur.
        get_avatar_color(user_name: str) -> str: Retourne une couleur d'avatar basée sur le nom d'utilisateur.
    """

    def __init__(self, message: Message):
        """
        Initialise une nouvelle instance de la vue de chat.
        Args:
            message (Message): L'objet message contenant les détails du message de chat.
        """
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.alignment = (
            ft.MainAxisAlignment.START
            if not message.is_owner
            else ft.MainAxisAlignment.END
        )
        self.bg_color = "#2B3D4E" if not message.is_owner else "#00A7D1"

        # Définition des contrôles UI en fonction du type de message
        self.controls = (
            [
                ft.CircleAvatar(
                    content=ft.Text(self.get_initials(message.user_name)),
                    color=ft.colors.WHITE,
                    bgcolor=self.get_avatar_color(message.user_name),
                    visible=True if not message.is_owner else False,
                ),
                ft.Column(
                    [
                        ft.Text(
                            message.user_name,
                            weight="bold",
                            color=self.get_avatar_color(message.user_name),
                            visible=True if not message.is_owner else False,
                        ),
                        ft.Container(
                            bgcolor=self.bg_color,
                            content=ft.Text(
                                message.text,
                                selectable=True,
                                overflow=ft.TextOverflow.VISIBLE,
                                color="white",
                                width=210,
                                height=(
                                    220
                                    if len(message.text) >= 250
                                    else ft.OptionalNumber
                                ),
                            ),
                            expand=True,
                            padding=ft.padding.all(10),
                            border_radius=(
                                ft.border_radius.only(
                                    top_left=0,
                                    top_right=15,
                                    bottom_left=15,
                                    bottom_right=15,
                                )
                                if not message.is_owner
                                else ft.border_radius.only(
                                    top_left=15,
                                    top_right=0,
                                    bottom_left=15,
                                    bottom_right=15,
                                )
                            ),
                        ),
                    ],
                    tight=True,
                    spacing=0,
                ),
            ]
            if message.message_type == "chat_message"
            else [MessageJoin(message.user_name)]
        )

    def get_initials(self, user_name: str):
        """
        Retourne les initiales du nom d'utilisateur.
        Args:
            user_name (str): Nom de l'utilisateur.
        Returns:
            str: Initiales du nom d'utilisateur.
        """
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"  # ou toute autre valeur par défaut

    def get_avatar_color(self, user_name: str):
        """
        Retourne une couleur d'avatar basée sur le nom d'utilisateur.
        Args:
            user_name (str): Nom de l'utilisateur.
        Returns:
            str: Couleur de l'avatar.
        """
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


# Classe représentant la vue de message
class MessageView(ft.SafeArea):
    """
    Classe représentant la vue de message.
    """

    def __init__(
        self,
        user_name: str,
        content=ft.Column(),
        message_type: str = "chat_message",
        isOwner: bool = True,
        message_id: int = 0,
        on_send_message=None,
    ):
        """
        Initialise une nouvelle instance de MessageView.
        Args:
            user_name (str): Nom de l'utilisateur.
            content (Column): Contenu de la vue.
        """
        super().__init__(content=content)
        self.user_name = user_name
        self.message_type = message_type
        self.isOwner = isOwner
        self.message_id = message_id
        self.message_sent = dict()
        self.expand = True
        self.on_send_message = on_send_message

        # Liste des messages de chat
        self.chat = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True,
        )
        # Formulaire de saisie d'un nouveau message
        self.new_message = ft.TextField(
            hint_text="Ecrire un message...",
            label="Votre message",
            shift_enter=True,
            autofocus=True,
            min_lines=1,
            max_lines=5,
            filled=True,
            expand=True,
            on_submit=self.send_message_click,
        )
        self.content = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    content=self.chat,
                    padding=10,
                    expand=True,
                ),
                ft.Row(
                    [
                        self.new_message,
                        ft.IconButton(
                            icon=ft.icons.SEND_ROUNDED,
                            tooltip="Envoyer le message",
                            on_click=self.send_message_click,
                        ),
                    ]
                ),
            ],
        )

    def add_message(self, message: dict):
        """message = ChatMessage(
            Message(
                user_name=message["user_name"],
                text=message["text"],
                message_type=message["type_message"],
                is_owner=message["is_owner"]
            )
        )"""
        message = ChatMessage(
            Message(
                user_name=message["user_name"],
                text=message["text"],
                message_type=message["type_message"],
                is_owner=message["is_owner"],
                message_id=message["user_name"],
            )
        )
        self.chat.controls.append(message)
        self.new_message.value = ""
        # Message envoyé est stocké dans self.message_sent
        self.message_sent = {
            "message": self.new_message.value,
            "user_name": self.user_name,
        }

    def send_message_click(self, e):
        """
        Méthode pour envoyer un message.
        Args:
            e: Événement déclenché lors de l'envoi du message.
        """
        if self.new_message.value != "":
            message = ChatMessage(
                Message(
                    self.user_name,
                    self.new_message.value,
                    self.message_type,
                    self.message_id,
                    self.isOwner,
                )
            )
            self.chat.controls.append(message)

            # Message envoyé est stocké dans self.message_sent
            self.message_sent = {
                "message": self.new_message.value,
                "user_name": self.user_name,
            }
            self.on_send_message(self.message_sent)
            self.new_message.value = ""
            self.update()
