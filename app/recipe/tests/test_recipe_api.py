import os
import tempfile

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Ingredient, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_tag(user, name="test Tag"):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="test Ingredient"):
    """Create and return a sample Ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
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

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)
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

    def test_recipe_detail_view(self):
        """test viewing a recipe details"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        #  .add() because it is a many to many field
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic recipe"""
        payload = {
            'title': 'Pasta',
            'time_minutes': 12,
            'price': 10
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_creating_recipe_with_tags(self):
        """test creating recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'tasty',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 12,
            'price': 5
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_creating_recipe_with_ingredients(self):
        """test creating a recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name='ingredient1')
        ingredient2 = sample_ingredient(user=self.user, name='ingredient2')
        payload = {
            'title': 'sauce',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 12,
            'price': 5
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """testing a partial update for the recipe"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="tasty")
        payload = {
            'title': 'threesome pasta',
            'tags': [new_tag.id]
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(payload['title'], recipe.title)
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """test a full update for the recipe"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        new_tag = sample_tag(user=self.user, name="tasty")
        new_ingredient = sample_ingredient(user=self.user, name="Hrissa")
        payload = {
            'title': 'chicken nuggets',
            'price': 12,
            'time_minutes': 30,
            'tags': [new_tag.id],
            'ingredients': [new_ingredient.id]
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(payload['title'], recipe.title)
        self.assertEqual(payload['price'], recipe.price)
        self.assertEqual(payload['time_minutes'], recipe.time_minutes)

        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 1)
        self.assertIn(new_ingredient, ingredients)


class RecipeImageUploadTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@test.com',
            'testtest'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.patch(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.patch(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = sample_recipe(user=self.user, title='pasta')
        recipe2 = sample_recipe(user=self.user, title='salade')
        tag1 = sample_tag(user=self.user, name='tasty')
        tag2 = sample_tag(user=self.user, name='vegan')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='cheese')

        res = self.client.get(
            RECIPE_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """test returning recipes with specific ingredients"""
        recipe1 = sample_recipe(user=self.user, title='pasta')
        recipe2 = sample_recipe(user=self.user, title='salade')
        ingredient1 = sample_ingredient(user=self.user, name='tasty')
        ingredient2 = sample_ingredient(user=self.user, name='vegan')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='cheese')

        res = self.client.get(
            RECIPE_URL,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
