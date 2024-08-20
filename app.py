from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia esto por una clave secreta más segura

API_LOGIN_URL = 'https://apirestnodeenmalle.onrender.com/acceso/login'
API_ASISTENCIA_URL = 'https://apirestnodeenmalle.onrender.com/celula/listado'
API_REGISTRO_ASISTENCIA_URL = 'https://apirestnodeenmalle.onrender.com/celula/registro/asistencia'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        response = requests.post(API_LOGIN_URL, json={'correo': email, 'password': password})
        
        if response.status_code == 200:
            user_data = response.json()
            if isinstance(user_data, list) and len(user_data) > 0:
                user_data = user_data[0]
                session['user'] = user_data
                return redirect(url_for('menu'))
            else:
                return "Datos de usuario inválidos", 400
        else:
            return "Error de autenticación", 401
    
    return render_template('login.html')

@app.route('/menu')
def menu():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    return render_template('menu.html', user=user)

@app.route('/asistencia', methods=['POST'])
def asistencia():
    if 'user' not in session:
        return redirect(url_for('login'))

    lider = request.form.get('lider')
    response = requests.post(API_ASISTENCIA_URL, json={'lider': lider})

    if response.status_code == 200:
        asistencia_data = response.json()

        # Verificar si la respuesta está vacía
        if not asistencia_data:
            # Si no hay datos, redirige con un mensaje
            return render_template('asistencia.html', mensaje='Usted ya registró la asistencia esta semana.')
        
        total_items = len(asistencia_data)
        return render_template('asistencia.html', asistencia=asistencia_data, total_items=total_items, mensaje=None)
    else:
        return "Error al obtener asistencia", response.status_code


@app.route('/guardar_asistencia', methods=['POST'])
def guardar_asistencia():
    if 'user' not in session:
        return redirect(url_for('login'))

    lider = session['user']['lider']
    celula = session['user']['celula']
    ids_seleccionados = request.form.getlist('asistencia_ids')

    if not ids_seleccionados:
        return redirect(url_for('asistencia'))

    trama = f"{lider};{celula}:{','.join(ids_seleccionados)},"

    # Enviar la trama a la API de registro de asistencia
    response = requests.post(API_REGISTRO_ASISTENCIA_URL, json={'trama': trama})

    if response.status_code == 200:
        # Devuelve un mensaje de éxito en formato JSON
        return {'message': 'Se registró correctamente su asistencia', 'status': 'success'}
    else:
        # Devuelve un mensaje de error en formato JSON
        return {'message': f'Error al enviar la trama: {response.text}', 'status': 'error'}, response.status_code

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
