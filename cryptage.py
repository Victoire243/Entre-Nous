from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import pickle

# Clé partagée entre le client et le serveur
__key = b"&ntre@!9"


def encrypt_message(message, key=__key):
    """
    Chiffre un message avec l'algorithme DES en mode CBC.

    Args:
        message (bytes): Le message à chiffrer.
        key (bytes): La clé de chiffrement (par défaut __key).

    Returns:
        bytes: Le message chiffré, précédé de l'IV.
    """
    # Génère un IV aléatoire pour chaque message
    iv = get_random_bytes(8)
    # Crée un objet de chiffrement DES en mode CBC avec la clé et l'IV
    cipher = DES.new(key, DES.MODE_CBC, iv)
    # Chiffre le message après l'avoir rempli pour qu'il soit un multiple de la taille du bloc
    ciphertext = cipher.encrypt(pad(message, DES.block_size))
    # Retourne l'IV concaténé avec le texte chiffré
    return iv + ciphertext


def decrypt_message(encrypted_message, key=__key):
    """
    Déchiffre un message chiffré avec l'algorithme DES en mode CBC.

    Args:
        encrypted_message (bytes): Le message chiffré à déchiffrer.
        key (bytes): La clé de déchiffrement (par défaut __key).

    Returns:
        object: Le message déchiffré et désérialisé.
    """
    # Extrait l'IV du début du message chiffré
    iv = encrypted_message[:8]
    # Extrait le texte chiffré après l'IV
    ciphertext = encrypted_message[8:]
    # Crée un objet de déchiffrement DES en mode CBC avec la clé et l'IV
    cipher = DES.new(key, DES.MODE_CBC, iv)
    # Déchiffre le texte chiffré et le dépade
    decrypted_message = unpad(cipher.decrypt(ciphertext), DES.block_size)
    # Désérialise le message déchiffré
    decrypted_message = pickle.loads(decrypted_message)
    return decrypted_message
