import os
from flask import (
    Flask, flash, render_template,
    redirect, request,
    session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    # note that we set the 500 status explicitly
    return render_template('500.html'), 500


@app.errorhandler(403)
def page_forbidden(e):
    return render_template('403.html'), 500


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    recipes = list(mongo.db.recipes.find().sort("recipe_name", 1))
    return render_template(
        "get_recipes.html",
        recipes=recipes)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template(
        "get_recipes.html",
        recipes=recipes)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # store form inputs in variables
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmpassword = request.form.get("confirm-password")

        # check if user already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": username.lower()})

        if existing_user:
            flash("username already exists. Please Try again?")
            return redirect(url_for("register"))

        # confirm password
        if password != confirmpassword:
            flash("Passwords do not match, please re-enter")
            return redirect(url_for("register"))

        # register user to mongodb
        register = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "password": generate_password_hash(password)
        }
        mongo.db.users.insert_one(register)

        # push the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Congratulations {}! You have registered successfully."
              .format(first_name.capitalize()))
        return redirect(url_for("get_recipes"))
    return render_template("register.html")


# Log in Function
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if the username already exist in the database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
               existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get(
                      "username").capitalize()))
                return redirect(url_for("get_recipes"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist in the database
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


# Profile page
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    recipes = list(mongo.db.recipes.find().sort("recipe_name", 1))
    categories = mongo.db.categories.find().sort("category_name", 1)

    # grab the session user's username from db
    if session["user"]:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        return render_template(
            "profile.html",
            username=username,
            recipes=recipes,
            categories=categories)


# Log out Function
@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out!")
    session.pop("user")
    return redirect(url_for("login"))


# Add a Recipe Function
@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if session["user"]:
        if request.method == "POST":
            todays_date = datetime.today().strftime('%Y-%m-%d')
            recipe = {
                "category_name": request.form.get("category_name"),
                "recipe_name": request.form.get("recipe_name").lower(),
                "image_url": request.form.get("image_url"),
                "created_by": session["user"],
                "date_added": todays_date
            }
            marks = {
                "marks": request.form.getlist("marks[]")
            }
            recipe_ingredients = {
                "recipe_ingredients": request.form.get(
                    "recipe_ingredients[]").split("\n")
            }
            cooking_steps = {
                "cooking_steps": request.form.get(
                    "cooking_steps[]").split("\n")
            }
            recipe.update(marks)
            recipe.update(recipe_ingredients)
            recipe.update(cooking_steps)
            mongo.db.recipes.insert_one(recipe)
            flash("Your Recipe Successfully Added")
            return redirect(url_for('profile', username=session['user']))

        categories = mongo.db.categories.find().sort("category_name", 1)
        marks = mongo.db.marks.find().sort("mark", 1)
        return render_template(
            "add_recipe.html", categories=categories, marks=marks)


@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    if (session['user'] == 'admin' or
            session['user'] == mongo.db.recipes.created_by):
        mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
        flash("Recipe Successfully Deleted!")
        if 'admin' != mongo.db.recipes.created_by:
            return redirect(url_for('get_recipes'))
        else:
            return redirect(url_for('profile', username=session['user']))
    else:
        return url_for('500.html')


@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        if session['user'] == mongo.db.recipes.created_by:
            todays_date = datetime.today().strftime('%Y-%m-%d')
            submit = {
                "category_name": request.form.get("category_name"),
                "recipe_name": request.form.get("recipe_name").lower(),
                "image_url": request.form.get("image_url"),
                "created_by": session["user"],
                "date_added": todays_date
            }
            marks = {
                "marks": request.form.getlist("marks[]")
            }
            recipe_ingredients = {
                "recipe_ingredients": request.form.get(
                    "recipe_ingredients[]").split("\n")
            }
            cooking_steps = {
                "cooking_steps": request.form.get(
                    "cooking_steps[]").split("\n")
            }
            submit.update(marks)
            submit.update(recipe_ingredients)
            submit.update(cooking_steps)
            mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, submit)
            flash("Your Recipe Successfully Updated")
            return redirect(url_for('profile', username=session['user']))

        recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
        categories = mongo.db.categories.find().sort("category_name", 1)
        marks = mongo.db.marks.find().sort("mark", 1)
        return render_template(
            "edit_recipe.html",
            recipe=recipe,
            categories=categories,
            marks=marks)


@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template(
        "get_categories.html",
        categories=categories)


@app.route("/get_marks")
def get_marks():
    marks = list(mongo.db.marks.find().sort("mark", 1))
    return render_template(
        "get_marks.html",
        marks=marks)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if session["user"] == "admin":
        if request.method == "POST":
            category = {
                "category_name": request.form.get("category_name")
            }
            mongo.db.categories.insert_one(category)
            flash("New Category Added")
            return redirect(url_for('get_categories'))

        return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        if session["user"] == "admin":
            submit = {
                "category_name": request.form.get("category_name")
            }
            mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
            flash("Category Successfully Updated")
            return redirect(url_for('get_categories'))

        category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
        return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    if session["user"] == "admin":
        mongo.db.categories.remove({"_id": ObjectId(category_id)})
        flash("Category Successfully Deleted")
        return redirect(url_for('get_categories'))


@app.route("/add_mark", methods=["GET", "POST"])
def add_mark():
    if session["user"] == "admin":
        if request.method == "POST":
            mark = {
                "mark": request.form.get("mark")
            }
            mongo.db.marks.insert_one(mark)
            flash("New Mark Added")
            return redirect(url_for('get_marks'))

        return render_template("add_mark.html")


@app.route("/edit_mark/<mark_id>", methods=["GET", "POST"])
def edit_mark(mark_id):
    if session["user"] == "admin":
        if request.method == "POST":
            submit = {
                "mark": request.form.get("mark")
            }
            mongo.db.marks.update({"_id": ObjectId(mark_id)}, submit)
            flash("Mark Successfully Updated")
            return redirect(url_for('get_marks'))

        mark = mongo.db.marks.find_one({"_id": ObjectId(mark_id)})
        return render_template("edit_mark.html", mark=mark)


@app.route("/delete_mark/<mark_id>")
def delete_mark(mark_id):
    if session["user"] == "admin":
        mongo.db.marks.remove({"_id": ObjectId(mark_id)})
        flash("Mark Successfully Deleted")
        return redirect(url_for('get_marks'))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
