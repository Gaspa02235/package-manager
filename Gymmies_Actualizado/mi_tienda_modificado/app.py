from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from tienda_db import (
    init_db, get_todos_productos, get_producto,
    agregar_producto, eliminar_producto,
    get_carrito, agregar_al_carrito, vaciar_carrito, eliminar_del_carrito,
    get_productos_por_categoria, crear_pedido,
    get_todos_pedidos, get_pedido, actualizar_status_pedido,
    get_avisos_activos, get_todos_avisos, crear_aviso, toggle_aviso, eliminar_aviso,
    STATUSES, STATUS_LABELS
)

app = Flask(__name__)
app.secret_key = 'gymmies_secret_2024'

# ── Usuarios hardcoded ──────────────────────────────────────
USUARIOS = {
    'admin':    {'password': 'admin123', 'rol': 'admin'},
    'comprador': {'password': 'gym2024', 'rol': 'comprador'},
}

# Inicializar DB
with app.app_context():
    init_db()

# ── Decoradores ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ── Context processor ───────────────────────────────────────
@app.context_processor
def inject_globals():
    carrito_count = 0
    if 'usuario' in session:
        items = get_carrito()
        carrito_count = sum(item['cantidad'] for item in items)
    return {'carrito_count': carrito_count, 'STATUS_LABELS': STATUS_LABELS}

# ── Auth ────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if 'usuario' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '').strip()
        user = USUARIOS.get(usuario)
        if user and user['password'] == password:
            session['usuario'] = usuario
            session['rol'] = user['rol']
            if user['rol'] == 'admin':
                return redirect(url_for('admin_panel'))
            return redirect(url_for('index'))
        error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Página principal ────────────────────────────────────────
@app.route('/')
def index():
    productos = get_todos_productos()
    avisos = get_avisos_activos()
    return render_template('index.html', productos=productos, avisos=avisos)

@app.route('/producto/<int:id>')
def producto(id):
    p = get_producto(id)
    if not p:
        return redirect(url_for('index'))
    return render_template('producto.html', producto=p)

@app.route('/categoria/<nombre>')
def categoria(nombre):
    productos = get_productos_por_categoria(nombre)
    avisos = get_avisos_activos()
    return render_template('index.html', productos=productos, categoria_activa=nombre, avisos=avisos)

# ── Carrito ─────────────────────────────────────────────────
@app.route('/agregar/<int:id>', methods=['POST'])
@login_required
def agregar(id):
    cantidad = int(request.form.get('cantidad', 1))
    ok = agregar_al_carrito(id, cantidad)
    if not ok:
        flash('No hay suficiente stock disponible.', 'error')
    else:
        flash('Producto agregado al carrito. 🛒', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/carrito')
@login_required
def carrito():
    items = get_carrito()
    subtotal = sum(item['subtotal'] for item in items)
    envio = 0 if subtotal >= 999 else 99
    total = subtotal + envio
    return render_template('carrito.html', items=items, subtotal=subtotal, envio=envio, total=total)

@app.route('/eliminar_carrito/<int:id>')
@login_required
def eliminar_carrito(id):
    eliminar_del_carrito(id)
    return redirect(url_for('carrito'))

# ── Checkout ────────────────────────────────────────────────
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = get_carrito()
    if not items:
        return redirect(url_for('carrito'))

    subtotal = sum(item['subtotal'] for item in items)
    envio = 0 if subtotal >= 999 else 99
    total = subtotal + envio

    if request.method == 'POST':
        datos = {
            'nombre':   request.form.get('nombre', '').strip(),
            'email':    request.form.get('email', '').strip(),
            'telefono': request.form.get('telefono', '').strip(),
            'calle':    request.form.get('calle', '').strip(),
            'colonia':  request.form.get('colonia', '').strip(),
            'ciudad':   request.form.get('ciudad', '').strip(),
            'estado':   request.form.get('estado', '').strip(),
            'cp':       request.form.get('cp', '').strip(),
        }
        # Validar campos requeridos
        required = ['nombre', 'email', 'calle', 'colonia', 'ciudad', 'estado', 'cp']
        if not all(datos[k] for k in required):
            flash('Por favor completa todos los campos requeridos.', 'error')
            return render_template('checkout.html', items=items, subtotal=subtotal, envio=envio, total=total, datos=datos)

        items_data = [{'producto_id': item['producto_id'], 'nombre': item['nombre'],
                       'cantidad': item['cantidad'], 'precio': item['precio'],
                       'subtotal': item['subtotal']} for item in items]

        pedido_id = crear_pedido(datos, items_data, total, envio)
        vaciar_carrito()
        return redirect(url_for('pedido_confirmado', id=pedido_id))

    return render_template('checkout.html', items=items, subtotal=subtotal, envio=envio, total=total, datos={})

@app.route('/pedido/<int:id>/confirmado')
@login_required
def pedido_confirmado(id):
    pedido, items = get_pedido(id)
    if not pedido:
        return redirect(url_for('index'))
    return render_template('checkout_ok.html', pedido=pedido, items=items, STATUS_LABELS=STATUS_LABELS)

@app.route('/mis-pedidos')
@login_required
def mis_pedidos():
    # Para un cliente real aquí filtraríamos por email/usuario
    # Como tenemos usuario hardcoded, mostramos todos los pedidos del comprador
    pedidos = get_todos_pedidos()
    return render_template('mis_pedidos.html', pedidos=pedidos, STATUS_LABELS=STATUS_LABELS, STATUSES=['recibido','preparando','enviado','en_camino','entregado'])

@app.route('/mis-pedidos/<int:id>')
@login_required
def detalle_pedido(id):
    pedido, items = get_pedido(id)
    if not pedido:
        return redirect(url_for('mis_pedidos'))
    return render_template('detalle_pedido.html', pedido=pedido, items=items, STATUS_LABELS=STATUS_LABELS, STATUSES=['recibido','preparando','enviado','en_camino','entregado'])

# ── Admin Panel ─────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_panel():
    productos = get_todos_productos()
    pedidos = get_todos_pedidos()
    avisos = get_todos_avisos()
    total_ventas = sum(p['total'] for p in pedidos)
    pedidos_hoy = [p for p in pedidos if p['fecha'][:10] == __import__('datetime').date.today().isoformat()]
    # Ganancia estimada: suma de (precio - costo) de todos los productos vendidos en pedidos
    total_ganancia = sum((p['precio'] - p['costo']) * p['stock'] for p in productos if p['precio'] > 0)
    return render_template('admin.html',
                           productos=productos,
                           pedidos=pedidos,
                           avisos=avisos,
                           total_ventas=total_ventas,
                           total_ganancia=total_ganancia,
                           pedidos_hoy=len(pedidos_hoy),
                           STATUS_LABELS=STATUS_LABELS)

@app.route('/admin/producto/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo_producto():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        precio = float(request.form['precio'])
        costo = float(request.form.get('costo', 0))
        imagen = request.form.get('imagen', '').strip()
        categoria = request.form['categoria']
        stock = int(request.form.get('stock', 0))
        agregar_producto(nombre, descripcion, precio, costo, imagen, categoria, stock)
        flash(f'Producto "{nombre}" agregado correctamente. ✅', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('admin_producto.html')

@app.route('/admin/producto/eliminar/<int:id>', methods=['POST'])
@admin_required
def admin_eliminar_producto(id):
    p = get_producto(id)
    if p:
        eliminar_producto(id)
        flash(f'Producto "{p["nombre"]}" eliminado.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/pedido/<int:id>/status', methods=['POST'])
@admin_required
def admin_status_pedido(id):
    nuevo_status = request.form.get('status')
    if nuevo_status in ['recibido','preparando','enviado','en_camino','entregado']:
        actualizar_status_pedido(id, nuevo_status)
        flash('Estado del pedido actualizado. ✅', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/aviso/nuevo', methods=['POST'])
@admin_required
def admin_nuevo_aviso():
    titulo = request.form.get('titulo', '').strip()
    cuerpo = request.form.get('cuerpo', '').strip()
    if titulo and cuerpo:
        crear_aviso(titulo, cuerpo)
        flash('Aviso publicado. ✅', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/aviso/<int:id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_aviso(id):
    toggle_aviso(id)
    return redirect(url_for('admin_panel'))

@app.route('/admin/aviso/<int:id>/eliminar', methods=['POST'])
@admin_required
def admin_eliminar_aviso(id):
    eliminar_aviso(id)
    flash('Aviso eliminado.', 'success')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
