import uuid
import os
from posixpath import join
from psycopg2 import sql
from werkzeug.utils import secure_filename
import database_common

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'static/upload'
dirname = os.path.dirname(__file__)
FOLDER_NAME = os.path.join(dirname, UPLOAD_FOLDER)


@database_common.connection_handler
def get_all_questions(cursor, key, direction, questions_limit=100):
    if key in ('title', 'message'):
        query = """
            SELECT question.*, ask_mate_user.user_name
            FROM question
            INNER JOIN ask_mate_user ON question.user_id = ask_mate_user.id
            ORDER BY LOWER({0}) {1}
            LIMIT {2}""".format(key, direction, questions_limit)
    else:
        query = """
            SELECT question.*, ask_mate_user.user_name
            FROM question
            INNER JOIN ask_mate_user ON question.user_id = ask_mate_user.id
            ORDER BY {0} {1}
            LIMIT {2}""".format(key, direction, questions_limit)
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def get_one_question(cursor, id):
    query = """
        SELECT *
        FROM question
        WHERE id = {0}""".format(id)
    cursor.execute(query)
    return cursor.fetchone()


@database_common.connection_handler
def get_one_answer(cursor, id):
    query = """
        SELECT *
        FROM answer
        WHERE id = {0}""".format(id)
    cursor.execute(query)
    return cursor.fetchone()


@database_common.connection_handler
def get_one_comment(cursor, id):
    query = """
        SELECT *
        FROM comment
        WHERE id = {0}""".format(id)
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def get_all_answers_for_question(cursor, question_id, key, order):
    query = sql.SQL("""
        SELECT answer.*, ask_mate_user.user_name
        FROM answer
        INNER JOIN ask_mate_user ON answer.user_id = ask_mate_user.id
        WHERE question_id = %s
        ORDER BY {key} {order}""").format(key=sql.Identifier(key), order=sql.SQL(order))
    try:
        cursor.execute(query, (int(question_id), ))
    except ValueError:
        pass
    return cursor.fetchall()


@database_common.connection_handler
def get_all_comments_for_answer(cursor, answer_id, key, order):
    query = """
        SELECT comment.*, ask_mate_user.user_name
        FROM comment
        INNER JOIN ask_mate_user ON comment.user_id = ask_mate_user.id
        WHERE answer_id = {0}
        ORDER BY {1} {2}""".format(answer_id, key, order)
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def get_all_comments_for_question(cursor, question_id, key, order):
    query = """
        SELECT comment.*, ask_mate_user.user_name
        FROM comment
        INNER JOIN ask_mate_user ON comment.user_id = ask_mate_user.id
        WHERE question_id = {0} and answer_id is NULL
        ORDER BY {1} {2}""".format(question_id, key, order)
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def get_question_id_from_answer(cursor, answer_id):
    query = """
        SELECT question_id
        FROM answer
        WHERE id = {0} """.format(answer_id)
    cursor.execute(query)
    return cursor.fetchall()[0]['question_id']


@database_common.connection_handler
def add_vote(cursor, type, id):
    query = """
        UPDATE {0}
        SET vote_number = vote_number + 1
        WHERE id = {1} """.format(type, id)
    cursor.execute(query)


@database_common.connection_handler
def remove_vote(cursor, type, id):
    query = """
        UPDATE {0}
        SET vote_number = vote_number - 1
        WHERE id = {1} """.format(type, id)
    cursor.execute(query)



@database_common.connection_handler
def increase_reputation(cursor, increase_amount, id):
    query = """
        UPDATE ask_mate_user
        SET reputation = ask_mate_user.reputation + {0}
        WHERE id = {1} """.format(increase_amount, id)
    cursor.execute(query)


@database_common.connection_handler
def decrease_reputation(cursor, increase_amount, id):
    query = """
        UPDATE ask_mate_user
        SET reputation = ask_mate_user.reputation - {0}
        WHERE id = {1} """.format(increase_amount, id)
    cursor.execute(query)


@database_common.connection_handler
def delete_question_by_id(cursor, question_id):
    answer_id_dict = delete_answer_by_id(question_id)
    answer_id = get_id_from_dict(answer_id_dict)
    delete_comments_by_answer_id_list(answer_id)
    query = f"""
            DELETE FROM comment
            WHERE question_id = '{question_id}';
            DELETE FROM answer
            WHERE question_id = '{question_id}';
            DELETE FROM question_tag
            WHERE question_id = '{question_id}';
            DELETE FROM question
            WHERE id = '{question_id}'
            RETURNING image"""
    cursor.execute(query)
    return cursor.fetchall()[0]['image']


@database_common.connection_handler
def delete_answer_by_id(cursor, question_id):
    query = """
            SELECT id FROM answer
            WHERE question_id = {0}""".format(question_id)
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def get_all_images_from_question_answers(cursor, question_id):
    query = """
            SELECT image FROM answer
            WHERE question_id = {0}""".format(question_id)
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def get_answer_id_by_question_id(cursor, question_id):
    query = """
            SELECT id FROM answer
            WHERE question_id = {0}""".format(question_id)
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def delete_answer(cursor, answer_id):
    query = """
            DELETE FROM answer
            WHERE id = {0}
            RETURNING image, question_id""".format(answer_id)
    cursor.execute(query)
    return cursor.fetchall()[0]


def get_id_from_dict(answer_id_dict):
    id_list = []
    for dictionary in answer_id_dict:
        id_list.append(dictionary['id'])
    return id_list


@database_common.connection_handler
def delete_comments_by_answer_id(cursor, answer_id):
    query = """
            DELETE FROM comment
            WHERE answer_id = {0}
            """.format(answer_id)
    cursor.execute(query)


@database_common.connection_handler
def delete_comment(cursor, comment_id):
    query = """
            DELETE FROM comment
            WHERE id = {0}
            RETURNING answer_id, question_id
            """.format(comment_id)
    cursor.execute(query)
    return cursor.fetchall()[0]


def delete_comments_by_answer_id_list(answer_id):
    for id in answer_id:
        delete_comments_by_answer_id(id)


@database_common.connection_handler
def add_new_question(cursor, data):
    query = """
        INSERT INTO question(submission_time, view_number, vote_number, title, message, user_id, image)
        VALUES ('{0}', {1}, {2}, '{3}', '{4}', {5}, '{6}')
        RETURNING id""".format(data['submission_time'], data['view_number'], data['vote_number'],
                               data['title'], data['message'], data['user_id'], data['image'])
    cursor.execute(query)
    return cursor.fetchall()[0]['id']


@database_common.connection_handler
def add_views_to_question(cursor, question_id):
    query = """
        UPDATE question
        SET view_number = view_number + 1
        WHERE id = %s"""
    try:
        cursor.execute(query, (int(question_id), ))
    except ValueError:
        pass


@database_common.connection_handler
def add_new_answer(cursor, data):
    query = """
        INSERT INTO answer(submission_time, vote_number, question_id, message, user_id, image, accepted)
        VALUES ('{0}', {1}, {2}, '{3}', {4}, '{5}', '0')""".format(data['submission_time'],
                                                                   data['vote_number'],
                                                                   data['question_id'],
                                                                   data['message'],
                                                                   data['user_id'],
                                                                   data['image'])
    cursor.execute(query)


@database_common.connection_handler
def get_all_tag_names(cursor):
    query = """SELECT DISTINCT name from tag;"""
    cursor.execute(query)
    tag_dicts = cursor.fetchall()
    all_tag_names = []
    for tag_dict in tag_dicts:
        all_tag_names.append(tag_dict["name"])

    return all_tag_names


@database_common.connection_handler
def add_tag_name(cursor, tag_name):
    query = """INSERT INTO tag (name)
    VALUES (%s)"""
    cursor.execute(query, (tag_name,))


@database_common.connection_handler
def add_comment(cursor, data):
    query = """INSERT INTO comment(question_id, answer_id, message, submission_time, user_id, edited_count)
    VALUES ({0}, {1}, '{2}', '{3}', {4}, {5})""".format(data['question_id'],
                                                     data['answer_id'],
                                                     data['message'],
                                                     data['submission_time'],
                                                     data['user_id'],
                                                     data['edited_count'])
    cursor.execute(query)


@database_common.connection_handler
def get_tag_id_by_name(cursor, tag_name):
    query = """SELECT id FROM tag
    WHERE name = %s"""
    cursor.execute(query, (tag_name, ))
    tag_id = cursor.fetchone()["id"]
    return tag_id


@database_common.connection_handler
def get_tag_id_by_name(cursor, tag_name):
    query = """SELECT id FROM tag
    WHERE name = %s"""
    cursor.execute(query, (tag_name, ))
    tag_id = cursor.fetchone()["id"]
    return tag_id


@database_common.connection_handler
def add_tag_id_to_question_tag(cursor, question_id, tag_id):
    query = """INSERT INTO question_tag (question_id, tag_id)
    VALUES (%s, %s)"""
    try:
        cursor.execute(query, (int(question_id), int(tag_id)))
    except ValueError:
        pass


@database_common.connection_handler
def remove_tag_id_from_question_tag(cursor, question_id, tag_id):
    query = """DELETE FROM question_tag
    WHERE question_id = %s AND tag_id= %s"""
    try:
        cursor.execute(query, (int(question_id), int(tag_id)))
    except ValueError:
        pass


@database_common.connection_handler
def get_tag_names_by_question_id(cursor, question_id):
    query = """SELECT name FROM 
    ((tag INNER JOIN question_tag ON tag.id = question_tag.tag_id) INNER JOIN question ON question.id = question_tag.question_id) 
    WHERE question_id = %s
    ORDER BY tag.id"""
    try:
        cursor.execute(query, (int(question_id), ))
    except ValueError:
        pass
    tag_dicts = cursor.fetchall()
    tag_names = []
    for tag_dict in tag_dicts:
        tag_names.append(tag_dict["name"])

    return tag_names


@database_common.connection_handler
def get_tags_by_question_id(cursor, question_id):
    query = """SELECT tag_id AS id, name FROM 
    ((tag INNER JOIN question_tag ON tag.id = question_tag.tag_id) INNER JOIN question ON question.id = question_tag.question_id) 
    WHERE question_id = %s
    ORDER BY tag.id"""
    try:
        cursor.execute(query, (int(question_id), ))
    except ValueError:
        pass
    return cursor.fetchall()


@database_common.connection_handler
def get_tags_and_question_count(cursor):
    query = """SELECT name, COUNT(question.id) AS count FROM 
    ((tag INNER JOIN question_tag ON tag.id = question_tag.tag_id) 
    INNER JOIN question ON question.id = question_tag.question_id)
    GROUP BY tag.id
    ORDER BY count DESC, tag.id"""
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def searching_questions_by_phrase(cursor, search_phrase):
    """serching in database question by phrase.
       If user try to hack database safe algoritm starts"""
    if ';' in search_phrase or 'DELETE' in search_phrase or 'SELECT' in search_phrase:
        query = """SELECT *
                   FROM question
                """
    else:
        query = """
                SELECT *
                FROM question
                WHERE lower(message) LIKE '%{0}%'
                OR lower(title) LIKE '%{0}%'
                """.format(search_phrase.lower())
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def edit_question(cursor, question_id, data):
    query = """
        UPDATE question
        SET submission_time = '{0}', view_number = {1}, vote_number = {2}, title = '{3}', 
                                                    message = '{4}', image = '{5}'
        WHERE id = {6}""".format(data['submission_time'], data['view_number'], data['vote_number'],
                                 data['title'], data['message'], data['image'], question_id)
    cursor.execute(query)


@database_common.connection_handler
def edit_answer(cursor, answer_id, data):
    query = """
        UPDATE answer
        SET submission_time = '{0}', vote_number = {1}, question_id = {2},  
                                                    message = '{3}', image = '{4}', accepted = '{5}'
        WHERE id = {6}""".format(data['submission_time'], data['vote_number'], data['question_id'],
                                 data['message'], data['image'], data['accepted'], answer_id)
    cursor.execute(query)


@database_common.connection_handler
def edit_comment(cursor, comment_id, data):
    query = """
        UPDATE comment
        SET question_id = {0}, message = '{1}', submission_time = '{2}',  
                                                    edited_count = {3}
        WHERE id = {4}""".format(data['question_id'], data['message'], data['submission_time'],
                                 data['edited_count'], comment_id)
    cursor.execute(query)


def create_id():
    """Create unique id."""
    return uuid.uuid4().hex


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file(file):
    """Save photo to the database and add it to the answer or question."""
    id = create_id()
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        file.save(join(FOLDER_NAME, str(id) + '.' + extension))
        return 'upload/' + str(id) + '.' + extension
    else:
        return ''


def remove_file(filepath):
    try:
        if filepath:
            os.remove('static/' + filepath)
            print(f'{filepath} removed successfully')
    except OSError as error:
        print(error)
        print('File path cannot be removed')


def remove_image(items: list):
    for item in items:
        remove_file(item["image"])


@database_common.connection_handler
def create_user(cursor, user_data):
    query = """
        INSERT INTO ask_mate_user(user_name, password, registration_time, email, reputation, account_type)
        VALUES(%s,%s,%s,%s,%s,%s)"""
    cursor.execute(query, (user_data['user_name'], user_data['password'], user_data['registration_time'],
                           user_data['email'], user_data['reputation'], user_data['account_type']))


########## One user data ##########


@database_common.connection_handler
def get_one_user(cursor, user_name):
    query = """
    SELECT *
    FROM ask_mate_user
    WHERE user_name = %s"""
    cursor.execute(query, (user_name, ))
    return cursor.fetchone()


@database_common.connection_handler
def get_user_data(cursor, user_id):
    query = """
    SELECT user_name, registration_time, reputation
    FROM ask_mate_user
    WHERE id = %s"""
    cursor.execute(query, (int(user_id), ))
    return cursor.fetchone()


@database_common.connection_handler
def get_user_questions(cursor, user_id):
    query = """
    SELECT *
    FROM question
    WHERE user_id = %s"""
    cursor.execute(query, (user_id, ))
    return cursor.fetchall()


@database_common.connection_handler
def get_count_user_questions(cursor, user_id):
    query = """
    SELECT COUNT(title) AS question
    FROM question
    WHERE user_id = %s
    GROUP BY user_id"""
    cursor.execute(query, (user_id, ))
    return cursor.fetchone()


@database_common.connection_handler
def get_user_answers(cursor, user_id):
    query = """
    SELECT *
    FROM answer
    WHERE user_id = %s"""
    cursor.execute(query, (user_id, ))
    return cursor.fetchall()


@database_common.connection_handler
def get_count_user_answers(cursor, user_id):
    query = """
    SELECT COUNT(message) AS answer
    FROM answer
    WHERE user_id = %s
    GROUP BY user_id"""
    cursor.execute(query, (user_id, ))
    return cursor.fetchone()


@database_common.connection_handler
def get_user_comment(cursor, user_id):
    query = """
    SELECT *
    FROM comment
    WHERE user_id = %s"""
    cursor.execute(query, (user_id, ))
    return cursor.fetchall()


@database_common.connection_handler
def get_count_user_comment(cursor, user_id):
    query = """
    SELECT COUNT(message) AS comment
    FROM comment
    WHERE user_id = %s
    GROUP BY user_id"""
    cursor.execute(query, (user_id, ))
    return cursor.fetchone()


##########All users data##########


@database_common.connection_handler
def get_all_users(cursor):
    query = """
    SELECT 
    ask_mate_user.id, 
    ask_mate_user.user_name as user_name, 
    ask_mate_user.registration_time as registration_time,
    ask_mate_user.reputation as reputation,
    count(distinct question.id) as questions,
    count(distinct answer.id) as answers,
    count(distinct comment.id) as comments
    FROM ask_mate_user
    LEFT JOIN question on ask_mate_user.id = question.user_id
    LEFT JOIN answer on ask_mate_user.id = answer.user_id
    LEFT JOIN comment on ask_mate_user.id = comment.user_id
    GROUP BY ask_mate_user.id, user_name, registration_time, reputation;"""
    cursor.execute(query)
    return cursor.fetchall()
