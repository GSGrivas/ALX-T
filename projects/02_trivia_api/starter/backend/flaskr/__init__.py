"""  
cd backend 
source venv/scripts/activate
export FLASK_APP=flaskr
export FLASK_DEBUG=true
flask run

curl http://localhost:5000/questions
"""

import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, questions):
  try:
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    
    current_questions = questions[start:end]
    formatted_questions = [question.format() for question in current_questions]
    return formatted_questions
  except:
    return None

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)

  @app.after_request
  def after_request(response):
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,true")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

  @app.route("/categories")
  def get_categories():
    
    categories = Category.query.order_by(Category.id).all()
    formatted_categories = [category.format() for category in categories]
    
    return jsonify(
      {
        "success": True,
        "categories": formatted_categories,
        "total_categories": len(Category.query.all())
      }
    )

  @app.route("/questions")
  def retrieve_questions():
    categories = Category.query.order_by(Category.id).all();
    formatted_categories = [category.format() for category in categories]
    questions = Question.query.order_by(Question.id).all();
    current_questions = paginate_questions(request, questions);
    
    if len(current_questions) == 0 :
      abort(404)

    return jsonify(
      {
          "success": True,
          "questions": current_questions,
          "categories": formatted_categories,
          "total_questions": len(Question.query.all()),
      }
    )

  @app.route("/questions/<int:question_id>", methods=["DELETE"])
  def delete_question(question_id):
    question = Question.query.filter(Question.id == question_id).one_or_none()

    if question is None:
        abort(404)

    question.delete()
    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)

    return jsonify(
        {
            "success": True,
            "deleted": question_id,
            "questions": current_questions,
            "total_questions": len(Question.query.all()),
        }
    )

  @app.route("/questions", methods=["POST"])
  def create_question():
    try:
      body = request.get_json()
      new_answer = body.get("answer", None)
      new_category = body.get("category", None)
      new_difficulty = body.get("difficulty", None)
      new_question = body.get("question", None)

      question = Question(
        answer=new_answer, 
        category=new_category, 
        difficulty=new_difficulty, 
        question=new_question
      )
      question.insert()

      questions = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, questions)


      return jsonify(
          {
              "success": True,
              "created": question.id,
              "questions": current_questions,
              "total_questions": len(Question.query.all())
          }
      )
    except:
        abort(422)

  @app.route("/questions/searches", methods=["POST"])
  def search_question():
    body = request.get_json()
    search = body.get("searchTerm")
    questions = {
      Question.query.order_by(Question.id)
      .filter(Question.question
      .ilike('%{}%'.format(search))).all()
    }
    formatted_questions = [question.format() for question in questions]

    if len(formatted_questions) == 0:
      abort(404)

    return jsonify(
    {
      "success": True,
      "questions": formatted_questions,
      "total_questions": len(formatted_questions),
    })

  @app.route("/categories/<int:category_id>/questions", methods=["GET"])
  def get_category_questions(category_id):
    category_id = int(category_id) + 1
    questions = Question.query.filter(Question.category==str(category_id)).all();
    formatted_questions = [question.format() for question in questions]
    current_category = Category.query.filter(Category.id == category_id).first()

    if len(formatted_questions) == 0:
      abort(404)
    elif current_category == None:
      abort(404)

    formatted_category = current_category.format()

    return jsonify(
    {
      "success": True,
      "questions": formatted_questions,
      "total_questions": len(formatted_questions),
      "current_category": formatted_category
    })

  @app.route("/quizzes", methods=["POST"])
  def quizzes():
    body = request.get_json()
    previous_questions = body.get("previous_questions", None)
    quiz_category = body.get("quiz_category", None)
    currentQuestion = None
    # quiz_category is for some reason being passed as {'type': {'id': 1, 'type': 'Science'}, 'id': '0'} in the getNextQuestion()
    # I had to pass it as quizCategory.type.type and then it works like this
    category = Category.query.filter(Category.type == quiz_category).first()
    if (category == None):
      questions = Question.query.all()
    else:
      questions = Question.query.filter(Question.category == category.id).all()

    if (len(questions) < 1):
      abort(404)

    for prevQuestion in previous_questions:
      for question in questions:
        if question.id == prevQuestion:
          questions.remove(question);


    if (len(questions) > len(previous_questions)):
      question = random.choice(questions)
      currentQuestion = question.format()

    return jsonify(
    {
      "success": True,
      "currentQuestion": currentQuestion
    })
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
      return (
          jsonify({"success": False, "error": 404, "message": "resource not found"}),
          404,
      )

  @app.errorhandler(422)
  def unprocessable(error):
      return (
          jsonify({"success": False, "error": 422, "message": "unprocessable"}),
          422,
      )

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

  @app.errorhandler(405)
  def not_found(error):
      return (
          jsonify({"success": False, "error": 405, "message": "method not allowed"}),
          405,
      )
  return app


  

    