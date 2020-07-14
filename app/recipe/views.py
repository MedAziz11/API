from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient

from . import serializers


class BaseRecipeViewSet(viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin):
    """Base viewset for user owned recipe attributes """
    authentication_classes = TokenAuthentication,
    permission_classes = IsAuthenticated,

    def get_queryset(self):
        """Return objects  for the current Auth user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """create a new attribute"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeViewSet):
    """Manage tags in the data base"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(BaseRecipeViewSet):
    """Manage ingredients in the DataBase"""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
