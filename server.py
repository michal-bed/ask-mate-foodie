from flask import Flask, render_template, request, redirect, session, flash
from data_manager import upload_file
from werkzeug.security import generate_password_hash, check_password_hash
import data_manager
import time
import re
import encrypter
import datetime
import session_common
import utils
import bonus_questions


UPLOAD_FOLDER = './static/upload'
SEPARATOR = ";"

app = Flask(__name__)
app.secret_key = 'tojestbardzosekretnasesja'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.before_request
def handle_permanent_session():
    """Automatic logout after 5 minutes of inactivity."""
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)


@app.route("/")
def list_main_page():
    """Display first five questions on the page."""
    is_logged = utils.is_user_logged_in()
    key = "submission_time"
    order = "desc"
    questions = data_manager.get_all_questions(key, order, 5)
    tags = utils.collect_all_tags_for_questions(questions)
    return render_template('list.html', questions_data=questions, last_key=key, last_order=order, tags=tags, url='/',
                           limit="true", logged=is_logged, user_id=utils.get_user_id(session))


@app.route('/list')
def list_main_page_with_all_questions():
    """Display all questions on the page."""
    key = request.args.get('order_by', "submission_time")
    order = request.args.get('order_direction', "desc")
    questions = data_manager.get_all_questions(key, order)
    tags = utils.collect_all_tags_for_questions(questions)
    return render_template('list.html', questions_data=questions, logged=utils.is_user_logged_in(),
                           last_key=key, last_order=order, tags=tags, url='/list', user_id=utils.get_user_id(session))


@app.route('/question/<question_id>')
def question(question_id):
    """Display one question with answers."""
    change_views = request.args.get("change_views", True)
    if change_views != "false":
        data_manager.add_views_to_question(question_id)
    selected_question = data_manager.get_one_question(question_id)
    key = request.args.get('order_by', "vote_number")
    order = request.args.get('order_direction', "desc")
    answers = data_manager.get_all_answers_for_question(question_id, key, order)
    tags = utils.collect_all_tags_for_one_question(selected_question)

    return render_template("question.html", session_id=utils.get_user_id(session), logged=utils.is_user_logged_in(),
                           question=selected_question, answers=answers, last_key=key, tags=tags,
                           user_id=utils.get_user_id(session))


@app.route('/bonus-questions')
def bonus_question():
    """Display table with bonus questions"""
    return render_template('bonus_questions.html', logged=utils.is_user_logged_in(),
                           questions=bonus_questions.SAMPLE_QUESTIONS, user_id=utils.get_user_id(session))


@app.route('/question/<question_id>/comments')
def question_with_comments(question_id):
    """Display one answer with all comments."""
    selected_question = data_manager.get_one_question(question_id)
    key = request.args.get('order_by', 'submission_time')
    order = request.args.get('order_direction', "desc")
    comments = data_manager.get_all_comments_for_question(question_id, key, order)
    tags = utils.collect_all_tags_for_one_question(selected_question)
    return render_template("question_with_comments.html", question=selected_question, tags=tags, comments=comments,
                           logged=utils.is_user_logged_in(), last_key=key, session_id=utils.get_user_id(session),
                           user_id=utils.get_user_id(session))


@app.route('/answer/<answer_id>')
def answer(answer_id):
    """Display one answer."""
    selected_answer = data_manager.get_one_answer(answer_id)
    key = request.args.get('order_by', 'submission_time')
    order = request.args.get('order_direction', "desc")
    comments = data_manager.get_all_comments_for_answer(answer_id, key, order)
    return render_template("answer.html", answer=selected_answer, comments=comments, user_id=utils.get_user_id(session),
                           session_id=utils.get_user_id(session), logged=utils.is_user_logged_in(), last_key=key)


@app.route('/question/<question_id>/add-vote')
@session_common.require_login
def add_vote_to_question(question_id):
    """Add vote to the question."""
    voted_question = data_manager.get_one_question(question_id)
    data_manager.increase_reputation(5, voted_question['user_id'])
    data_manager.add_vote('question', question_id)
    return utils.handle_vote_redirect(question_id)


@app.route('/question/<question_id>/remove-vote')
@session_common.require_login
def remove_vote_from_question(question_id):
    """Remove vote from the question."""
    voted_question = data_manager.get_one_question(question_id)
    data_manager.decrease_reputation(2, voted_question['user_id'])
    data_manager.remove_vote('question', question_id)
    return utils.handle_vote_redirect(question_id)


@app.route('/answer/<answer_id>/add-vote')
@session_common.require_login
def add_vote_to_answer(answer_id):
    """Add vote to the answer."""
    voted_question = data_manager.get_one_answer(answer_id)
    data_manager.increase_reputation(10, voted_question['user_id'])
    data_manager.add_vote('answer', answer_id)
    if request.args.get('page') == 'answer':
        return redirect(f'/answer/{answer_id}')
    question_id = data_manager.get_question_id_from_answer(answer_id)
    return redirect(f'/question/{question_id}')


@app.route('/answer/<answer_id>/remove-vote')
@session_common.require_login
def remove_vote_from_answer(answer_id):
    """Remove vote from the answer."""
    voted_question = data_manager.get_one_answer(answer_id)
    data_manager.decrease_reputation(2, voted_question['user_id'])
    data_manager.remove_vote('answer', answer_id)
    if request.args.get('page') == 'answer':
        return redirect(f'/answer/{answer_id}')
    question_id = data_manager.get_question_id_from_answer(answer_id)
    return redirect(f'/question/{question_id}')


@app.route('/add-question', methods=['GET', 'POST'])
@session_common.require_login
def add_question():
    """Add new question to the database."""
    if request.method == 'POST':
        data = {'submission_time': time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
                'view_number': 0,
                'vote_number': 0,
                'title': request.form['title'],
                'message': request.form['message'],
                'image': upload_file(request.files['image']),
                'user_id': utils.get_user_id(session)}
        data['message'] = utils.replacing_special_keys(data['message'])
        data['title'] = utils.replacing_special_keys(data['title'])
        question_id = data_manager.add_new_question(data)
        return redirect(f'/question/{question_id}')
    return render_template('add_question.html', user_id=utils.get_user_id(session), logged=utils.is_user_logged_in())


@app.route('/question/<question_id>/edit', methods=["GET", "POST"])
@session_common.require_login
def edit_question(question_id):
    the_question = data_manager.get_one_question(question_id)
    if utils.check_if_owner(the_question, session):
        if request.method == 'GET':
            return render_template('add_question.html', user_id=utils.get_user_id(session),
            logged=utils.is_user_logged_in(), question=the_question)
        if request.method == 'POST':
            data = {'submission_time': time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
                    'view_number': 0,
                    'vote_number': 0,
                    'title': request.form['title'],
                    'message': request.form['message'],
                    'image': upload_file(request.files['image'])}
            data['message'] = data['message'].replace("\'", "''")
            data['title'] = data['title'].replace("\'", "''")
            data_manager.remove_image([the_question])
            data_manager.edit_question(question_id, data)
            return redirect(f'/question/{question_id}')
    flash("You can not edit the question.")
    return redirect('/')


@app.route('/question/<question_id>/delete')
@session_common.require_login
def remove_question(question_id):
    question = data_manager.get_one_question(question_id)
    if utils.check_if_owner(question, session):
        answers_images = data_manager.get_all_images_from_question_answers(question_id)
        data_manager.remove_image(answers_images)
        question_image = data_manager.delete_question_by_id(question_id)
        data_manager.remove_file(question_image)
    else:
        flash("You can not remove the question.")
    return redirect("/")


@app.route('/question/<question_id>/new-answer', methods=['GET', 'POST'])
@session_common.require_login
def add_answer(question_id):
    """Add answer to the question and to the database."""
    if request.method == "POST":
        data = {
            "submission_time": time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
            "question_id": question_id,
            "vote_number": 0,
            "message": request.form['message'],
            "image": upload_file(request.files['image']),
            "user_id": utils.get_user_id(session),
            "accepted": 0
        }
        data['message'] = utils.replacing_special_keys(data['message'])
        data_manager.add_new_answer(data)
        return redirect(f'/question/{question_id}')
    if request.method == 'GET':
        the_question = data_manager.get_one_question(question_id)
        return render_template('add_answer.html', logged=utils.is_user_logged_in(), user_id=utils.get_user_id(session),
                               question=the_question)


@app.route('/answer/<answer_id>/delete')
@session_common.require_login
def remove_answer(answer_id):
    answer = data_manager.get_one_answer(answer_id)
    if utils.check_if_owner(answer, session):
        answer_data = data_manager.delete_answer(answer_id)
        data_manager.remove_file(answer_data['image'])
        return redirect(f"/question/{answer_data['question_id']}")
    flash("You can not remove the answer.")
    return redirect('/')


@app.route('/question/<question_id>/<answer_id>/edit', methods=["GET", "POST"])
@session_common.require_login
def edit_answer(question_id, answer_id):
    the_question = data_manager.get_one_question(question_id)
    the_answer = data_manager.get_one_answer(answer_id)
    if utils.check_if_owner(the_answer, session):
        if request.method == 'GET':
            return render_template('add_answer.html', logged=utils.is_user_logged_in(),
                                   question=the_question, answer=the_answer, user_id=utils.get_user_id(session))
        if request.method == 'POST':
            data = {'submission_time': time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
                    'view_number': 0,
                    'question_id': question_id,
                    'vote_number': 0,
                    'accepted': the_answer['accepted'],
                    'message': request.form['message'],
                    'image': upload_file(request.files['image'])}
            data['message'] = data['message'].replace("\'", "''")
            data_manager.edit_answer(answer_id, data)
            return redirect(f'/question/{question_id}#{answer_id}')
    flash("You can not edit the answer.")
    return redirect('/')


@app.route('/question/<question_id>/<comment_id>/edit-comment', methods=["GET", "POST"])
@session_common.require_login
def edit_comment_to_question(question_id, comment_id):
    the_question = data_manager.get_one_question(question_id)
    the_comment = data_manager.get_one_comment(comment_id)[0]
    if utils.check_if_owner(the_comment, session):
        if request.method == 'GET':
            return render_template('add_comment.html', question=the_question, comment=the_comment,
                                   comment_message=the_comment['message'], logged=utils.is_user_logged_in(),
                                   header='Question', action='Edit', user_id=utils.get_user_id(session))
        if request.method == 'POST':
            data = {'question_id': question_id, 'message': request.form['comment'],
                    'submission_time': time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
                    'edited_count': the_comment["edited_count"]+1}

            data_manager.edit_comment(comment_id, data)
            return redirect(f'/question/{question_id}/comments')
    flash("You can not edit the comment.")
    return redirect('/')


@app.route('/answer/<question_id>/<answer_id>/<comment_id>/edit', methods=["GET", "POST"])
@session_common.require_login
def edit_comment_to_answer(answer_id, question_id, comment_id):
    the_answer = data_manager.get_one_answer(answer_id)
    the_comment = data_manager.get_one_comment(comment_id)[0]
    if utils.check_if_owner(the_comment, session):
        if request.method == 'GET':
            return render_template('add_comment.html', answer=the_answer, question=None, comment=the_comment,
                                   comment_message=the_comment['message'], header='Answer',
                                   logged=utils.is_user_logged_in(), action='Edit', user_id=utils.get_user_id(session))
        if request.method == 'POST':
            data = {'question_id': question_id, 'answer_id': answer_id, 'message': request.form['comment'],
                    'submission_time': time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
                    'edited_count': the_comment["edited_count"]+1}

            data_manager.edit_comment(comment_id, data)
            return redirect(f'/answer/{answer_id}#{comment_id}')
    flash("You can not edit the comment.")
    return redirect('/')


@app.route('/question/<question_id>/new-tag', methods=["GET", "POST"])
@session_common.require_login
def add_tags_to_question(question_id):
    if request.method == "GET":
        return utils.add_tag_if_get_method(question_id)
    elif request.method == "POST":
        return utils.add_tag_if_post_method(question_id)


@app.route('/tags')
@session_common.require_login
def display_all_tags():
    all_tags = data_manager.get_tags_and_question_count()
    return render_template('tags.html', logged=utils.is_user_logged_in(), all_tags=all_tags,
                           user_id=utils.get_user_id(session))


@app.route('/question/<question_id>/tag/<tag_id>/delete')
@session_common.require_login
def delete_tag_from_question(question_id, tag_id):
    redirect_to = request.args.get("redirect_to")
    data_manager.remove_tag_id_from_question_tag(question_id, tag_id)
    return utils.redirect_if_main(redirect_to, question_id)


@app.route('/question/<question_id>/new-comment', methods=["GET", "POST"])
@session_common.require_login
def add_comment_to_question(question_id):
    question_to_comment = data_manager.get_one_question(question_id)
    if request.method == 'GET':
        return render_template('add_comment.html', question=question_to_comment,
                               url=f'/question/{question_id}/new-comment', user_id=utils.get_user_id(session),
                               header='Question', logged=utils.is_user_logged_in(), action='Add')
    if request.method == 'POST':
        data = {
            "question_id": question_id,
            "answer_id": 'NULL',
            "message": request.form['comment'],
            "submission_time": time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
            "edited_count": 0,
            "user_id": utils.get_user_id(session)
        }
        data_manager.add_comment(data)
        return redirect(f'/question/{question_id}/comments')


@app.route('/answer/<answer_id>/new-comment', methods=["GET", "POST"])
@session_common.require_login
def add_comment_to_answer(answer_id):
    answer_to_comment = data_manager.get_one_answer(answer_id)
    if request.method == 'GET':
        return render_template('add_comment.html', question=answer_to_comment,
                               url=f'/answer/{answer_id}/new-comment', user_id=utils.get_user_id(session),
                               header='Answer', logged=utils.is_user_logged_in(), action='Add')
    if request.method == 'POST':
        data = {
            "question_id": answer_to_comment['question_id'],
            "answer_id": answer_id,
            "message": request.form['comment'],
            "submission_time": time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple()),
            "edited_count": 0,
            "user_id": utils.get_user_id(session)
        }
        data_manager.add_comment(data)
        return redirect(f'/answer/{answer_id}')


@app.route('/answer/<answer_id>/accept', methods=["GET", "POST"])
@session_common.require_login
def accept_answer(answer_id):
    voted_question = data_manager.get_one_answer(answer_id)
    data_manager.increase_reputation(15, voted_question['user_id'])
    answer_to_accept = data_manager.get_one_answer(answer_id)
    question_of_answer = data_manager.get_one_question(answer_to_accept['question_id'])
    question_user_id = question_of_answer['user_id']
    session_user_id = utils.get_user_id(session)
    state_of_acceptance = int(answer_to_accept['accepted'])
    if session_user_id == question_user_id:
        state_of_acceptance += 1
        answer_to_accept['accepted'] = str(state_of_acceptance % 2)
        data_manager.edit_answer(answer_id, answer_to_accept)
        return redirect(request.referrer)
    flash("You do not have permission to accept answers.")
    return redirect('/')


@app.route('/search')
def search_question():
    key = request.args.get('order_by', "vote_number")
    order = request.args.get('order_direction', "desc")
    search_phrase = request.args.get('search-question')
    search_phrase = utils.replacing_special_keys(search_phrase)
    questions = data_manager.searching_questions_by_phrase(search_phrase)
    utils.mark_phrase(questions, search_phrase)
    tags = utils.collect_all_tags_for_questions(questions)
    return render_template('list.html', questions_data=questions, tags=tags, last_key=key,
                           user_id=utils.get_user_id(session),
                           last_order=order, logged=utils.is_user_logged_in(), url='/search')


@app.route('/comments/<comment_id>/delete')
@session_common.require_login
def remove_one_comment(comment_id):
    comment = data_manager.get_one_comment(comment_id)[0]
    if utils.check_if_owner(comment, session):
        comment_data = data_manager.delete_comment(comment_id)
        question_id = comment_data['question_id']
        answer_id = comment_data['answer_id']
        if not answer_id:
            return redirect(f"/question/{question_id}/comments")
        return redirect(f"/answer/{answer_id}")
    flash("You can not remove the comment")
    return redirect('/')


@app.route('/login', methods=["GET", "POST"])
def login():
    if utils.is_user_logged_in():
        flash("You can not login if you are logged in now.")
        return redirect('/')
    if request.method == 'POST':
        user_name = request.form['user_name']
        password = request.form['password']
        my_user = data_manager.get_one_user(user_name)
        if my_user and check_password_hash(my_user['password'], password):
            session['login'] = encrypter.encrypt('True')
            session['user_name'] = encrypter.encrypt(my_user['user_name'])
            session['user_id'] = encrypter.encrypt(str(my_user['id']))
            session['account_type'] = encrypter.encrypt(my_user['account_type'])
            return redirect("/")
        else:
            return render_template('login.html', logged=utils.is_user_logged_in(),
                                   message='incorrect user name or password')
    return render_template('login.html', logged=utils.is_user_logged_in())


@app.route('/register', methods=["GET", "POST"])
def register():
    if 'login' in session:
        return redirect('/')
    if request.method == 'POST':
        username = request.form['user_name']
        if data_manager.get_one_user(username):
            return render_template('register.html', logged=utils.is_user_logged_in(), message='user already exists')

        mail = request.form['email']
        if not re.match(r'[^@]+@+[^@]+\.[^@]', mail):
            return render_template('register.html', logged=utils.is_user_logged_in(), message='wrong email')

        user_data = {'user_name': request.form['user_name'],
                     'reputation': 0,
                     'account_type': 'basic',
                     'password': generate_password_hash(request.form['password']),
                     'email': request.form['email'],
                     'registration_time': time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().timetuple())}
        data_manager.create_user(user_data)

        return redirect("/login")
    return render_template('register.html', logged=utils.is_user_logged_in())


@app.route('/logout', methods=["GET"])
@session_common.require_login
def logout():
    session.pop('login')
    session.pop('user_name')
    session.pop('user_id')
    session.pop('account_type')
    return render_template('login.html', logged=utils.is_user_logged_in(), message='You are logged out',
                           user_id=utils.get_user_id(session))


########## user page functions ##########


@app.route("/user/<user_id>")
@session_common.require_login
def user_page(user_id):
    # user_id = utils.decrypt_user_id(session.get('user_id'))
    user_data = data_manager.get_user_data(user_id)
    questions_counted = data_manager.get_count_user_questions(user_id)
    answers_counted = data_manager.get_count_user_answers(user_id)
    comments_counted = data_manager.get_count_user_comment(user_id)
    return render_template('user_page.html', questions=questions_counted,
                           answers=answers_counted, comments=comments_counted,
                           user_data=user_data, logged=utils.is_user_logged_in(),
                           user_id=utils.get_user_id(session))


@app.route("/user/questions")
@session_common.require_login
def get_user_questions():
    user_id = utils.decrypt_user_id(session.get('user_id'))
    user_data = data_manager.get_user_data(user_id)
    questions_counted = data_manager.get_count_user_questions(user_id)
    answers_counted = data_manager.get_count_user_answers(user_id)
    comments_counted = data_manager.get_count_user_comment(user_id)
    user_questions = data_manager.get_user_questions(user_id)
    tags = utils.collect_all_tags_for_questions(user_questions)
    return render_template('user_page.html', questions=questions_counted,
                           answers=answers_counted, comments=comments_counted,
                           user_data=user_data, user_questions=user_questions,
                           tags=tags, url="/user/questions", user_id=utils.get_user_id(session))


@app.route("/user/answers")
@session_common.require_login
def get_user_answers():
    user_id = utils.decrypt_user_id(session.get('user_id'))
    user_data = data_manager.get_user_data(user_id)
    questions_counted = data_manager.get_count_user_questions(user_id)
    answers_counted = data_manager.get_count_user_answers(user_id)
    comments_counted = data_manager.get_count_user_comment(user_id)
    user_answers = data_manager.get_user_answers(user_id)
    return render_template('user_page.html', questions=questions_counted,
                           answers=answers_counted, comments=comments_counted,
                           user_data=user_data, user_answers=user_answers,
                           url="/user/answers", user_id=utils.get_user_id(session))


@app.route("/user/comments")
@session_common.require_login
def get_user_comments():
    user_id = utils.decrypt_user_id(session.get('user_id'))
    user_data = data_manager.get_user_data(user_id)
    questions_counted = data_manager.get_count_user_questions(user_id)
    answers_counted = data_manager.get_count_user_answers(user_id)
    comments_counted = data_manager.get_count_user_comment(user_id)
    user_comments = data_manager.get_user_comment(user_id)
    return render_template('user_page.html', questions=questions_counted,
                           answers=answers_counted, comments=comments_counted,
                           user_data=user_data, user_comments=user_comments,
                           url="/user/comments", user_id=utils.get_user_id(session))


@app.route('/users', methods=["GET"])
@session_common.require_login
def all_users():
    users = data_manager.get_all_users()
    return render_template('all_users.html', logged=utils.is_user_logged_in(), users=users,
                           user_id=utils.get_user_id(session))


if __name__ == "__main__":
    app.run(debug=True)
