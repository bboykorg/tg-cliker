import psycopg2
from os import environ
from flask import Flask, render_template, request, redirect, url_for, session
import threading
import time
cost_bot = 25000
app = Flask(__name__)

app.secret_key = environ.get("APP_SECRET")

DB_HOST = environ.get('DB_HOST')
DB_NAME = environ.get('DB_NAME')
DB_USER = environ.get('DB_USER')
DB_PASS = environ.get('DB_PASS')

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def update_click_count():
    while True:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT \"ID_user\", \"bot\" FROM \"score\" WHERE \"bot\" = 1")
                users_with_bot = cursor.fetchall()
                for user in users_with_bot:
                    user_id = user[0]
                    cursor.execute("SELECT \"score\", \"ID_improvements\" FROM \"score\" WHERE \"ID_user\" = %s",
                                   (user_id,))
                    result = cursor.fetchone()
                    if result:
                        click_count = result[0]
                        improvement_id = result[1]
                        cursor.execute("SELECT \"add\" FROM \"improvements\" WHERE \"ID\" = %s", (improvement_id,))
                        add_clicks = cursor.fetchone()[0]
                        new_click_count = click_count + add_clicks
                        cursor.execute("UPDATE \"score\" SET \"score\" = %s WHERE \"ID_user\" = %s",
                                       (new_click_count, user_id))
                conn.commit()
        time.sleep(2)  # Обновлять каждые 2 секунды


def update_energy():
    while True:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT \"ID_user\", \"energy\" FROM \"score\"")
                users = cursor.fetchall()
                for user in users:
                    user_id = user[0]

                    cursor.execute(
                        "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\"  WHERE \"ID_user\" = %s",
                        (user_id,))
                    result = cursor.fetchone()
                    if result:
                        energy = result[-1]
                        energy_max = result[1]
                        if energy < energy_max:
                            new_energy = energy + 3
                            cursor.execute("UPDATE \"score\" SET \"energy\" = %s WHERE \"ID_user\" = %s",
                                       (new_energy, user_id))
                conn.commit()
        time.sleep(3)


@app.route("/")
def index():
    user_id = request.args.get('user_id', type=int)
    if "user_id" in session:
        user_id = session['user_id']
    energy = 0
    if user_id is None:
        click_count = 0
        return render_template("index.html", click_count=click_count, energy=energy)
    else:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT \"score\", \"ID_improvements\" FROM \"score\" WHERE \"ID_user\" = %s",
                               (user_id,))
                result = cursor.fetchone()
                cursor.execute(
                    "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"ID_improvements\"  WHERE \"ID_user\" = %s",
                    (user_id,))
                current_energy = cursor.fetchone()
                cursor.execute(
                    "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\" WHERE \"ID_user\" = %s",
                    (user_id,)
                )
                result_energy = cursor.fetchone()
                cursor.execute("SELECT \"bot\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
                result_bot = cursor.fetchone()
                if result and current_energy and result_energy and result_bot:
                    click_count = result[0]
                    improvement_lvl = result[1]
                    a_energy = current_energy[1]
                    energy = result_energy[-1]
                    bot = result_bot[0]
                else:
                    click_count = 1

    return render_template("index.html", click_count=click_count, energy=energy, improvement=improvement_lvl,
                           current_energy=a_energy, bot=bot)


@app.route('/clicker', methods=['post'])
def clicker():
    user_id = request.form.get('user_id', type=int)
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
            result = cursor.fetchone()
            cursor.execute(
                "SELECT * FROM \"improvements\" JOIN \"score\" ON \"improvements\".\"ID\" = \"score\".\"ID_improvements\"  WHERE \"ID_user\" = %s",
                (user_id,))
            result_add = cursor.fetchone()
            if result is not None:
                add = result_add[2]

            if result is None:
                cursor.execute("INSERT INTO \"score\" (\"ID_user\", \"score\") VALUES (%s, %s)", (user_id, 1))
                click_count = 1
            else:
                click_count = result[0] + add
                cursor.execute(
                    "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\" WHERE \"ID_user\" = %s",
                    (user_id,)
                )
                result_energy = cursor.fetchone()
                energy = result_energy[-1] - add
                if energy >= 0:
                    cursor.execute("UPDATE score SET \"score\" = %s, \"energy\" = %s WHERE \"ID_user\" = %s",
                                   (click_count, energy, user_id))

            conn.commit()
    session['user_id'] = user_id
    return redirect(url_for('index'))


@app.route("/improvements", methods=['get'])
def improvements():
    user_id = request.args.get('user_id', type=int)
    if "user_id" in session:
        user_id = session['user_id']
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM \"improvements\" JOIN \"score\" ON \"improvements\".\"ID\" = \"score\".\"ID_improvements\"  WHERE \"ID_user\" = %s",
                (user_id,))
            result = cursor.fetchone()
            cursor.execute(
                "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\"  WHERE \"ID_user\" = %s",
                (user_id,))
            result_energy = cursor.fetchone()
            if result and result_energy is not None:
                improvement = result[0]
                cost = result[1]
                points = result_energy[8]
                cost_energy = result_energy[2]
            else:
                improvement = None
                cost = "Пользователь не найден или у него нет улучшений"

            if user_id is None:
                click_count = 0
            else:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
                        result = cursor.fetchone()
                        click_count = result[0]
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT \"bot\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
                    result_bot = cursor.fetchone()
                    bot = result_bot[0]
    session['user_id'] = user_id
    return render_template("improvements.html", improvement=improvement, cost=cost, click_count=click_count, bot=bot,
                           points=points, cost_energy=cost_energy)


@app.route('/check_improvements', methods=['post'])
def check_improvements():
    user_id = request.form.get('user_id', type=int)
    if user_id is None:
        return redirect(url_for('improvements'))

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM \"improvements\" JOIN \"score\" ON \"improvements\".\"ID\" = \"score\".\"ID_improvements\" WHERE \"ID_user\" = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return redirect(url_for('improvements'))

            cost = result[1]
            improvement = result[0]
            max_improvement = get_max_improvement()
            if improvement >= max_improvement:
                return redirect(url_for('improvements'))

            cursor.execute("SELECT \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
            result_count = cursor.fetchone()
            if result_count is None:
                return redirect(url_for('improvements'))

            click_count = result_count[0]
            if click_count - cost < 0:
                return redirect(url_for('improvements'))

            cursor.execute(
                "UPDATE \"score\" SET \"score\" = \"score\" - %s, \"ID_improvements\" = \"ID_improvements\" + 1 WHERE \"ID_user\" = %s",
                (cost, user_id)
            )
            conn.commit()

    session['user_id'] = user_id
    return redirect(url_for('improvements'))


def get_max_improvement():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT max(\"ID\") FROM \"improvements\"")
            result = cursor.fetchone()
            if result is None:
                return 0
            return result[0]


@app.route('/toggle_bot', methods=['post'])
def toggle_bot():
    user_id = request.form.get('user_id', type=int)
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Проверка баланса перед покупкой
            cursor.execute("SELECT \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
            result_count = cursor.fetchone()
            if result_count is None or result_count[0] < cost_bot:
                return redirect(url_for('improvements'))
            # Обновление значений в базе данных
            cursor.execute(
                "UPDATE \"score\" SET \"bot\" = 1, \"score\" = \"score\" - %s WHERE \"ID_user\" = %s",
                (cost_bot, user_id,)
            )
            conn.commit()

    session['user_id'] = user_id
    return redirect(url_for('improvements'))


@app.route('/energy', methods=['post'])
def check_energy():
    user_id = request.form.get('user_id', type=int)
    if user_id is None:
        return redirect(url_for('improvements'))
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\"  WHERE \"ID_user\" = %s",
                (user_id,))
            result_energy = cursor.fetchone()
            if result_energy is None:
                return redirect(url_for('improvements'))

            cost = result_energy[2]
            energy = result_energy[0]
            max_improvement = get_max_improvement()
            if energy >= max_improvement:
                return redirect(url_for('improvements'))

            cursor.execute("SELECT \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
            result_count = cursor.fetchone()
            if result_count is None:
                return redirect(url_for('improvements'))

            click_count = result_count[0]
            if click_count - cost < 0:
                return redirect(url_for('improvements'))

            cursor.execute(
                "UPDATE \"score\" SET \"score\" = \"score\" - %s, \"energy_lvl\" = \"energy_lvl\" + 1 WHERE \"ID_user\" = %s",
                (cost, user_id)
            )
            conn.commit()

    session['user_id'] = user_id
    return redirect(url_for('improvements'))

@app.route('/profile')
def profile():
    user_id = request.args.get('user_id', type=int)
    cards = load_inventory(user_id)
    return render_template("profile.html", cards=cards)


def load_inventory(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT \"cards\".* FROM \"cards\" JOIN \"inventory\" ON \"cards\".\"ID\" = \"inventory\".\"ID_card\" WHERE \"inventory\".\"ID_user\" = %s",
                (user_id,))
            result = cursor.fetchall()
    return result

if __name__ == '__main__':
    # Запуск фонового процесса для обновления счетчика кликов
    threading.Thread(target=update_click_count, daemon=True).start()
    threading.Thread(target=update_energy, daemon=True).start()
    app.run(debug=True, port=5001)
