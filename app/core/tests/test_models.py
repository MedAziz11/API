from django.test import TestCase

from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """test creating a new user with an email is succesful """
        email = "test@test.com"
        password = "testtest"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'testtest')

    def test_create_new_super_user(self):
        """Tests the creation of a super user """
        user = get_user_model().objects.create_superuser(
            "test@gmail.com",
            "testest"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
