from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from backend.apps.categories.models import Category


class CategoryCreateAPITestCase(TestCase):

    def setUp(self):
        self.url = reverse('categories:create-categories')

    def test_create_valid_name(self):
        data = {'name': 'category'}
        response = self.client.post(self.url, data, format='json', content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.get().name, 'category')

    def test_create_no_name(self):
        data = {'title': 'category'}
        response = self.client.post(self.url, data, format='json', content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 0)

    def test_create_empty_name(self):
        data = {'name': ''}
        response = self.client.post(self.url, data, format='json', content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 0)

    def test_create_large_name(self):
        data = {'name': '1' * (Category._meta.get_field('name').max_length + 1)}
        response = self.client.post(self.url, data, format='json', content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 0)

    def test_create_not_unique_name(self):
        data = {'name': 'category'}
        response_one = self.client.post(self.url, data, format='json', content_type='application/json')
        response_second = self.client.post(self.url, data, format='json', content_type='application/json')

        self.assertEqual(response_one.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)

    def test_create_valid_with_children(self):
        data = {
            'name': 'category 1',
            'children': [
                {
                    'name': 'category 1.1',
                },
                {
                    'name': 'category 1.2',
                },
                {
                    'name': 'category 1.3',
                    'children': [
                        {
                            'name': 'category 1.3.1',
                        },
                    ],
                },
            ],
        }
        response = self.client.post(self.url, data, format='json', content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(Category.objects.first().name, 'category 1')
        self.assertEqual(Category.objects.last().name, 'category 1.3.1')

        parents = {parent.name for parent in Category.objects.get(name='category 1.3.1').parents}
        self.assertSetEqual(parents, {'category 1.3', 'category 1'})

        children = {child.name for child in Category.objects.get(name='category 1').children.all()}
        self.assertSetEqual(children, {'category 1.1', 'category 1.2', 'category 1.3'})

        siblings = {sibling.name for sibling in Category.objects.get(name='category 1.2').siblings.all()}
        self.assertSetEqual(siblings, {'category 1.1', 'category 1.3'})


class CategoryGetAPITestCase(TestCase):

    def test_get_by_valid_id(self):
        category = Category.objects.create(name='Category 1')
        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': category.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], category.name)

    def test_get_by_invalid_id(self):
        category = Category.objects.create(name='Category 1')
        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': category.pk + 1}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_children(self):
        category = Category.objects.create(name='Category 1')
        child_one = Category.objects.create(name='Category 1.1', parent=category)
        child_second = Category.objects.create(name='Category 1.2', parent=category)
        not_child_one = Category.objects.create(name='Category 1.1.1', parent=child_one)
        not_child_second = Category.objects.create(name='Category 2')

        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': category.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({child['name'] for child in response.data['children']}, {child_one.name, child_second.name})

        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': not_child_second.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({child['name'] for child in response.data['children']}, set())

    def test_get_parents(self):
        grand_parent = Category.objects.create(name='Category 1')
        parent = Category.objects.create(name='Category 2', parent=grand_parent)
        category = Category.objects.create(name='Category 3', parent=parent)
        child = Category.objects.create(name='Category 4', parent=category)
        sibling = Category.objects.create(name='Category 5', parent=parent)

        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': category.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({child['name'] for child in response.data['parents']}, {parent.name, grand_parent.name})

        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': grand_parent.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({child['name'] for child in response.data['parents']}, set())

    def test_get_siblings(self):
        grand_parent = Category.objects.create(name='Category 1')
        parent = Category.objects.create(name='Category 2', parent=grand_parent)
        category = Category.objects.create(name='Category 3', parent=parent)
        child = Category.objects.create(name='Category 4', parent=category)
        sibling_one = Category.objects.create(name='Category 5', parent=parent)
        sibling_second = Category.objects.create(name='Category 6', parent=parent)

        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': category.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(
            {child['name'] for child in response.data['siblings']}, {sibling_one.name, sibling_second.name})

        response = self.client.get(reverse('categories:get-categories', kwargs={'pk': parent.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual({child['name'] for child in response.data['siblings']}, set())
