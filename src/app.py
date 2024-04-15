from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required

from config import config

from dotenv import load_dotenv

import pandas as pd
from pandas import json_normalize
import requests
from bs4 import BeautifulSoup
import json
import re

# Models:
from models.ModelUser import ModelUser

# Entities:
from models.entities.User import User

#ARC
import arc_data
#OpenAI
import llm

app = Flask(__name__)

load_dotenv()

csrf = CSRFProtect()
db = MySQL(app)
login_manager_app = LoginManager(app)


@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
    	#print(request.form['email'])
    	#print(request.form['password'])
    	user = User(0, request.form['email'], request.form['password'])
    	logged_user = ModelUser.login(db, user)
    	if logged_user != None:
    		if logged_user.password:
    			login_user(logged_user)
    			return redirect(url_for('home'))
    		else:
    			flash("Invalid password...")
    			return render_template('auth/login.html')
    	else:
    		flash("User not found...")
    		return render_template('auth/login.html')
    else:
    	return render_template('auth/login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    return render_template('home.html')


@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada</h1>", 404


@app.route('/extraer_notas', methods=['POST'])
@login_required
def extraer_notas():
    token = request.headers.get('Authorization')
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')

    if fecha_inicio > fecha_fin:
        return jsonify({'error': 'La fecha fin debe ser mayor o igual a la fecha inicio'}), 400

    notas = obtener_notas(fecha_inicio,fecha_fin)
    
    # Almacenar las fechas en la sesión para que persistan
    session['fecha_inicio'] = fecha_inicio
    session['fecha_fin'] = fecha_fin

    print(notas)
    
    return render_template('home.html', notas=notas, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

def obtener_notas(fecha_inicio, fecha_fin):
    # Obtiene endpoint y access_token
    api_url,access_token = arc_data.get_data(fecha_inicio, fecha_fin)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json", 
    }
    response = requests.get(api_url, headers=headers)

    
    if response.status_code == 200:
        data = response.json()
        cuerpo_nota = ''
        # Extraer la lista de elementos de contenido
        content_elements = data.get('content_elements', [])
        # Crear un DataFrame de pandas
        df = pd.json_normalize(content_elements)
        #print(df)
        
        df['publish_date'] = pd.to_datetime(df['publish_date'], errors='coerce', format='mixed')
        df['publish_date'] = pd.to_datetime(df['publish_date']).dt.tz_convert('America/Mexico_City')
        df['publish_date'] = df['publish_date'].dt.strftime('%d-%m-%Y %H:%M')
        df['taxonomy.sections'] = df['taxonomy.sections'].apply(extract_name)        

        df = df.drop(columns=['promo_items.basic.distributor.mode','promo_items.basic.distributor.reference_id','promo_items.basic.type'])
        nuevos_nombres = {'_id':'id','publish_date': 'publish_date', 'headlines.basic': 'titulo', 'canonical_url':'url', 'canonical_website':'website', 'taxonomy.sections':'seccion', 'promo_items.basic.url': 'image_url', 'promo_items.basic.subtitle' : 'image_description' }
        df.rename(columns=nuevos_nombres, inplace=True)

        notas = []
        for index, row in df.iterrows():
            nota = {
                'publish_date': row['publish_date'],
                'seccion': row['seccion'],
                'titulo': row['titulo'],
                'url': row['url'],
                'website': row['website'],
                'image_url':  row['image_url'],
                'image_description': row['image_description'],
                'id': row['id']
            }
            notas.append(nota)
        #df.to_csv('notasall.csv', index = None, header=True, encoding='utf-8', sep='|')
        return notas

def extract_name(entry):
    if isinstance(entry, list):
        # Si es una lista, toma el primer elemento y extrae 'name' si existe
        return entry[0].get('name') if entry else None
    elif isinstance(entry, dict):
        # Si es un diccionario, simplemente extrae 'name' si existe
        return entry.get('name')
    else:
        # Para otros casos, simplemente devuelve el valor original
        return entry

@app.route('/accion_notas', methods=['POST'])
@login_required
def accion_notas():
    fecha_inicio=session.get('fecha_inicio', '')
    fecha_fin=session.get('fecha_fin', '')
    newsletters = []

    notas = obtener_notas(fecha_inicio,fecha_fin)

    notas_seleccionadas = request.form.getlist('notas_seleccionadas')

    j=0
    for nota in notas_seleccionadas:
        #print(nota.split('|'))
        seccion,titulo,url,website,image_url,image_description,nota_id = nota.split('|')

        # Obtiene endpoint y access_token
    
        api_url,access_token = arc_data.get_content(url)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json", 
            }
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            cuerpo_nota = ''
            content = data['content_elements']
            #print(len(content))

            #print(data)

            for i in range(len(content)-1):
                if 'content' in content[i]:
                    if 'Lee también'  not in content[i]['content']:
                        if 'Suscríbete'  not in content[i]['content']:
                            cuerpo_nota = cuerpo_nota + '\n\n' + content[i]['content']

            soup = BeautifulSoup(cuerpo_nota, 'html.parser')
            cuerpo_nota_all = soup.get_text()
            cuerpo_nota = cuerpo_nota_all.strip().replace('\n', ' ')
            #print(cuerpo_nota)

            resumenes,titulos= llm.resume_news(cuerpo_nota)

            resumen1,resumen2,resumen3 = resumenes.split('|')

            title1,title2,title3 = titulos.split('|')
            
            nueva_newsletters = {
                'numero': j,
                'seccion': seccion,            
                'titulo': titulo,
                'titulo1': title1,
                'titulo2': title2,
                'titulo3': title3,
                'url': url,
                'website': website,
                'image_url': image_url,
                'image_description': image_description,
                'resumen1': resumen1,
                'resumen2': resumen2,
                'resumen3': resumen3,
                'id': nota_id
            }
            newsletters.append(nueva_newsletters)
            j=j+1

        else:
            print(response.status_code)
    
    return render_template('home.html', notas=notas, newsletters=newsletters, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

@app.route('/pvnewsletters', methods=['POST'])
@login_required
def pv_newsletter():
    resumen_seleccionado = request.form.get('resumen_seleccionado')

    data = json.loads(resumen_seleccionado)
    df = json_normalize(data)

    df = pd.DataFrame(data)
    
    #print(df)

    newsletters = [] 

    for index, row in df.iterrows():
            nota = {
                'seccion': row['seccion'],            
                'titulo': row['titulo'],
                'url': 'https://www.' + row['website'] + '.com.mx' + row['url'],
                'image_url': row['image_url'],
                'image_description': row['image_description'],
                'resumen': row['resumen'],
                'id': row['id']
            }
            newsletters.append(nota)

    return render_template('newsletter.html', newsletters=newsletters)


@app.route('/register', methods= ["GET", "POST"])
@login_required
def crear_registro():

	cursor = db.connection.cursor()
	sql = "SELECT id, type_name FROM usertype"
	cursor.execute(sql)
	rows = cursor.fetchall()

	df = pd.DataFrame(rows, columns=['id', 'type_name'])

	perfiles = []
	for index, row in df.iterrows():
		perfil = {
		'id': row['id'],
		'type_name': row['type_name']
		}
		perfiles.append(perfil)

	if request.method == 'POST':
		correo=request.form['email']
		password=request.form['password']
		fullname = correo.split('.')[0]
		perfil=request.form['perfil']
		user = User(0, request.form['email'], request.form['password'], fullname, request.form['perfil'])
    	register_user = ModelUser.register(db, user)

		cursor = db.connection.cursor()
		cursor.execute(" SELECT email FROM user")
		row = cursor.fetchone()
		if row != None:
			cursor.execute(" INSERT INTO user (email, password, fullname, id_usertype) VALUES (%s, %s, %s, %s)",(correo,password,fullname,perfil))
			db.connection.commit()
			return render_template('auth/register.html',perfiles=perfiles)
		else:
			return render_template('auth/register.html',perfiles=perfiles)
	else:
		return render_template('auth/register.html',perfiles=perfiles)

if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run()