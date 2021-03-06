from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from mezzanine.blog.models import BlogPost as Post, BlogCategory
from mezzanine.pages.models import Page

from rest_framework import viewsets, filters, permissions, mixins
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import UserSerializer, CategorySerializer, PageSerializer, SiteSerializer
from .serializers import PostCreateSerializer, PostUpdateSerializer, PostOutputSerializer
from .permissions import IsAdminOrReadOnly  # , IsAppAuthenticated
from .pagination import MezzaninePagination, PostPagination
from .mixins import PutUpdateModelMixin

# Supports custom user models
User = get_user_model()


class ListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A viewset that provides only `list` actions.

    To use it, override the class and set the `.queryset` and `.serializer_class` attributes.
    """
    pass


class SiteViewSet(ListViewSet):
    """
    For retrieving site title, tagline and domain.
    """
    queryset = Site.objects.all()
    serializer_class = SiteSerializer


class UserFilter(django_filters.FilterSet):
    """
    A class for filtering users.
    """
    username = django_filters.CharFilter(field_name="username", lookup_expr='istartswith')

    class Meta:
        model = User
        fields = ['username']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    For listing or retrieving users.
    ---
    list:
        parameters:
            - name: username
              type: string
              description: Filter usernames starting with query
              paramType: query
            - name: page
              type: integer
              description: Page number
              paramType: query
    """
    queryset = User.objects.all()
    filterset_class = UserFilter
    filter_backends = (DjangoFilterBackend,)
    serializer_class = UserSerializer
    pagination_class = MezzaninePagination
    permission_classes = (permissions.IsAdminUser,)


class PageFilter(django_filters.FilterSet):
    """
    A class for filtering pages by title.
    """
    title = django_filters.CharFilter(field_name="title")

    class Meta:
        model = Page
        fields = ['title']


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    For listing or retrieving pages.
    ---
    list:
        parameters:
            - name: page
              type: integer
              description: Page number
              paramType: query
    """
    queryset = Page.objects.published()
    serializer_class = PageSerializer
    pagination_class = MezzaninePagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filterset_class = PageFilter
    ordering_fields = ('id', 'parent', 'title',)
    ordering = ('title',)

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if user and not user.is_authenticated:
            queryset = queryset.filter(login_required=False)

        return queryset


class CategoryViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      PutUpdateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    For listing, retrieving, creating or updating blog categories.
    ---
    list:
        parameters:
            - name: search
              type: string
              description: Search for category names that match the query
              paramType: query
            - name: page
              type: integer
              description: Page number
              paramType: query
    """
    queryset = BlogCategory.objects.all()
    serializer_class = CategorySerializer
    pagination_class = MezzaninePagination
    permission_classes = [IsAdminOrReadOnly]  # IsAppAuthenticated
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,)
    ordering_fields = ('id', 'title',)
    ordering = ('title',)
    search_fields = ('title',)


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """
    Enable multi-category filtering
    """
    pass


class PostFilter(django_filters.FilterSet):
    """
    A class for filtering blog posts.
    """
    category_id = django_filters.NumberFilter(field_name="categories__id")
    category_name = CharInFilter(field_name="categories__title", lookup_expr='in')
    category_slug = django_filters.CharFilter(field_name="categories__slug", lookup_expr='exact')
    tag = django_filters.CharFilter(field_name='keywords_string', lookup_expr='contains')
    author_id = django_filters.NumberFilter(field_name="user__id")
    author_name = django_filters.CharFilter(field_name="user__username", lookup_expr='istartswith')
    date_min = django_filters.DateFilter(field_name='publish_date', lookup_expr='gte')
    date_max = django_filters.DateFilter(field_name='publish_date', lookup_expr='lte')

    class Meta:
        model = Post
        fields = ['category_id', 'category_name', 'tag', 'author_id', 'author_name', 'date_min', 'date_max']


class PostViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  PutUpdateModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    For listing, retrieving, creating or updating blog posts.
    ---
    list:
        parameters:
            - name: category_id
              type: integer
              description: Filter posts by category ID
              paramType: query
            - name: category_name
              type: string
              description: Filter posts by category name
              paramType: query
            - name: category_slug
              type: string
              description: Filter posts by category slug
              paramType: query
            - name: tag
              type: string
              description: Filter posts by tag name
              paramType: query
            - name: author_id
              type: integer
              description: Filter posts by author ID
              paramType: query
            - name: author_name
              type: string
              description: Filter posts by author's username
              paramType: query
            - name: date_min
              type: datetime
              description: Filter posts by minimum publish date
              paramType: query
            - name: date_max
              type: datetime
              description: Filter posts by maximum publish date
              paramType: query
            - name: search
              type: string
              description: Search for blog posts that match the query
              paramType: query
            - name: page
              type: integer
              description: Page number
              paramType: query
    """
    queryset = Post.objects.filter(status=2)
    pagination_class = PostPagination
    permission_classes = [IsAdminOrReadOnly]  # IsAppAuthenticated
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter,)
    filterset_class = PostFilter
    ordering_fields = ('id', 'title', 'publish_date', 'updated', 'user',)
    ordering = ('-publish_date',)
    search_fields = ('title', 'content',)

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PostUpdateSerializer
        elif self.request.method == 'POST':
            return PostCreateSerializer
        else:
            return PostOutputSerializer
