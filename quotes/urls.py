from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.random_quote, name='random_quote'),
    path('add/', views.add_quote, name='add_quote'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(
        template_name='quotes/login.html'), name='login'
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('random_source/',
         views.random_source_quotes,
         name='random_source_quotes'),
    path('register/', views.register, name='register'),
    path('top/', views.top_quotes, name='top_quotes'),
    path('vote/<int:quote_id>/<str:vote_type>/', views.vote, name='vote'),
    path('edit/<int:quote_id>/', views.edit_quote, name='edit_quote'),
]
