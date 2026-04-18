# 🐼 Gymmies Store — Proyecto Completo

## Cómo correr el proyecto

```bash
cd mi_tienda
pip install flask
python app.py
```
Luego abre: http://127.0.0.1:5000

## Usuarios

| Usuario    | Contraseña | Rol       |
|------------|-----------|-----------|
| `admin`    | `admin123` | Admin     |
| `comprador`| `gym2024`  | Comprador |

## Funcionalidades nuevas

### Comprador
- 🛍️ Ver stock disponible en cada producto (OK / Pocas unidades / Agotado)
- 🛒 Carrito con contador en el navbar
- 📦 Checkout con formulario completo de datos de envío
- 📋 Mis Pedidos: lista con barra de seguimiento visual
- 🔍 Detalle de pedido con dirección y productos

### Administrador
- 📊 Dashboard con estadísticas (productos, pedidos, ventas)
- ➕ Agregar productos con stock inicial
- 🗑️ Eliminar productos
- 🚚 Cambiar status de pedidos (Recibido → Preparando → Enviado → En Camino → Entregado)
- 📢 Crear/pausar/eliminar avisos que aparecen en la tienda

## Estructura
```
mi_tienda/
├── app.py           ← Rutas Flask
├── tienda_db.py     ← Base de datos SQLite
├── requirements.txt
├── static/
│   └── styles.css
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── producto.html
    ├── carrito.html
    ├── checkout.html       ← NUEVO: formulario de envío
    ├── checkout_ok.html    ← confirmación con pedido ID
    ├── mis_pedidos.html    ← NUEVO: tracking de pedidos
    ├── detalle_pedido.html ← NUEVO: detalle con dirección
    ├── admin.html          ← NUEVO: panel completo
    └── admin_producto.html ← NUEVO: agregar producto
```
