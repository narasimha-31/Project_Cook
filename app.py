from flask import Flask, render_template, request
import pandas as pd

# Load the dataset
df = pd.read_csv("keywords_recipes.csv")

app = Flask(__name__)

def match_recipes(user_input):
    user_ingredients = [i.strip().lower() for i in user_input.split(",")]

    def score(row):
        all_text = f"{row['Keywords']} {row['Instructions']}".lower()
        matches = [
            word for word in user_ingredients 
            if any(w in all_text for w in [word, word + 's'])  # handle plural
        ]
        return len(matches)

    df['match_score'] = df.apply(score, axis=1)

    # 👇 Add this to compute time in minutes
    def time_to_minutes(time_str):
        import re
        time_str = str(time_str).lower()
        mins = 0
        if "hr" in time_str:
            hr_match = re.search(r"(\d+)\s*hr", time_str)
            if hr_match:
                mins += int(hr_match.group(1)) * 60
        if "min" in time_str:
            min_match = re.search(r"(\d+)\s*min", time_str)
            if min_match:
                mins += int(min_match.group(1))
        return mins

    df['time_mins'] = df['total_time'].apply(time_to_minutes)

    # 👇 Final sorting: match score → rating → time
    matches = df[df['match_score'] > 0].sort_values(
        by=['match_score', 'Rating', 'time_mins'],
        ascending=[False, False, True]
    )

    return matches[['recipe_name', 'total_time', 'Rating', 'Ingredients', 'Instructions']].head(5)

@app.route("/", methods=["GET", "POST"])
def index():
    recipes = []
    ingredients = ""
    ingredient_list = []

    if request.method == "POST":
        if "clear" in request.form:
            return render_template("index.html", recipes=[], ingredients="", ingredient_list=[])
        
        ingredients = request.form.get("ingredients", "")
        ingredient_list = [i.strip().lower() for i in ingredients.split(",")]
        recipes = match_recipes(ingredients).to_dict(orient="records")

    return render_template("index.html", recipes=recipes, ingredients=ingredients, ingredient_list=ingredient_list)

from markupsafe import Markup

@app.template_filter('highlight')
def highlight(text, words):
    if not text:
        return text
    for word in words:
        word = word.strip()
        if word:
            text = text.replace(word, f"<mark>{word}</mark>")
    return Markup(text)


if __name__ == "__main__":
    app.run(debug=True)
