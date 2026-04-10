"""
Script para poblar la base de datos con datos de prueba.
Uso: python seed.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Product, Order

# Usuarios
alice = User.objects.create_user(username='alice', password='alice123', email='alice@test.com')
bob = User.objects.create_user(username='bob', password='bob123', email='bob@test.com')
admin = User.objects.create_user(username='admin', password='admin123', email='admin@test.com', is_admin=True)

# Productos
p1 = Product.objects.create(name='Laptop', price=999.99, stock=10)
p2 = Product.objects.create(name='Mouse', price=29.99, stock=50)
p3 = Product.objects.create(name='Teclado', price=59.99, stock=30)

# Órdenes (alice tiene orden #1, bob tiene orden #2)
Order.objects.create(owner=alice, product=p1, quantity=1)
Order.objects.create(owner=bob, product=p2, quantity=2)
Order.objects.create(owner=bob, product=p3, quantity=1)

print("Datos de prueba creados:")
print(f"  Usuarios: alice / alice123, bob / bob123, admin / admin123")
print(f"  Productos: {Product.objects.count()}")
print(f"  Órdenes: {Order.objects.count()}")
print()
print("Vulnerabilidades presentes:")
print("  API1 (BOLA):  GET /api/orders/1/ con token de bob → devuelve orden de alice")
print("  API2 (Auth):  GET /api/users/  sin token        → devuelve todos los usuarios")
print("  API3 (Props): GET /api/users/1/ sin token       → expone password hash e is_admin")
print("  API4 (Throttle): sin límite de requests en ningún endpoint")
print("  API5 (FuncAuthz): GET /api/admin-panel/ sin token → devuelve datos de admin")
