# Description: Serveur de l'application Entre Nous


import sqlite3
from hashlib import sha256
import socket
import threading
import pickle


from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


__key = b"&ntre@!9"  # clé partagée entre le client et le serveur


def encrypt_message(message, key=__key):
    iv = get_random_bytes(8)  # IV aléatoire pour chaque message
    cipher = DES.new(key, DES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(message, DES.block_size))
    print(f"encrypted message to send to client : {iv+ciphertext}")
    return iv + ciphertext  # Retourne IV + texte chiffré


def decrypt_message(encrypted_message, key=__key):
    iv = encrypted_message[:8]  # Extraire l'IV du message chiffré
    ciphertext = encrypted_message[8:]  # Extraire le texte chiffré
    cipher = DES.new(key, DES.MODE_CBC, iv)
    decrypted_message = unpad(cipher.decrypt(ciphertext), DES.block_size)
    decrypted_message = pickle.loads(decrypted_message)  # Désérialiser le message
    print(f"Decrypted Message : {decrypted_message}")
    return decrypted_message


class Data:
    def __init__(self, message: str | dict):
        self.message = message  # Initialiser le message

    def get_user_name(self):
        user_name = self.message["user_name"]
        return user_name.lower()  # Retourner le nom d'utilisateur en minuscules

    def get_message_type(self):
        return self.message[
            "type_message"
        ].lower()  # Retourner le type de message en minuscules

    def get_room_code(self):
        return self.message["room_code"]  # Retourner le code de la salle

    def get_room_name(self):
        return self.message[
            "room_name"
        ].lower()  # Retourner le nom de la salle en minuscules

    def get_message(self):
        return self.message["message"]  # Retourner le contenu du message

    def get_sender_name(self):
        return self.message["sender_name"]  # Retourner le nom de l'expéditeur

    def get_target_name(self):
        return self.message["target_name"]  # Retourner le nom du destinataire

    def user_matricule(self):
        return self.message["user_matricule"]  # Retourner le matricule de l'utilisateur

    def get_channel_name(self):
        return self.message["channel"]  # Retourner le nom du canal


class Database:
    def __init__(self, db_name: str = "entre_nous.sqlite"):
        self.connexion = sqlite3.connect(
            db_name, check_same_thread=False
        )  # Connexion à la base de données
        self.cursor = self.connexion.cursor()  # Création du curseur

    def get_room_info(self, room_name: str):
        self.cursor.execute(
            f"SELECT * FROM rooms WHERE room_name = '{room_name.lower().strip()}'"
        )
        return self.cursor.fetchall()  # Retourner les informations de la salle

    def is_room_code(self, room_name: str, room_code: str):
        self.cursor.execute(
            f"SELECT room_code FROM rooms WHERE room_name = '{room_name.lower().strip()}'"
        )
        result = self.cursor.fetchall()
        if result:
            return (
                result[0][0] == sha256(room_code.encode()).hexdigest()
            )  # Vérifier le code de la salle
        return False

    def get_messages(self):
        self.cursor.execute("SELECT * FROM messages")
        return self.cursor.fetchall()  # Retourner tous les messages

    def get_message_from_room(self, room_name: str):
        self.cursor.execute(
            f"SELECT * FROM messages WHERE message_room = '{room_name.lower().strip()}'"
        )
        return self.cursor.fetchall()  # Retourner les messages de la salle

    def get_user_name_from_matricule(self, matricule: str):
        self.cursor.execute(
            f"SELECT user_name FROM users WHERE user_matricule = '{matricule}'"
        )
        return (
            self.cursor.fetchall()
        )  # Retourner le nom d'utilisateur à partir du matricule

    def get_rooms(self):
        self.cursor.execute("SELECT room_name, room_code FROM rooms")
        return self.cursor.fetchall()  # Retourner toutes les salles

    def add_message(
        self, text: str, message_type: str, message_owner: str, message_room: str
    ):

        query = """
            INSERT INTO messages (text, message_type, message_owner, message_room) VALUES (?, ?, ?, ?);
        """
        try:
            self.cursor.execute(
                query,
                (
                    text,
                    message_type.lower(),
                    message_owner.lower().strip(),
                    message_room.lower().strip(),
                ),
            )
        except Exception as e:
            print("Erreur Base de données : ajout d'un message échoué")
            print(e)
        else:
            self.connexion.commit()  # Valider l'ajout du message

    def add_room(self, room_name: str, room_code: str):
        self.cursor.execute(
            f"INSERT INTO rooms (room_name, room_code) VALUES ('{room_name}', '{room_code}')"
        )
        self.connexion.commit()  # Valider l'ajout de la salle


data_base = Database()  # Instancier la base de données


def forward_message(message, sender_connection):
    """Function to forward the message to all connected clients except the sender."""
    data = pickle.dumps({"data": message, "sender_name": "server"})
    data = encrypt_message(data)
    print(f"Message crypté à envoyer : {data}")
    for client in clients:
        if client != sender_connection:  # Ne pas renvoyer le message à l'expéditeur
            try:
                client.sendall(data)  # Transférer le message aux autres clients
            except Exception as e:
                print(f"Failed to send message to {client}: {e}")
    print("Message envoyé à tous les clients avec succès")
    print("-------------------------")


def send_message_to_client(message, connection):
    """Function to send a message to a specific client."""

    print(f"Envoi du message à {connection}")
    data = pickle.dumps({"data": message, "sender_name": "server"})
    data = encrypt_message(data)
    print(f"Message crypté à envoyer : {data}")
    try:
        connection.sendall(data)  # Envoyer le message au client
    except Exception as e:
        print(f"Failed to send message to {connection}: {e}")
    else:
        print(f"Message envoyé à {connection} avec succès")
        print("-------------------------")


def handle_client(connection, client_address):
    """Function to handle client connection."""

    def client_msg(data, connexion):
        global data_base, connected

        sender_name = data["sender_name"]
        print(f"Message reçu de {sender_name}")

        data = Data(data["data"])  # Convertir les données en objet Data
        print("-------------------------")
        type_message = data.get_message_type().lower()  # Obtenir le type de message
        try:
            match type_message:
                case "login":
                    print("Dans le cas login")
                    user_matricule = (
                        data.user_matricule()
                    )  # Obtenir le matricule de l'utilisateur
                    print(f"Matricule : {user_matricule}")
                    user_name = data_base.get_user_name_from_matricule(
                        sender_name
                    )  # Obtenir le nom d'utilisateur
                    print(f"User Name : {user_name}")
                    user_name = (
                        {"login": user_name[0][0]} if user_name else {"login": "null"}
                    )
                    send_message_to_client(
                        message=user_name, connection=connexion
                    )  # Envoyer le nom d'utilisateur au client

                case "get_messages":
                    messages = data_base.get_message_from_room(
                        data.get_room_name()
                    )  # Obtenir les messages de la salle
                    messages = (
                        {"messages": messages} if messages else {"messages": "null"}
                    )
                    send_message_to_client(
                        message=messages, connection=connexion
                    )  # Envoyer les messages au client

                case "chat_message":
                    room_name = data.get_room_name()  # Obtenir le nom de la salle
                    message = data.get_message()  # Obtenir le contenu du message
                    message_type = data.get_message_type()  # Obtenir le type de message
                    user_name = data.get_user_name()  # Obtenir le nom d'utilisateur
                    user_matricule = (
                        data.user_matricule()
                    )  # Obtenir le matricule de l'utilisateur
                    data_base.add_message(
                        text=message,
                        message_type=message_type,
                        message_owner=user_name,
                        message_room=room_name,
                    )  # Ajouter le message à la base de données
                    forward_message(
                        message={
                            "user_name": user_name,
                            "text": message,
                            "type_message": message_type,
                        },
                        sender_connection=connexion,
                    )  # Transférer le message aux autres clients

        except Exception as e:
            print(e)

    clients.append(connection)  # Ajouter le nouveau client à la liste
    try:
        while True:
            # Receive data from client
            data = connection.recv(1024)
            if not data:
                print(f"No data from {client_address}. Closing connection.")
                break  # No more data from the client

            received_data = decrypt_message(data)
            print(f"Message crypté reçu : {data}")
            print(f"Message décrypté reçu : {received_data}")
            print(f"-------------------------")
            client_msg(received_data, connexion=connection)

    except Exception as e:
        print(f"Error with {client_address}: {e}")
    finally:
        clients.remove(
            connection
        )  # Retirer le client de la liste lors de la déconnexion
        connection.close()
        print(f"Connection with {client_address} closed.")


server_address = ("", 20002)

# Créer un socket TCP/IP
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(server_address)
server_sock.listen(5)  # Définir une file d'attente pour un maximum de 5 connexions

server_ip = socket.gethostbyname(socket.gethostname())

print(f"Le serveur est en écoute sur IP : {server_ip} et Port : {server_address[1]}")

# Liste pour suivre les clients connectés
clients = []

while True:
    connection, client_address = server_sock.accept()

    # Démarrer un nouveau thread pour chaque connexion client
    client_thread = threading.Thread(
        target=handle_client, args=(connection, client_address)
    )
    client_thread.start()
