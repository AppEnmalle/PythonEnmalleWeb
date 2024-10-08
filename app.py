from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')  # Usa una clave secreta más segura en producción

creyentes = []  # Asegúrate de tener una lista de creyentes

API_LOGIN_URL = 'https://apirestnodeenmalle.onrender.com/acceso/login'
API_ASISTENCIA_URL = 'https://apirestnodeenmalle.onrender.com/celula/listado'
API_REGISTRO_ASISTENCIA_URL = 'https://apirestnodeenmalle.onrender.com/celula/registro/asistencia/web'
API_REGISTRO_NUEVO_URL = 'https://apirestnodeenmalle.onrender.com/celula/nuevo/creyente'
API_BARRIOS_URL = 'https://apirestnodeenmalle.onrender.com/celula/listado/sector'
API_CONTROL_REGISTRO_ASISTENCIA_URL = 'https://apirestnodeenmalle.onrender.com/celula/control/registro/asistencia'
API_URL_LISTADO = 'https://apirestnodeenmalle.onrender.com/celula/listado/integrantes'
API_URL_ACTUALIZACION = 'https://apirestnodeenmalle.onrender.com/celula/actualizacion/creyente'
API_URL_CONSULTA = 'https://apirestnodeenmalle.onrender.com/celula/consulta/creyente'
API_UPDATE_CREYENTE_URL = 'https://apirestnodeenmalle.onrender.com/celula/actualizacion/creyente'

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

# Ruta para asistencia
@app.route('/asistencia', methods=['POST', 'GET'])
def asistencia():
    if 'user' not in session:
        return redirect(url_for('login'))


    print ("metodo request ", request.method)
    if request.method == 'GET' or request.method == 'POST':
        #lider = request.form.get('lider')
        lider = session['user']['lider']
        lider_str = str(lider)
        request.method = 'POST'
        #print ("metodo request JJJJ", request.method)

        response = requests.post(API_ASISTENCIA_URL, json={'lider': lider_str})
        #print ("//////////////////////////////////")
        #print (lider)
        #print (response)

        if response.status_code == 200:
            asistencia_data = response.json()

            # Verificar si la respuesta está vacía
            if not asistencia_data:
                # Si no hay datos, redirige con un mensaje
                return render_template('asistencia.html', mensaje='Usted ya registró la asistencia esta semana.')

            # Formatear las fechas
            for item in asistencia_data:
                # Convertir de ISO 8601 a datetime y luego a formato d-m-Y
                item['fecha_nac'] = datetime.strptime(item['fecha_nac'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d-%m-%Y')

            total_items = len(asistencia_data)
            return render_template('asistencia.html', asistencia=asistencia_data, total_items=total_items, mensaje=None)
        else:
            return "Error al obtener asistencia", response.status_code

    return render_template('asistencia.html', mensaje=None)


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
    #print (trama)

    # Enviar la trama a la API de registro de asistencia
    response = requests.post(API_REGISTRO_ASISTENCIA_URL, json={'trama': trama})
    #print (response.status_code)
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

@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    if 'user' not in session:
        return redirect(url_for('login'))

    lider = session['user']['lider']
    sexo = session['user']['sexo']

    # Obtener los datos de barrios y sectores desde la API
    response = requests.get(API_BARRIOS_URL)
    if response.status_code == 200:
        barrios_data = response.json()
    else:
        barrios_data = []

    if request.method == 'POST':
        datos = {
            'cedula_identidad': request.form.get('cedula_identidad'),
            'primer_nombre': request.form.get('primer_nombre'),
            'segundo_nombre': request.form.get('segundo_nombre'),
            'apellido_paterno': request.form.get('apellido_paterno'),
            'apellido_materno': request.form.get('apellido_materno'),
            'fecha_nacimiento': request.form.get('fecha_nacimiento'),
            'estado_civil': request.form.get('estado_civil'),
            'sexo': sexo,
            'barrio': request.form.get('barrio'),  # Aquí se enviará el id del barrio seleccionado
            'calle_principal': request.form.get('calle_principal'),
            'calle_secundaria': request.form.get('calle_secundaria'),
            'numero_casa': request.form.get('numero_casa'),
            'telefono_casa': request.form.get('telefono_casa'),
            'telefono_oficina': request.form.get('telefono_oficina'),
            'telefono_celular': request.form.get('telefono_celular'),
            'id_lider': lider,
            'invitado_x': request.form.get('invitado_x')
        }

        try:
            response = requests.post(API_REGISTRO_NUEVO_URL, json=datos)
            response.raise_for_status()

            if response.status_code == 200:
                return render_template('nuevo.html', mensaje='Registro guardado correctamente.', barrios=barrios_data)
            else:
                return render_template('nuevo.html', mensaje='Error al guardar el registro.', error=response.text, barrios=barrios_data)
        except requests.RequestException as e:
            return render_template('nuevo.html', mensaje='Error al enviar la solicitud.', error=str(e), barrios=barrios_data)

    return render_template('nuevo.html', barrios=barrios_data)

  

@app.route('/estadistica')
def estadistica():
    return render_template('estadistica.html')

@app.route('/cumpleaños')
def cumpleaños():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    return render_template('cumpleaños.html', user=user)


@app.route('/validacionasistencia', methods=['GET', 'POST'])
def validacionasistencia():
    #print("Entro////////AQUI")
    #print(request.method)
    
    if request.method == 'POST':
        # Obtener datos de la sesión
        lider = session.get('user', {}).get('lider')
        celula = session.get('user', {}).get('celula')
        
        if lider is None or celula is None:
            return "Error: Datos de sesión incompletos", 400

        lider_str = str(lider)
        celula_str = str(celula)
        #print("Lider:", lider_str)
        #print("Celula:", celula_str)

        try:
            response = requests.post(API_CONTROL_REGISTRO_ASISTENCIA_URL, json={'lider': lider_str, 'celula': celula_str})
            response.raise_for_status()
            #print(response)
            data = response.json()
            #print("Datos recibidos de la API:", data)
            
            if isinstance(data, list):
                if len(data) == 0:
                    #print("Fecha está vacía, redirigiendo a asistencia")
                    return redirect(url_for('asistencia'))
                else:
                    fecha = list(data[0].values())[0]  # Obtén el primer valor del primer diccionario
                    print("Fecha:", fecha)

                    if fecha == "Ene_01_1900":
                        #print("Fecha es 'Ene_01_1900', redirigiendo a menu")
                        return redirect(url_for('menu'))
                    else:
                        return render_template('validacionasistencia.html', fecha=fecha)
            else:
                return "Error: La respuesta de la API no es una lista", 400

        except requests.RequestException as e:
            return f"Error al contactar con la API: {e}"

    return render_template('menu.html')





@app.route('/listado')
def listado():
    lider = session.get('user', {}).get('lider')  # Obtener el valor de 'lider' desde la sesión
    liderstr = str(lider)
    if not lider:
        return "No tienes permiso para ver esta página.", 403  # O redirige a una página de inicio de sesión

    try:
        response = requests.post(API_URL_LISTADO, json={'lider': liderstr})
        response.raise_for_status()  # Lanza un error si el código de estado HTTP es 4xx/5xx
        data = response.json()
        
        #print (data)
        return render_template('listado.html', data=data)
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return "No se pudo obtener datos de la API.", 500
    except ValueError as e:
        print(f"Error al decodificar JSON: {e}")
        return "Error al procesar los datos de la API.", 500
        


@app.route('/ver_foto/<int:id>')
def ver_foto(id):
    #print("ENTRO---------------------------VerFoto")
    #print (id)
    lider = session.get('user', {}).get('lider')
    if not lider:
        return "No tienes permiso para ver esta página.", 403

    try:
        response = requests.post(API_URL_LISTADO, json={'lider': lider})
        response.raise_for_status()
        data = response.json()
        record = next((item for item in data if item[''][0].split(': ')[1] == str(id)), None)
        image_url = record['ImageUrl'] if record else None
        return render_template('ver_foto.html', image_url=image_url)
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return "No se pudo obtener datos de la API.", 500
    except ValueError as e:
        print(f"Error al decodificar JSON: {e}")
        return "Error al procesar los datos de la API.", 500

@app.route('/editar_creyente/<int:id>')
#@app.route('/editar/<id>', methods=['POST'])
def editar_creyente(id):
    idcreyente = str(id)
    # Realizar la solicitud POST a la API
    response = requests.post(API_URL_CONSULTA, json={'creyente': idcreyente})
    data = response.json()
    # Obtener los datos de barrios y sectores desde la API
    response = requests.get(API_BARRIOS_URL)
    if response.status_code == 200:
        barrios_data = response.json()
    else:
        barrios_data = []
    # Renderizar la plantilla con los datos obtenidos
    return render_template('editar_creyente.html', data=data, barrios=barrios_data)




@app.route('/guardar', methods=['POST'])
def guardar():
    # Extraer datos del formulario
    id_creyente = request.form.get('id')
    cedula_identidad = request.form.get('cedula_identidad')
    nombre = request.form.get('nombre')
    nombre_s = request.form.get('nombre-s')
    apellido_p = request.form.get('apellido-p')
    apellido_m = request.form.get('apellido-m')
    fecha_nacimiento = request.form.get('fecha_nacimiento')
    estado_civil = request.form.get('estado_civil')
    barrio = request.form.get('barrio')
    calle_principal = request.form.get('calle-principal')
    calle_secundaria = request.form.get('calle-secundaria')
    numero_casa = request.form.get('numero-casa')
    telefono_casa = request.form.get('telefono-casa')
    telefono_oficina = request.form.get('telefono-oficina')
    telefono_movil = request.form.get('telefono-movil')

    # Verificar que todos los campos necesarios estén presentes
    if not all([id_creyente, nombre, apellido_p, fecha_nacimiento]):
        return jsonify({"error": "Por favor, complete todos los campos obligatorios."}), 400

    # Enviar la solicitud POST a la API externa
    try:
        response = requests.post(API_UPDATE_CREYENTE_URL, json={
            'id_creyente': id_creyente,
            'cedula_identidad': cedula_identidad,
            'primer_nombre': nombre,
            'segundo_nombre': nombre_s,
            'apellido_paterno': apellido_p,
            'apellido_materno': apellido_m,
            'fecha_nacimiento': fecha_nacimiento,
            'estado_civil': estado_civil,
            'barrio': barrio,
            'calle_principal': calle_principal,
            'calle_secundaria': calle_secundaria,
            'numero_casa': numero_casa,
            'telefono_casa': telefono_casa,
            'telefono_oficina': telefono_oficina,
            'telefono_celular': telefono_movil
        })

        print("Código de respuesta:", response.status_code)
        print("Contenido de la respuesta:", response.text)

        if response.status_code == 200:
            if 'application/json' in response.headers.get('Content-Type', ''):
                try:
                    response_data = response.json()
                    print("Datos procesados:", response_data)

                    # Validar que 'Respuesta' esté en el primer elemento de la lista
                    if len(response_data) > 0 and 'Respuesta' in response_data[0]:
                        if response_data[0]['Respuesta'] == "OK":
                            return jsonify({"Respuesta": "OK"}), 200  # Devuelve JSON
                        elif response_data[0]['Respuesta'] == "ERROR":
                            return jsonify({"error": 'Error al guardar el registro: ' + response_data[0].get("message", "Error desconocido.")}), 400
                        else:
                            return jsonify({"error": 'Respuesta inesperada de la API: ' + str(response_data)}), 400
                    else:
                        return jsonify({"error": 'La respuesta no contiene el campo "Respuesta".'}), 400
                except ValueError as ve:
                    print("Error de JSON:", ve)
                    return jsonify({"error": 'Error al procesar la respuesta de la API.'}), 500
            else:
                return jsonify({"error": 'La respuesta no es de tipo JSON.'}), 500
        else:
            return jsonify({"error": 'Error en la solicitud: ' + str(response.status_code)}), response.status_code

    except requests.exceptions.HTTPError as http_err:
        return jsonify({"error": 'Error en la solicitud HTTP: ' + str(http_err)}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": 'Error de conexión: ' + str(e)}), 500
    except Exception as e:
        return jsonify({"error": 'Error inesperado: ' + str(e)}), 500


    # Redirigir a la plantilla con mensaje de error
    # return redirect(url_for('editar_creyente', id=id_creyente))









if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Usa el puerto proporcionado por el entorno
    app.run(host='0.0.0.0', port=port, debug=False)  # Desactiva el modo debug para producción
