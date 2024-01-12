from flask import Flask, render_template, request, session, redirect, url_for
import flask_bootstrap
import flask
import pymysql
from flask_mysqldb import MySQL
import yaml
import sqlite3
from passlib.hash import sha256_crypt
from datetime import datetime, timedelta, time
import mysql.connector



app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
flask_bootstrap.Bootstrap(app)

# Configure DB
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


@app.route('/provjeri/', methods=['GET', 'POST'])
def p():
    if request.method == 'POST':
        if session.get('brojsasije') is None:
            cur = mysql.connection.cursor()
            brojsasije = request.form.get('brojsasije')
            if cur.execute("SELECT * from automobil where brojsasije = %s", [brojsasije]) > 0:
                automobil  = cur.fetchone()
                flask.flash('Vaše vozilo je registrovano!', 'success')
                return render_template('provjeri.html')
            else:
                flask.flash('Netačan broj šasije!', 'danger')
                return render_template('provjeri.html')
    return render_template("provjeri.html")


@app.route('/osiguranje/')
def osiguranje():
    try:
        cur = mysql.connection.cursor()

        query = "SELECT * FROM osiguranja"
        cur.execute(query)

        data = cur.fetchall()

        cur.close()
        return render_template('osiguranje.html', data=data)
    except ValueError:
        return "Greška"


@app.route('/zaposleni/')
def zaposleni():
    try:
        cur = mysql.connection.cursor()

        query = "SELECT * FROM zaposleni"
        cur.execute(query)

        data = cur.fetchall()

        cur.close()
        return render_template('zaposleni.html', data=data)
    except ValueError:
        return "Greška"



@app.route('/login/', methods=['GET', 'POST'])
def l():
    if request.method == 'POST':
        if session.get('email') is None:
            cur = mysql.connection.cursor()
            email = request.form.get('email')
            sifra = request.form.get('sifra')
            if cur.execute("SELECT * from baza where email = %s", [email]) > 0:
                baza = cur.fetchone()
                if cur.execute("SELECT * from baza where sifra = %s", [sifra]) > 0:
                    # print(user)
                    session['login'] = True
                    session['email'] = baza[0]
                    session['imevlasnika'] = baza[3]
                    session['prezimevlasnika'] = baza[4]
                    session['adresa'] = baza[5]
                    session['termin'] = baza[6]
                    mysql.connection.commit()
                    cur.execute("UPDATE baza SET active = 1 WHERE email = %s ", [email])
                    mysql.connection.commit()
                    # fetch all blogs
                    result_value = cur.execute("SELECT * from baza")
                    if result_value > 0:
                        podaci = cur.fetchall()
                        return render_template("home.html", podaci=podaci)
                    return render_template("home.html")
                else:
                    flask.flash("Neispravna šifra!", "danger")
                return render_template('login.html')
            else:
                flask.flash('Neispravan email!', 'danger')
                return render_template('login.html')
        else:
            cur = mysql.connection.cursor()
            result_value = cur.execute("SELECT * from baza")
            if result_value > 0:
                podaci = cur.fetchall()
                return render_template("home.html", podaci=podaci)
            return render_template("home.html")
    else:
        if session.get('email') is not None:
            cur = mysql.connection.cursor()
            result_value = cur.execute("SELECT * from baza")
            if result_value > 0:
                podaci = cur.fetchall()
                return render_template("home.html", podaci=podaci)
        else:
            return render_template("login.html")
    return render_template("login.html")


@app.route('/home/', methods=['GET', 'POST'])
def home():
    if session.get('email') is None:
        return render_template("login.html")
    else:
        cur = mysql.connection.cursor()
        result_value = cur.execute("SELECT * from baza")
        if result_value > 0:
            podaci = cur.fetchall()
            return render_template("home.html", podaci=podaci)
        return render_template("home.html")


@app.route('/logout/')
def logout():
    if session.get('email') is not None:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE baza  SET active = 0 WHERE email = %s ", [session['email']])
        mysql.connection.commit()
        session.pop('email')
        return render_template('index.html')
    else:
        return render_template('index.html')


@app.route('/')
def index():
    return render_template('index.html')



def radno_vrijeme(termin_str):
    try:
        termin = datetime.strptime(termin_str, '%H:%M').time()
        start_time = datetime.strptime('07:00', '%H:%M').time()
        end_time = datetime.strptime('15:00', '%H:%M').time()
        return start_time <= termin <= end_time
    except ValueError:
        return False


def moguci_termini(termin_str):
    try:
        termin = datetime.strptime(termin_str, '%H:%M').time()
        return termin.minute % 30 == 0
    except ValueError:
        return False


@app.route('/zakazitermin/', methods=['GET', 'POST'])
def z():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        termin_str = request.form.get('termin')
        imevlasnika = request.form.get('imevlasnika')
        prezimevlasnika = request.form.get('prezimevlasnika')
        email = request.form.get('email')
        sifra = request.form.get('sifra')
        adresa = request.form.get('adresa')
        nazivosiguranja = request.form.get('nazivosiguranja')
        kategorija = request.form.get('kategorija')
        vrstagoriva = request.form.get('vrstagoriva')
        termin_confirm = request.form.get('terminConfirm')
        termin_hash = sha256_crypt.hash(termin_str)
        if termin_str == termin_confirm:
            if cur.execute("SELECT * from baza where email = %s", [email]) == 0:
                if radno_vrijeme(termin_str) and moguci_termini(termin_str):
                    cur.execute("INSERT INTO termini(termin, kategorija, vrstagoriva, imevlasnika, prezimevlasnika, email, sifra, nazivosiguranja, adresa) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                  [termin_hash, kategorija, vrstagoriva, imevlasnika, prezimevlasnika, email, sifra, nazivosiguranja, adresa])
                    mysql.connection.commit()
                    cur.close()
                    flask.flash('Zakazali ste Vaš termin!', 'success')
                    return redirect(url_for('zakazitermin'))
                else:
                    flask.flash('Radno vrijeme je od 07.00 do 15.00!', 'danger')
                    return render_template("zakazitermin.html")
            else:
                flask.flash('Email već postoji!', 'danger')
                return render_template("zakazitermin.html")
        else:
            flask.flash('Neispravan termin!', 'danger')
            return render_template("zakazitermin.html")
    return render_template("zakazitermin.html")


@app.errorhandler(404)
def invalid_route(e):
    return render_template("404.html")