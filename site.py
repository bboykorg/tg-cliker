import psycopg2
from os import environ
from flask import Flask, render_template, request, redirect, url_for, session
from apscheduler.schedulers.background import BackgroundScheduler

cost_bot = 25000
app = Flask(__name__)

app.secret_key = environ.get("APP_SECRET")

DB_HOST = environ.get('DB_HOST')
DB_NAME = environ.get('DB_NAME')
DB_USER = environ.get('DB_USER')
DB_PASS = environ.get('DB_PASS')


def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)


@app.route("/info/<user_id>")
def info(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\"  WHERE \"ID_user\" = %s",
                (user_id,))
            result1 = cursor.fetchone()
            cursor.execute(
                "SELECT * FROM \"improvements\" JOIN \"score\" ON \"improvements\".\"ID\" = \"score\".\"ID_improvements\"  WHERE \"ID_user\" = %s",
                (user_id,))
            result2 = cursor.fetchone()
    return {
        "coins": result1[3],
        "energy": result1[-1],
        "max_energy": result1[1],
        "cost_energy": result1[2],
        "id_energy": result1[0],
        "id_improvements": result2[0],
        "add_improvements": result2[2],
        "cost_improvements": result2[1],
        "bot": result2[7],
        "cost_bot": cost_bot

    }


def update_all():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT \"ID_user\" FROM \"score\"")
            result = cursor.fetchall()
            for i in result:
                user_id = i[0]
                cursor.execute("SELECT \"score\", \"ID_improvements\", \"bot\" FROM \"score\" WHERE \"ID_user\" = %s",
                               (user_id,))
                result = cursor.fetchone()
                new_click_count = 0
                if result:
                    click_count = result[0]
                    improvement_id = result[1]
                    bot = result[2]
                    if bot == 1:
                        cursor.execute("SELECT \"add\" FROM \"improvements\" WHERE \"ID\" = %s", (improvement_id,))
                        add_clicks = cursor.fetchone()[0]
                        new_click_count = click_count + add_clicks
                        cursor.execute("UPDATE \"score\" SET \"score\" = %s WHERE \"ID_user\" = %s",
                                       (new_click_count, user_id))
                    cursor.execute(
                        "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\"  WHERE \"ID_user\" = %s",
                        (user_id,))
                    result = cursor.fetchone()
                    new_energy = 0
                    energy_max = 500
                    if result:
                        energy = result[-1]
                        energy_max = result[1]
                        if energy < energy_max:
                            new_energy = energy + 3
                            cursor.execute("UPDATE \"score\" SET \"energy\" = %s WHERE \"ID_user\" = %s",
                                           (new_energy, user_id,))
            conn.commit()


# @app.route("/coins/<user_id>")
# def update_click_count(user_id):
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT \"score\", \"ID_improvements\", \"bot\" FROM \"score\" WHERE \"ID_user\" = %s",
#                            (user_id,))
#             result = cursor.fetchone()
#             new_click_count = 0
#             if result:
#                 click_count = result[0]
#                 improvement_id = result[1]
#                 bot = result[2]
#                 if bot == 1:
#                     cursor.execute("SELECT \"add\" FROM \"improvements\" WHERE \"ID\" = %s", (improvement_id,))
#                     add_clicks = cursor.fetchone()[0]
#                     new_click_count = click_count + add_clicks
#                     cursor.execute("UPDATE \"score\" SET \"score\" = %s WHERE \"ID_user\" = %s",
#                                    (new_click_count, user_id))
#                     conn.commit()
#                     return new_click_count
#             return new_click_count
#
#
# @app.route("/energy/<user_id>")
# def update_energy(user_id):
#     try:
#         with get_db_connection() as conn:
#             with conn.cursor() as cursor:
#                 cursor.execute(
#                     "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\"  WHERE \"ID_user\" = %s",
#                     (user_id,))
#                 result = cursor.fetchone()
#                 new_energy = 0
#                 energy_max = 500
#                 if result:
#                     energy = result[-1]
#                     energy_max = result[1]
#                     if energy < energy_max:
#                         new_energy = energy + 3
#                         cursor.execute("UPDATE \"score\" SET \"energy\" = %s WHERE \"ID_user\" = %s",
#                                        (new_energy, user_id,))
#                         conn.commit()
#                         return f"{str(new_energy)} / {str(energy_max)}"
#                 return f"{str(new_energy)} / {str(energy_max)}"  # Возвращаем значение по умолчанию, если result is None
#
#     except Exception as e:
#         conn.rollback()  # Откатываем изменения в случае ошибки
#         return f"An error occurred: {e}"


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
                if result:
                    click_count = result[0]
                else:
                    click_count = 1

    return render_template("index.html", click_count=click_count)


@app.route('/clicker/<user_id>/<clicks>/<add>')
def clicker(user_id, clicks, add):
    clicks1 = int(clicks)
    add1 = int(add)
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
            result = cursor.fetchone()

            if result is None:
                cursor.execute("INSERT INTO \"score\" (\"ID_user\", \"score\") VALUES (%s, %s)", (user_id, 1))
                click_count = 1
                energy = 0
            else:
                cursor.execute(
                    "SELECT * FROM \"improvements_energy\" JOIN \"score\" ON \"improvements_energy\".\"ID\" = \"score\".\"energy_lvl\" WHERE \"ID_user\" = %s",
                    (user_id,)
                )
                result_energy = cursor.fetchone()

                if result_energy is not None:
                    current_energy = result_energy[-1]

                    max_possible_clicks = min(clicks1, current_energy // add1)

                    if max_possible_clicks > 0:
                        click_count = result[0] + (add1 * max_possible_clicks)
                        new_energy = current_energy - (add1 * max_possible_clicks)

                        cursor.execute("UPDATE score SET \"score\" = %s, \"energy\" = %s WHERE \"ID_user\" = %s",
                                       (click_count, new_energy, user_id))
                        conn.commit()

                        return {
                            "coins": click_count,
                            "energy": new_energy
                        }


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
                energy_lvl = result_energy[8]
                cost_energy = result_energy[2]
            else:
                improvement = 1
                cost = 500
                energy_lvl = 1
                cost_energy = 500

            if user_id is None:
                bot = 0
            else:
                cursor.execute("SELECT \"bot\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
                result_bot = cursor.fetchone()
                bot = result_bot[0]
    session['user_id'] = user_id
    return render_template("improvements.html", improvement=improvement, cost=cost, bot=bot,
                           energy_lvl=energy_lvl, cost_energy=cost_energy)


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
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_all, 'interval', seconds=3)
    scheduler.start()
    app.run(debug=True, port=5001)
