from flask import render_template, request, redirect, session
import data_manager
import server
import encrypter
import cryptography

def collect_all_tags_for_questions(questions):
    tags = {}
    for q in questions:
        tags[q["id"]] = data_manager.get_tags_by_question_id(q["id"])
        if tags[q["id"]] is None:
            tags[q["id"]] = []
    return tags


def collect_all_tags_for_one_question(question):
    tags = {}
    question_id = question["id"]
    tags[question_id] = data_manager.get_tags_by_question_id(question_id)
    if tags[question_id] is None:
        tags[question_id] = []
    return tags


def handle_vote_redirect(question_id):
    if request.args.get('page') == 'question':
        return redirect(f'/question/{question_id}?change_views=false')
    key = request.args.get('order_by', 'vote_number')
    order = request.args.get('order_direction', 'desc')
    limit = request.args.get("limit")
    if limit and limit == "true":
        return redirect(f'/?order_by={key}&order_direction={order}')
    return redirect(f'/list?order_by={key}&order_direction={order}')


def redirect_if_main(redirect_to, question_id):
    if redirect_to and redirect_to == "main":
        last_key = request.args.get("order_by")
        last_order = request.args.get("order_direction")
        limit = request.args.get("limit")
        if limit and limit == "true":
            if last_key and last_order:
                return redirect(f"/?order_by={last_key}&order_direction={last_order}#{question_id}")
            return redirect(f"/#{question_id}")
        if last_key and last_order:
            return redirect(f"/list?order_by={last_key}&order_direction={last_order}#{question_id}")
        return redirect(f"/list#{question_id}")
    return redirect(f"/question/{question_id}?change_views=false")


def add_tag_if_get_method(question_id):
    redirect_to = request.args.get("redirect_to")
    all_tags = data_manager.get_all_tag_names()
    tag_names_by_question_id = data_manager.get_tag_names_by_question_id(question_id)
    all_tags = [t for t in all_tags if t not in tag_names_by_question_id]
    if redirect_to and redirect_to == "main":
        limit = request.args.get("limit")
        if limit and limit == "true":
            return render_template("add_tag.html", question_id=question_id, all_tags=all_tags,
                                   redirect_to=redirect_to, limit="true")
        return render_template("add_tag.html", question_id=question_id, all_tags=all_tags,
                               redirect_to=redirect_to)
    return render_template("add_tag.html", question_id=question_id, all_tags=all_tags)


def add_tag_if_post_method(question_id):
    redirect_to = request.args.get("redirect_to")
    all_existing_tags = data_manager.get_all_tag_names()
    existing_tag = request.form.getlist("existing_tag")
    new_tag = request.form["new_tag"]
    new_tags = new_tag.split(server.SEPARATOR)  # default semicolon
    new_tags = [tag.strip() for tag in new_tags if tag.strip()]
    for tag in new_tags:
        if tag and tag not in all_existing_tags:
            data_manager.add_tag_name(tag)
    existing_tag.extend(new_tags)
    existing_tag = list(set(existing_tag))
    tag_names_by_question_id = data_manager.get_tag_names_by_question_id(question_id)
    existing_tag = [tag for tag in existing_tag if tag not in tag_names_by_question_id]
    for i in range(len(existing_tag)):
        tag_id = data_manager.get_tag_id_by_name(existing_tag[i])
        if tag_id:
            data_manager.add_tag_id_to_question_tag(question_id, tag_id)
    return redirect_if_main(redirect_to, question_id)


def is_user_logged_in():
    try:
        return get_user_id(session) >= 1
    except (cryptography.fernet.InvalidToken, KeyError):
        return False


def mark_phrase(results, phrase):
    import re
    for result in results:
        result['title'] = re.sub(re.escape(phrase), f'<mark>{phrase}</mark>', result['title'], flags=re.IGNORECASE)
        result['message'] = re.sub(re.escape(phrase), f'<mark>{phrase}</mark>', result['message'], flags=re.IGNORECASE)


def replacing_special_keys(data_to_replace):
    replaced_data = data_to_replace.replace("\'", "''")
    return replaced_data


def get_user_id(session):
    """Get user id from actual session."""
    try:
        return decrypt_user_id(session['user_id'])
    except:
        return 0


def decrypt_user_id(user_id):
    """Decrypt user id from session."""
    return int(encrypter.decrypt(user_id))


def check_if_owner(record, session):
    """Check is in actual session belong to the record owner."""
    user_id = get_user_id(session)
    return user_id == record['user_id']
