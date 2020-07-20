from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')


class IngredientApiTest(TestCase):
    """Test the publicly available Ingredient API"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthIngredientApiTest(TestCase):
    """Test the authorized user Ingredient API"""
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@test.com',
            'testtest'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient(self):
        """Test the retrievement of user's ingredients"""
        Ingredient.objects.create(user=self.user, name="TestIngredient1")
        Ingredient.objects.create(user=self.user, name="TestIngredient2")

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_authenticated_user(self):
        """test that the ingredients are limited to the authenticated user"""
        user2 = get_user_model().objects.create_user(
            'user2@test.com',
            'testtest'
        )
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="TestIngredient1"
            )
        Ingredient.objects.create(user=user2, name='User2 Ingredients test')

        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_creating_ingredients_successful(self):
        """tests creating ingredients for the auth user"""
        payload = {'name': 'Test name'}
        self.client.post(INGREDIENT_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_valid_name_ingredient(self):
        """test that the ingredient name is valid"""
        res = self.client.post(INGREDIENT_URL, {'name': ''})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """test filtering tags by those who are assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='chicken')
        ingredient2 = Ingredient.objects.create(user=self.user, name='turky')
        recipe = Recipe.objects.create(
            title='Coriander eggs and toast',
            price=12,
            time_minutes=30,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)
        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
