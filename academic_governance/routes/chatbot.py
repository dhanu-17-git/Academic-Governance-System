import logging

from flask import Blueprint, request, jsonify, session, render_template
from flask_wtf.csrf import generate_csrf

from academic_governance.services.chatbot_service import (
    ask_ai,
    build_student_context,
)
from academic_governance.services.security import rate_limiter

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")

# Rate limit: 20 requests per 60 seconds per user
CHATBOT_RATE_MAX = 20
CHATBOT_RATE_WINDOW = 60


def get_logged_in_student():
    return session.get("user_email")


@chatbot_bp.route("/", methods=["GET"])
def chatbot_page():
    if not get_logged_in_student():
        return jsonify({"error": "Please log in first."}), 401
    return render_template("chatbot_page.html", csrf_token=generate_csrf())


@chatbot_bp.route("/ask", methods=["POST"])
def ask():
    student_email = get_logged_in_student()
    if not student_email:
        return jsonify(
            {
                "reply": "🔒 Please log in to use the Academic Advisor.",
                "status": "unauthorized",
            }
        ), 401

    # Rate limit chatbot requests to prevent API abuse
    if not rate_limiter.is_allowed(
        "chatbot", student_email, CHATBOT_RATE_MAX, CHATBOT_RATE_WINDOW
    ):
        return jsonify(
            {"reply": "⏳ Too many requests. Please wait a moment.", "status": "rate_limited"}
        ), 429

    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify(
            {"reply": "Please type a message first!", "status": "empty"}
        ), 400

    user_message = data["message"].strip()
    if len(user_message) > 500:
        return jsonify({"reply": "Message too long.", "status": "too_long"}), 400

    try:
        context = build_student_context(student_email)
    except Exception:
        logger.exception("Failed to load academic context for %s", student_email)
        return jsonify(
            {"reply": "⚠️ Could not load academic data. Please try again later.", "status": "db_error"}
        ), 500

    try:
        ai_reply = ask_ai(context, user_message)
        rate_limiter.record("chatbot", student_email)
    except Exception:
        logger.exception("AI API call failed for %s", student_email)
        return jsonify(
            {"reply": "🤖 AI service unavailable.", "status": "ai_error"}
        ), 500

    return jsonify({"reply": ai_reply, "status": "ok"})


@chatbot_bp.route("/suggestions", methods=["GET"])
def get_suggestions():
    suggestions = [
        "Am I at risk of detention in any subject?",
        "Which is my weakest subject?",
        "What's the status of my grievances?",
    ]
    return jsonify({"suggestions": suggestions})
