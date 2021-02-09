import os
from flask import (
    Flask, flash, render_template,
    redirect, request,
    session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
if os.path.exists('env.py'):
    import env


app = Flask(__name__)

app.config['MONGO_DBNAME'] = os.environ.get('MONGO_DBNAME')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.secret_key = os.environ.get('SECRET_KEY')

mongo = PyMongo(app)


@app.errorhandler(404)
def page_not_found(e):
    '''
    Displays the page not found error.

    Parameters:
        e (str):The string which is an error.

    Returns:
        Renders the 404.html bearing the error 404.
    '''
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    '''
    Displays the internal server error.

    Parameters:
        e (str):The string which is an error.

    Returns:
        Renders the 500.html bearing the error 500.
    '''
    return render_template('500.html'), 500


@app.errorhandler(403)
def page_forbidden(e):
    '''
    Displays the forbidden page error.

    Parameters:
        e (str):The string which is an error.

    Returns:
        Renders the 403.html bearing the error 403.
    '''
    return render_template('403.html'), 500


@app.route('/')
@app.route('/get_recipes')
def get_recipes():
    '''
    Displays the recipes details.

    Returns:
        Renders the get_recipes.html bearing the recipes details.
    '''
    recipes = list(mongo.db.recipes.find().sort('recipe_name', 1))
    return render_template(
        'get_recipes.html',
        recipes=recipes)


@app.route('/search', methods=['GET', 'POST'])
def search():
    '''
    Displays the search details.

    Returns:
        Renders the get_recipes.html bearing
        the recipes with this search indexes.
    '''
    query = request.form.get('query')
    recipes = list(mongo.db.recipes.find({'$text': {'$search': query}}))
    return render_template(
        'get_recipes.html',
        recipes=recipes)


@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    Displays the register form.

    Returns:
        Redirects to the register.html if username already exists.
        Redirects to the register.html if password confirmation don't match.
        Redirects to get_recipes.html if form filled correctlly.
        Renders register.html page bearing the registerd user details.
    '''
    if request.method == 'POST':
        # store form inputs in variables
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirmpassword = request.form.get('confirm-password')

        # check if user already exists in db
        existing_user = mongo.db.users.find_one(
            {'username': username.lower()})

        if existing_user:
            flash('username already exists. Please Try again?')
            return redirect(url_for('register'))

        # confirm password
        if password != confirmpassword:
            flash('Passwords do not match, please re-enter')
            return redirect(url_for('register'))

        # register user to mongodb
        register = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'password': generate_password_hash(password)
        }
        mongo.db.users.insert_one(register)

        # push the new user into 'session' cookie
        session['user'] = request.form.get('username').lower()
        flash('Congratulations {}! You have registered successfully.'
              .format(first_name.capitalize()))
        return redirect(url_for('get_recipes'))
    return render_template('register.html')


# Log in Function
@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Displays the login form.

    Returns:
        Redirects to get_recipes.html if
        user exists and and username and password are correct.
        Redirects to login.html if invalid password.
        Redirects to login.html if usename doesn't exist.
        Renders the login.html bearing the user details.
    '''
    if request.method == 'POST':
        # check if the username already exist in the database
        existing_user = mongo.db.users.find_one(
            {'username': request.form.get('username').lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
               existing_user['password'], request.form.get('password')):
                session['user'] = request.form.get('username').lower()
                flash('Welcome, {}'.format(request.form.get(
                      'username').capitalize()))
                return redirect(url_for('get_recipes'))
            else:
                # invalid password match
                flash('Incorrect Username and/or Password')
                return redirect(url_for('login'))

        else:
            # username doesn't exist in the database
            flash('Incorrect Username and/or Password')
            return redirect(url_for('login'))

    return render_template('login.html')


# Profile page
@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    '''
    Displays the profile details.

    Parameters:
        username (str):The string which is login name of the user.

    Returns:
        Renders the profile.html page bearing this user's recipes details.
        Renders the 401.html page if user not in session.
    '''
    recipes = list(mongo.db.recipes.find().sort('recipe_name', 1))
    categories = mongo.db.categories.find().sort('category_name', 1)

    # grab the session user's username from db
    if 'user' in session and session['user'] == username:
        username = mongo.db.users.find_one(
            {'username': session['user']})['username']
        return render_template(
            'profile.html',
            username=username,
            recipes=recipes,
            categories=categories)
    else:
        return render_template('401.html')


# Log out Function
@app.route('/logout')
def logout():
    '''
    Logs out this user.

    Returns:
        Redirects to login.html.
    '''
    # remove user from session cookies
    flash('You have been logged out!')
    session.pop('user')
    return redirect(url_for('login'))


# Add a Recipe Function
@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    '''
    Displays the add recipe form.

    Returns:
        Redirects to user's profile.html page if form filled correctlly.
        Renders the add_recipe.html page bearing the added recipe details.
        Renders the 401.html page bearing the
        unauthorized error page if not registered user.
    '''
    if 'user' in session:
        if request.method == 'POST':
            todays_date = datetime.today().strftime('%Y-%m-%d')
            recipe = {
                'category_name': request.form.get('category_name'),
                'recipe_name': request.form.get('recipe_name').lower(),
                'image_url': request.form.get('image_url'),
                'created_by': session['user'],
                'date_added': todays_date
            }
            marks = {
                'marks': request.form.getlist('marks[]')
            }
            recipe_ingredients = {
                'recipe_ingredients': request.form.get(
                    'recipe_ingredients[]').split('\n')
            }
            cooking_steps = {
                'cooking_steps': request.form.get(
                    'cooking_steps[]').split('\n')
            }
            recipe.update(marks)
            recipe.update(recipe_ingredients)
            recipe.update(cooking_steps)
            mongo.db.recipes.insert_one(recipe)
            flash('Your Recipe Successfully Added')
            return redirect(url_for('profile', username=session['user']))

        categories = mongo.db.categories.find().sort('category_name', 1)
        marks = mongo.db.marks.find().sort('mark', 1)
        return render_template(
            'add_recipe.html', categories=categories, marks=marks)
    else:
        return render_template('401.html')


@app.route('/edit_recipe/<recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    '''
    Displays the edit recipe details.

    Parameters:
        recipe_id (str):The string which is this recipe id.

    Returns:
        Renders 404.html bearing a page not found error
        if the recipe doesn't exist.
        Renders 401.html bearing an unauthorized error
        if user in session is not recipe creator.
        redirects to this user profile page if
        user in session is the recipe creator.
        Renders the edit_recipe.html bearing the updated recipe details.
    '''
    recipe = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
    if not recipe:
        return render_template('404.html')
    elif 'user' in session and recipe['created_by'] != session['user']:
        return render_template('401.html')
    elif (request.method == 'POST' and
            'user' in session and
            recipe['created_by'] == session['user']):
        todays_date = datetime.today().strftime('%Y-%m-%d')
        submit = {
            'category_name': request.form.get('category_name'),
            'recipe_name': request.form.get('recipe_name').lower(),
            'image_url': request.form.get('image_url'),
            'created_by': session['user'],
            'date_added': todays_date
        }
        marks = {
            'marks': request.form.getlist('marks[]')
        }
        recipe_ingredients = {
            'recipe_ingredients': request.form.get(
                'recipe_ingredients[]').split('\n')
        }
        cooking_steps = {
            'cooking_steps': request.form.get(
                'cooking_steps[]').split('\n')
        }
        submit.update(marks)
        submit.update(recipe_ingredients)
        submit.update(cooking_steps)
        mongo.db.recipes.update({'_id': ObjectId(recipe_id)}, submit)
        flash('Your Recipe Successfully Updated')
        return redirect(url_for('profile', username=session['user']))
    elif (request.method == 'GET' and
            'user' in session and
            recipe['created_by'] == session['user']):
        categories = mongo.db.categories.find().sort('category_name', 1)
        marks = mongo.db.marks.find().sort('mark', 1)
        return render_template(
            'edit_recipe.html',
            recipe=recipe,
            categories=categories,
            marks=marks)
    else:
        return render_template('401.html')


@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    '''
    The delete recipe function.

    Parameters:
        recipe_id (str):The string which is this recipe id.

    Returns:
        Redirects the admin to which page they are in.
        Redirect the recipe creator to their profile.
        Renders 401.html bearing an unauthorized error if
        user in session is not admin or recipe creator.
    '''
    if 'user' in session:
        username = mongo.db.users.find_one(
                {'username': session['user']})['username']
        recipe = mongo.db.recipes.find(
            {'_id': ObjectId(recipe_id)})
        if session['user'] == 'admin':
            mongo.db.recipes.remove({'_id': ObjectId(recipe_id)})
            flash('Recipe Successfully Deleted!')
            return redirect(request.referrer)

        if (session['user'] == username and
                recipe == recipe):
            mongo.db.recipes.delete_one({'_id': ObjectId(recipe_id)})
            flash('Recipe Successfully Deleted!')
            return redirect(url_for('profile', username=session['user']))
    else:
        return render_template('401.html')


@app.route('/get_categories')
def get_categories():
    '''
    Displays the manage categories page details.

    Returns:
        Renders 401.html if user in session is not admin.
        Renders the get_categories.html bearing the categories details.
    '''
    if ('user' in session and session['user'] == 'admin'):
        categories = list(
            mongo.db.categories.find().sort(
                'category_name', 1))
        return render_template(
            'get_categories.html',
            categories=categories)
    else:
        return render_template('401.html')


@app.route('/get_marks')
def get_marks():
    '''
    Displays the manage marks page details.

    Returns:
        Renders 401.html if user in session is not admin.
        Renders the get_marks.html bearing the marks details.
    '''
    if ('user' in session and session['user'] == 'admin'):
        marks = list(mongo.db.marks.find().sort('mark', 1))
        return render_template(
            'get_marks.html',
            marks=marks)
    else:
        return render_template('401.html')


@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    '''
    Displays the add category page details.

    Returns:
        Renders 401.html if user in session is not admin.
        Redirects to get.categories.html.
        Renders the add_category.html bearing the added category details.
    '''

    if ('user' in session and session['user'] == 'admin'):
        if request.method == 'POST':
            category = {
                'category_name': request.form.get('category_name').lower()
            }
            mongo.db.categories.insert_one(category)
            flash('New Category Added')
            return redirect(url_for('get_categories'))

        if request.method == 'GET':
            return render_template('add_category.html')
    else:
        return render_template('401.html')


@app.route('/edit_category/<category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    '''
    Displays the edit category details.

    Parameters:
        category_id (str):The string which is this category id.

    Returns:
        Renders 401.html if user in session is not admin.
        Redirects to get.categories.html.
        Renders the edit_category.html bearing the updated category details.
    '''

    if ('user' in session and session['user'] == 'admin'):
        if request.method == 'POST':
            submit = {
                'category_name': request.form.get('category_name')
            }
            mongo.db.categories.update({'_id': ObjectId(category_id)}, submit)
            flash('Category Successfully Updated')
            return redirect(url_for('get_categories'))

        if request.method == 'GET':
            category = mongo.db.categories.find_one(
                {'_id': ObjectId(category_id)})
            return render_template('edit_category.html', category=category)
    else:
        return render_template('401.html')


@app.route('/delete_category/<category_id>')
def delete_category(category_id):
    '''
    Deletes this category.

    Parameters:
        category_id (str):The string which is this category id.

    Returns:
        Renders 401.html if user in session is not admin.
        Redirects to get.categories.html.
        Renders the delete_category.html deleting this category.
    '''
    if ('user' in session and session['user'] == 'admin'):
        mongo.db.categories.remove({'_id': ObjectId(category_id)})
        flash('Category Successfully Deleted')
        return redirect(url_for('get_categories'))
    else:
        return render_template('401.html')


@app.route('/add_mark', methods=['GET', 'POST'])
def add_mark():
    '''
    Displays the add mark page details.

    Returns:
        Renders 401.html if user in session is not admin.
        Redirects to get.marks.html.
        Renders the add_mark.html bearing the added mark details.
    '''

    if ('user' in session and session['user'] == 'admin'):
        if request.method == 'POST':
            mark = {
                'mark': request.form.get('mark')
            }
            mongo.db.marks.insert_one(mark)
            flash('New Mark Added')
            return redirect(url_for('get_marks'))

        if request.method == 'GET':
            return render_template('add_mark.html')
    else:
        return render_template('401.html')


@app.route('/edit_mark/<mark_id>', methods=['GET', 'POST'])
def edit_mark(mark_id):
    '''
    Displays the edit mark details.

    Parameters:
        mark_id (str):The string which is this mark id.

    Returns:
        Renders 401.html if user in session is not admin.
        Redirects to get_marks.html bearing all the marks.
        Renders the edit_mark.html bearing the updated mark details.
    '''

    if 'user' in session and session['user'] == 'admin':
        if request.method == 'POST':
            submit = {
                'mark': request.form.get('mark')
            }
            mongo.db.marks.update({'_id': ObjectId(mark_id)}, submit)
            flash('Mark Successfully Updated')
            return redirect(url_for('get_marks'))

        if request.method == 'GET':
            mark = mongo.db.marks.find_one({'_id': ObjectId(mark_id)})
            return render_template('edit_mark.html', mark=mark)
    else:
        return render_template('401.html')


@app.route('/delete_mark/<mark_id>')
def delete_mark(mark_id):
    '''
    Deletes this mark.

    Parameters:
        mark_id (str):The string which is this mark id.

    Returns:
        Renders 401.html if user in session is not admin.
        Redirects to get_marks.html.
    '''
    if 'user' in session and session['user'] == 'admin':
        mongo.db.marks.remove({'_id': ObjectId(mark_id)})
        flash('Mark Successfully Deleted')
        return redirect(url_for('get_marks'))
    else:
        return render_template('401.html')


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)
