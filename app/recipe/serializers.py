from rest_framework import serializers

from core.models import Tag, Ingredient, Recipe


class TagSerializer(serializers.ModelSerializer):
    """Serializer Tag objects"""

    class Meta:
        model = Tag
        fields = 'id', 'name'
        read_only_fields = 'id',


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer Ingredients objects"""

    class Meta:
        model = Ingredient
        fields = 'id', 'name'
        read_only_fields = 'id',


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer Recipe Objects"""
    ingredients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Ingredient.objects.all()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = 'title', 'user', 'time_minutes', 'price', 'link',\
                 'ingredients', 'tags'
        read_only_fields = 'id',
