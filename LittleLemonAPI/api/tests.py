from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from .models import Category, MenuItem, Cart, Order, OrderItem

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        
        self.category = Category.objects.create(slug='test-category', title='Test Category')
        self.menu_item = MenuItem.objects.create(title='Test Item', price=10.00, featured=True, category=self.category)

    def test_menu_items_list(self):
        response = self.client.get(reverse('menu-items'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_menu_item(self):
        data = {
            'title': 'New Item',
            'price': 15.00,
            'featured': False,
            'category': self.category.id
        }
        response = self.client.post(reverse('menu-items'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_add_to_cart(self):
        data = {
            'menu_item_id': self.menu_item.id,
            'quantity': 2
        }
        response = self.client.post(reverse('cart-items'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_order_list(self):
        response = self.client.get(reverse('orders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
