from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import session
import os
import global_functions
from classes.user import User

user_accounts = {}
flask_app = Flask('ShoppingList',
                  template_folder="Designs",
                  static_folder='Designs/assets')
flask_app.secret_key = os.urandom(24)


def create_user_account(username=None, password=None, firstname="",
                        lastname=""):
    """This function validates user inputs and
    attempts to create a user
    object.
        :arg
            username (str): A unique name to identify user.
            password (str): A secret phrase to authenticate a user.
            firstname (str): The user's first name.
            lastname (str): The user's last name.

        :returns
            str: if validation fails, otherwise return None.
    """

    if not isinstance(password, str):
        return 'Password provided must be a string'

    if not isinstance(username, str):
        return 'Username must be string'

    if len(password) < 1:
        return 'User must provide a pword'

    if len(username) < 1:
        return 'User must provide a username'

    if not username.isalnum():
        return 'Username should only contain letters and numbers'

    if len(password) < 6:
        return 'Password should have at-least 6 characters'

    if username in user_accounts.keys():
        return "Username " + username + " is already taken. Use a unique" \
                                        " username"

    new_user_account = User(username, password, firstname, lastname)
    user_accounts[username] = new_user_account


def login(username, password):
    """This function authenticates users and creates user sessions.
        :arg
            username (str): A unique name to identify user.
            password (str): A secret phrase to authenticate a user.

        :returns
            error message if validation fails, otherwise return True
    """

    if password is None:
        return 'Password must be provided'

    if username is None:
        return 'Username must be provided'

    if username in user_accounts.keys():
        user_account = user_accounts[username]

        password_hash = global_functions.sha1_hash(password)
        if user_account.password_hash == password_hash:
            session["user_logged_in"] = user_account.username
            return True

    return 'Wrong credentials combination'


def signout():
    """This function clears user session"""
    if "user_logged_in" in session.keys():
        session.pop("user_logged_in")


def current_user_has_shopping_lists():
    """This function checks if the current sessions user has any shopping-lists .
        :returns
            bool: True if user has at-least one shoppinglist
            otherwise returns False
    """
    return len(user_accounts[session["user_logged_in"]].shopping_lists) > 0


def get_shopping_list(shopping_list_id):
    """This function finds a particular shopping-list from
    shoppinglists owned by current
    sessions user.
        :arg
            shopping_list_id (str): A unique identifier for the
            shoppinglist being retrieved.

        :returns
            ShoppingList: if shopping-list has been retrieved,
            otherwise returns None
    """
    # check if current user has any shoppinglists
    if current_user_has_shopping_lists():

        # get shoppinglists owned by current user
        my_shoppinglists = user_accounts[
            session["user_logged_in"]].shopping_lists

        if shopping_list_id in my_shoppinglists.keys():
            return my_shoppinglists[shopping_list_id]


@flask_app.route('/', methods=['GET'])
def index():
    if "user_logged_in" not in session.keys():
        return redirect('/login')

    return redirect('/shopping-list')


@flask_app.route('/signup', methods=['POST', 'GET'])
def create_user():
    if "user_logged_in" in session.keys():
        return redirect('/shopping-list')

    data = {'host_url': request.host_url}

    if request.method == 'GET':
        data['error'] = None
        return render_template('create_account.html', data=data)

    firstname = request.form['firstname']
    lastname = request.form['lastname']
    password = request.form['password']
    username = request.form['username']

    error = create_user_account(
        username.lower().strip(), password, firstname, lastname)

    if error is None:
        # log this user in
        login(username, password)
        return redirect('/shopping-list')

    data['error'] = "*" + str(error) + "*"
    return render_template('create_account.html', data=data)


@flask_app.route('/login', methods=['POST', 'GET'])
def authenticate_user():
    if "user_logged_in" in session.keys():
        return redirect('/shopping-list')

    data = {'host_url': request.host_url}

    if request.method == 'GET':
        data['error'] = None
        return render_template('login.html', data=data)

    password = request.form['password']
    username = request.form['username']

    error = login(username, password)

    if error is not True:
        data['error'] = "*" + str(error) + "*"
        return render_template('login.html', data=data)

    return redirect('/shopping-list')


@flask_app.route('/logout', methods=['GET'])
def end_session():
    signout()
    return redirect('/login')


@flask_app.route('/create/shopping-list', methods=['POST'])
def create_shoppinglist():
    title = request.form['title']
    current_user = user_accounts[session["user_logged_in"]]
    error_msg = current_user.create_shopping_list(title=title.strip())

    # if error message was returned display error
    if error_msg is not None:
        # show shoppinglists page with error message
        return view_shopping_list(message=error_msg)

    # show shoppinglists
    return redirect('/shopping-list')


@flask_app.route('/shopping-list', methods=['GET'])
def view_shopping_list(return_type=None, message=None):
    # assert user is logged in
    if "user_logged_in" not in session.keys():
        return redirect('/login')

    data = dict()
    data['host_url'] = request.host_url
    data['message'] = message
    data['current_users_shopping_lists'] = []

    # check if current user has any shopping_lists
    if current_user_has_shopping_lists():

        # get shopping_lists owned by current user
        count = 1
        current_users_shopping_lists = []
        current_users_shopping_lists_objects = \
            user_accounts[session["user_logged_in"]].shopping_lists.values()
        for shopping_list in current_users_shopping_lists_objects:
            shopping_list_data = global_functions.get_attributes_from_class(
                shopping_list
            )

            shopping_list_data["priority"] = count

            current_users_shopping_lists.append(shopping_list_data)
            count += 1

        data['current_users_shopping_lists'] = current_users_shopping_lists

    if return_type == 'raw':
        # returns raw data (python dictionary)
        return data

    return render_template('shopping-list.html', data=data)


@flask_app.route('/update/shopping-list', methods=['POST'])
def update_shoppinglist():
    identifier = request.form['id']
    title = request.form['title']

    # get selected shoppinglist
    shoppinglist = get_shopping_list(identifier)
    if shoppinglist is not None:

        # validate that no other already existing shoppinglist
        # has the same title
        current_users_shopping_lists_objects = \
            user_accounts[session["user_logged_in"]].shopping_lists.values()
        for shopping_list in current_users_shopping_lists_objects:
            if title.lower().strip() == shopping_list.title.lower():
                error_msg = "Shopping list `" + title + "` already exists"
                return view_shopping_list(message=error_msg)

        shoppinglist.update(title)

    return redirect('/shopping-list')


@flask_app.route('/delete/shopping-list/<shoppinglist_id>', methods=['GET'])
def delete_shoppinglist(shoppinglist_id):
    # get current selected shoppinglist
    shoppinglist = get_shopping_list(shoppinglist_id)
    if shoppinglist is not None:
        del user_accounts[session["user_logged_in"]].shopping_lists[
            shoppinglist_id]

    return redirect('/shopping-list')


@flask_app.route('/shopping-list/<shoppinglist_id>/create', methods=['POST'])
def create_shoppinglist_item(shoppinglist_id):
    item_name = request.form['item']

    # get selected shoppinglist
    shoppinglist = get_shopping_list(shoppinglist_id)

    if shoppinglist is not None:
        error_msg = shoppinglist.add_item(item_name.strip())
        if error_msg is not None:
            return view_shoppinglist_items(shoppinglist_id, error_msg)

    return redirect('/shopping-list/' + shoppinglist_id)


@flask_app.route('/shopping-list/<shoppinglist_id>', methods=['GET'])
def view_shoppinglist_items(shoppinglist_id, message=None):
    data = dict()
    data['host_url'] = request.host_url
    data['current_shoppinglist'] = shoppinglist_id
    data['my_shoppinglists'] = []

    if current_user_has_shopping_lists():

        # get shoppinglists owned by current user
        my_shoppinglists = view_shopping_list('raw')[
            'current_users_shopping_lists']
        data['my_shoppinglists'] = my_shoppinglists

        data['message'] = message

        # get selected shoppinglist
        shoppinglist = get_shopping_list(shoppinglist_id)
        data['current_shoppinglists_title'] = shoppinglist.title

        # get items in selected shopping_list
        shopping_list_items = []
        for item in shoppinglist.items:
            item_data = global_functions.get_attributes_from_class(item)
            shopping_list_items.append(item_data)

        data['my_shoppinglist_items'] = shopping_list_items

    return render_template('shoppinglist_items.html', data=data)


@flask_app.route('/shopping-list/<shoppinglist_id>/update-item',
                 methods=['POST'])
def update_shoppinglist_item(shoppinglist_id):
    item_id = request.form['id']
    name = request.form['name']

    # get items in the selected shopping list
    shoppinglist = get_shopping_list(shoppinglist_id)
    for item in shoppinglist.items:

        # validate no other item has same name
        if item.name.lower() == name.lower().strip():
            error_msg = "Item `" + name + "` already exists"
            return view_shoppinglist_items(shoppinglist_id, message=error_msg)

        if str(item.id) == item_id:
            item.update(name)
            break

    return redirect('/shopping-list/' + shoppinglist_id)


@flask_app.route('/shopping-list/<shoppinglist_id>/delete/<item_id>',
                 methods=['GET'])
def delete_shoppinglist_item(shoppinglist_id, item_id):
    shoppinglist = get_shopping_list(shoppinglist_id)
    if shoppinglist is not None:
        shoppinglist.remove_item(int(item_id))

    return redirect('/shopping-list/' + shoppinglist_id)


if __name__ == "__main__":
    flask_app.run()
