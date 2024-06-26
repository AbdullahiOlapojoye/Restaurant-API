from django.urls import path
from . import views

urlpatterns = [
    path('menu-items/', views.MenuItemListView.as_view(), name='menu-items'),
    path('menu-items/<int:pk>/', views.MenuItemDetailView.as_view(), name='menu-item-detail'),
    path('cart/menu-items/', views.CartItemView.as_view(), name='cart-items'),
    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('groups/<str:group_name>/users/', views.UserGroupListView.as_view(), name='group-users'),
    path('groups/<str:group_name>/users/add/', views.AddUserToGroupView.as_view(), name='add-user-to-group'),
    path('groups/<str:group_name>/users/<int:user_id>/', views.RemoveUserFromGroupView.as_view(), name='remove-user-from-group'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
]