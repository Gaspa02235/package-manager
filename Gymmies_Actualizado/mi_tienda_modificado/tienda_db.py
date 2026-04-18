import sqlite3

DB_PATH = 'tienda.sqlite3'

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Productos con stock
    c.execute('''CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        precio REAL NOT NULL,
        costo REAL NOT NULL DEFAULT 0,
        imagen TEXT,
        categoria TEXT,
        stock INTEGER NOT NULL DEFAULT 0
    )''')

    # Migración: agregar columna costo si no existe (para bases de datos ya creadas)
    try:
        c.execute('ALTER TABLE productos ADD COLUMN costo REAL NOT NULL DEFAULT 0')
        conn.commit()
    except Exception:
        pass  # La columna ya existe

    # Carrito por sesión/usuario
    c.execute('''CREATE TABLE IF NOT EXISTS carrito (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(producto_id) REFERENCES productos(id)
    )''')

    # Pedidos con datos de envío y estado
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_cliente TEXT NOT NULL,
        email TEXT NOT NULL,
        telefono TEXT,
        calle TEXT NOT NULL,
        colonia TEXT NOT NULL,
        ciudad TEXT NOT NULL,
        estado TEXT NOT NULL,
        cp TEXT NOT NULL,
        total REAL NOT NULL,
        envio REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'recibido',
        fecha TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    )''')

    # Detalle de pedidos
    c.execute('''CREATE TABLE IF NOT EXISTS pedido_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        nombre_producto TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
        FOREIGN KEY(producto_id) REFERENCES productos(id)
    )''')

    # Avisos del admin
    c.execute('''CREATE TABLE IF NOT EXISTS avisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        cuerpo TEXT NOT NULL,
        activo INTEGER NOT NULL DEFAULT 1,
        fecha TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    )''')

    # Seed productos si está vacío
    c.execute('SELECT COUNT(*) FROM productos')
    if c.fetchone()[0] == 0:
        productos = [
            ('Mancuernas Ajustables 20kg', 'Par de mancuernas ajustables de acero con agarre antideslizante. Ideal para entrenamiento en casa o gym.', 899.00, 550.00, 'mancuernas.jpg', 'Pesas', 15),
            ('Barra Olímpica 20kg', 'Barra olímpica de acero niquelado, 220cm, capacidad 300kg. Para levantamiento de potencia.', 1599.00, 950.00, 'barra.jpg', 'Pesas', 8),
            ('Cuerda para Saltar Pro', 'Cuerda de velocidad con rodamientos de acero, cable de acero recubierto. Perfecta para HIIT.', 199.00, 80.00, 'cuerda.jpg', 'Accesorios', 50),
            ('Guantes de Gym', 'Guantes de entrenamiento con soporte de muñeca integrado. Cuero sintético premium.', 249.00, 110.00, 'guantes.jpg', 'Accesorios', 30),
            ('Playera Dry-Fit', 'Playera deportiva de alto rendimiento, tela transpirable y anti-sudor. Tallas S-XXL.', 349.00, 150.00, 'playera.jpg', 'Ropa', 40),
            ('Shorts de Entrenamiento', 'Shorts ligeros con bolsillos laterales y cintura elástica. Tela stretch 4 vías.', 299.00, 120.00, 'shorts.jpg', 'Ropa', 35),
            ('Banda de Resistencia Pack x5', 'Set de 5 bandas con resistencias de 10 a 50 lbs. Látex natural, duraderas.', 399.00, 180.00, 'bandas.jpg', 'Accesorios', 20),
            ('Kettlebell 16kg', 'Kettlebell de hierro fundido con base plana, 16kg. Acabado en polvo negro.', 649.00, 380.00, 'kettlebell.jpg', 'Pesas', 12),
        ]
        c.executemany('INSERT INTO productos (nombre, descripcion, precio, costo, imagen, categoria, stock) VALUES (?,?,?,?,?,?,?)', productos)

    conn.commit()
    conn.close()

# ─── PRODUCTOS ───────────────────────────────────────────────────

def get_todos_productos():
    conn = get_connection()
    productos = conn.execute('SELECT * FROM productos ORDER BY id').fetchall()
    conn.close()
    return productos

def get_producto(id):
    conn = get_connection()
    producto = conn.execute('SELECT * FROM productos WHERE id=?', (id,)).fetchone()
    conn.close()
    return producto

def agregar_producto(nombre, descripcion, precio, costo, imagen, categoria, stock):
    conn = get_connection()
    conn.execute('INSERT INTO productos (nombre, descripcion, precio, costo, imagen, categoria, stock) VALUES (?,?,?,?,?,?,?)',
                 (nombre, descripcion, precio, costo, imagen, categoria, stock))
    conn.commit()
    conn.close()

def eliminar_producto(id):
    conn = get_connection()
    conn.execute('DELETE FROM carrito WHERE producto_id=?', (id,))
    conn.execute('DELETE FROM productos WHERE id=?', (id,))
    conn.commit()
    conn.close()

def actualizar_stock(producto_id, delta):
    """Reduce stock by delta. Returns False if insufficient stock."""
    conn = get_connection()
    prod = conn.execute('SELECT stock FROM productos WHERE id=?', (producto_id,)).fetchone()
    if not prod or prod['stock'] < delta:
        conn.close()
        return False
    conn.execute('UPDATE productos SET stock = stock - ? WHERE id=?', (delta, producto_id))
    conn.commit()
    conn.close()
    return True

def get_productos_por_categoria(categoria):
    conn = get_connection()
    productos = conn.execute('SELECT * FROM productos WHERE categoria=?', (categoria,)).fetchall()
    conn.close()
    return productos

# ─── CARRITO ─────────────────────────────────────────────────────

def get_carrito():
    conn = get_connection()
    items = conn.execute('''
        SELECT c.id, p.id as producto_id, p.nombre, p.precio, p.imagen,
               p.categoria, p.stock, c.cantidad,
               (p.precio * c.cantidad) as subtotal
        FROM carrito c JOIN productos p ON c.producto_id = p.id
    ''').fetchall()
    conn.close()
    return items

def agregar_al_carrito(producto_id, cantidad=1):
    conn = get_connection()
    # Verificar stock disponible
    prod = conn.execute('SELECT stock FROM productos WHERE id=?', (producto_id,)).fetchone()
    if not prod:
        conn.close()
        return False
    existing = conn.execute('SELECT id, cantidad FROM carrito WHERE producto_id=?', (producto_id,)).fetchone()
    if existing:
        nueva_cantidad = existing['cantidad'] + cantidad
        if nueva_cantidad > prod['stock']:
            conn.close()
            return False
        conn.execute('UPDATE carrito SET cantidad=? WHERE id=?', (nueva_cantidad, existing['id']))
    else:
        if cantidad > prod['stock']:
            conn.close()
            return False
        conn.execute('INSERT INTO carrito (producto_id, cantidad) VALUES (?,?)', (producto_id, cantidad))
    conn.commit()
    conn.close()
    return True

def vaciar_carrito():
    conn = get_connection()
    conn.execute('DELETE FROM carrito')
    conn.commit()
    conn.close()

def eliminar_del_carrito(carrito_id):
    conn = get_connection()
    conn.execute('DELETE FROM carrito WHERE id=?', (carrito_id,))
    conn.commit()
    conn.close()

# ─── PEDIDOS ─────────────────────────────────────────────────────

STATUSES = ['recibido', 'preparando', 'enviado', 'en_camino', 'entregado']

STATUS_LABELS = {
    'recibido': 'Pedido Recibido',
    'preparando': 'Preparando',
    'enviado': 'Enviado',
    'en_camino': 'En Camino',
    'entregado': 'Entregado',
}

def crear_pedido(datos_cliente, items, total, envio):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO pedidos (nombre_cliente, email, telefono, calle, colonia, ciudad, estado, cp, total, envio, status)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (datos_cliente['nombre'], datos_cliente['email'], datos_cliente.get('telefono',''),
               datos_cliente['calle'], datos_cliente['colonia'], datos_cliente['ciudad'],
               datos_cliente['estado'], datos_cliente['cp'], total, envio, 'recibido'))
    pedido_id = c.lastrowid
    for item in items:
        c.execute('''INSERT INTO pedido_items (pedido_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal)
                     VALUES (?,?,?,?,?,?)''',
                  (pedido_id, item['producto_id'], item['nombre'], item['cantidad'], item['precio'], item['subtotal']))
        # Descontar stock
        conn.execute('UPDATE productos SET stock = stock - ? WHERE id=?', (item['cantidad'], item['producto_id']))
    conn.commit()
    conn.close()
    return pedido_id

def get_todos_pedidos():
    conn = get_connection()
    pedidos = conn.execute('SELECT * FROM pedidos ORDER BY fecha DESC').fetchall()
    conn.close()
    return pedidos

def get_pedido(id):
    conn = get_connection()
    pedido = conn.execute('SELECT * FROM pedidos WHERE id=?', (id,)).fetchone()
    items = conn.execute('SELECT * FROM pedido_items WHERE pedido_id=?', (id,)).fetchall()
    conn.close()
    return pedido, items

def actualizar_status_pedido(pedido_id, nuevo_status):
    conn = get_connection()
    conn.execute('UPDATE pedidos SET status=? WHERE id=?', (nuevo_status, pedido_id))
    conn.commit()
    conn.close()

# ─── AVISOS ──────────────────────────────────────────────────────

def get_avisos_activos():
    conn = get_connection()
    avisos = conn.execute('SELECT * FROM avisos WHERE activo=1 ORDER BY fecha DESC').fetchall()
    conn.close()
    return avisos

def get_todos_avisos():
    conn = get_connection()
    avisos = conn.execute('SELECT * FROM avisos ORDER BY fecha DESC').fetchall()
    conn.close()
    return avisos

def crear_aviso(titulo, cuerpo):
    conn = get_connection()
    conn.execute('INSERT INTO avisos (titulo, cuerpo) VALUES (?,?)', (titulo, cuerpo))
    conn.commit()
    conn.close()

def toggle_aviso(aviso_id):
    conn = get_connection()
    conn.execute('UPDATE avisos SET activo = 1 - activo WHERE id=?', (aviso_id,))
    conn.commit()
    conn.close()

def eliminar_aviso(aviso_id):
    conn = get_connection()
    conn.execute('DELETE FROM avisos WHERE id=?', (aviso_id,))
    conn.commit()
    conn.close()
