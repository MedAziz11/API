from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UserApiTests(TestCase):
    """ Test users Api """
    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """test creating user with valid payload is successful"""
        payload = {
            'email': 'test@test.com',
            'password': 'testtest',
            'name': 'Test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn('password', res.data)

    def test_users_exists(self):
        """Test creating a user that already exists"""
        payload = {
            'email': 'test@test.com',
            'password': 'testtest'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 6 chars"""
        payload = {
            'email': 'test@test.com',
            'password': 'test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_user_token(self):
        """test that the token is created for the user """
        payload = {
            'email': 'test@test.com',
            'password': 'testtest'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """test that token is not created if invalid credentials are given"""
        create_user(email='test@test.com', password='testtest')
        payload = {
            'email': 'test@test.com',
            'password': '123456'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesnt exist"""
        payload = {
            'email': 'test@test.com',
            'password': '123456'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """test password and email are required"""
        payload = {
            'email': 'test@test.com',
            'password': ''
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retreive_user_unauthorized(self):
        """Auth is required"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthUserApiTests(TestCase):
    """Test API requests that requires authentication"""

    def setUp(self):
        self.user = create_user(
            email='test@test.com',
            password='testtest',
            name='name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_me_not_allowed(self):
        """test that the POST request is not allowed on the me url"""
        payload = {
            'email': "post@notallowed.com",
            'name': "post"
        }
        res = self.client.post(ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_me_allowed(self):
        """test that the patch requests are allowed on me url"""
        payload = {
            'password': "patchtest",
            'name': "patch"
        }
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
