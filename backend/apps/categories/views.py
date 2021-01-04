from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from backend.apps.categories.models import Category
from backend.apps.categories.serializers import CategorySerializer


class CategoryAPIView(APIView):
    serializer_class = CategorySerializer

    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = self.serializer_class(category).data
        data['parents'] = self.serializer_class(category.parents, many=True).data
        data['children'] = self.serializer_class(category.children, many=True).data
        data['siblings'] = self.serializer_class(category.siblings, many=True).data
        return Response(data)

    def post(self, request, *args, **kwargs):
        names = set()

        def validate(data):
            name = data.get('name')
            children = data.get('children', list())
            valid = all([
                name,
                isinstance(name, str),
                isinstance(children, list),
                len(name) <= Category._meta.get_field('name').max_length,
                name not in names,
            ])
            if not valid:
                raise
            names.add(name)
            for child in children:
                validate(child)

        try:
            validate(request.data)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if Category.objects.filter(name__in=names).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            category = Category.objects.create(name=request.data['name'])
            if children := request.data.get('children'):
                self._create_children(category, children)

        return Response(status=status.HTTP_201_CREATED)

    def _create_children(self, parent, data):
        children = [
            {'category': Category(name=i['name'], parent=parent), 'children': i.get('children', list())}
            for i in data
        ]

        Category.objects.bulk_create([child['category'] for child in children])
        for child in children:
            self._create_children(child['category'], child['children'])
