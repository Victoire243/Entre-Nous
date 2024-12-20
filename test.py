import unittest
from cryptage import encrypt_message, decrypt_message
import pickle


class TestCryptage(unittest.TestCase):
    """Classe de test pour les fonctions de cryptage et décryptage."""

    def test_encrypt_decrypt_message(self):
        """Test de cryptage et décryptage d'un message standard."""
        original_message = {"sender_name": "test_user", "data": "Hello, World!"}
        serialized_message = pickle.dumps(original_message)

        encrypted_message = encrypt_message(serialized_message)
        decrypted_message = decrypt_message(encrypted_message)

        self.assertEqual(original_message, decrypted_message)

    def test_encrypt_decrypt_empty_message(self):
        """Test de cryptage et décryptage d'un message vide."""
        original_message = {}
        serialized_message = pickle.dumps(original_message)

        encrypted_message = encrypt_message(serialized_message)
        decrypted_message = decrypt_message(encrypted_message)

        self.assertEqual(original_message, decrypted_message)

    def test_encrypt_decrypt_large_message(self):
        """Test de cryptage et décryptage d'un message volumineux."""
        original_message = {"sender_name": "test_user", "data": "A" * 1000}
        serialized_message = pickle.dumps(original_message)

        encrypted_message = encrypt_message(serialized_message)
        decrypted_message = decrypt_message(encrypted_message)

        self.assertEqual(original_message, decrypted_message)

    def test_encrypt_decrypt_special_characters(self):
        """Test de cryptage et décryptage d'un message avec des caractères spéciaux."""
        original_message = {
            "sender_name": "test_user",
            "data": "Hello, World! @#$%^&*()",
        }
        serialized_message = pickle.dumps(original_message)

        encrypted_message = encrypt_message(serialized_message)
        decrypted_message = decrypt_message(encrypted_message)

        self.assertEqual(original_message, decrypted_message)


if __name__ == "__main__":
    unittest.main()
