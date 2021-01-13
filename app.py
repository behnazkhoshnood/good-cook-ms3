import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
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


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    recipes = list(mongo.db.recipes.find().sort("recipe_name", 1))
    return render_template("get_recipes.html", recipes=recipes)


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
        return redirect(url_for("profile", username=session["user"]))
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
                return redirect(url_for("profile", username=session["user"]))
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
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


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
    if request.method == "POST":
        todays_date = datetime.today().strftime('%Y-%m-%d')
        recipe = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
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
        recipe_ingredients_without_empty_strings = []
        for string in recipe_ingredients:
            if (string != ""):
                recipe_ingredients_without_empty_strings.append(string)
        cooking_steps = {
            "cooking_steps": request.form.get(
                "cooking_steps[]").split("\n")
        }
        recipe.update(marks)
        recipe.update(recipe_ingredients)
        recipe.update(cooking_steps)
        mongo.db.recipes.insert_one(recipe)
        flash("Your Recipe Successfully Added")
        return redirect(url_for("get_recipes"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    marks = mongo.db.marks.find().sort("mark", 1)
    return render_template(
        "add_recipe.html", categories=categories, marks=marks)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
