from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """Create a sample recipe object"""
    defaults = {
        'title': 'Pasta',
        'time_minutes': 12,
        'price': 10
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class RecipeTests(TestCase):
    """Test the Publicly available recipe """
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """test login is required for retrieving the recipes"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthRecipeTests(TestCase):
    """Test the authorized user recipe API"""
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@test.com',
            'testtest'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieving_user_recipe(self):
        """test retrieving the user's recipes"""
        sample_recipe(self.user)
        sample_recipe(self.user)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_the_auth_user(self):
        """test that the recipes are only limited to the authenticated user"""
        user2 = get_user_model().objects.create_user(
            'user2@test.com',
            'testtest'
        )
        sample_recipe(user2)
        sample_recipe(self.user)
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], serializer.data[0]['title'])
