from flask import session


class SessionManager:

    def create_session(self, user, role):
        # Clear old session first
        session.clear()

        session["user"] = user
        session["role"] = role
        session["authenticated"] = True
        session.permanent = True

    def get_current_user(self):
        if session.get("authenticated"):
            return {"user": session.get("user"), "role": session.get("role")}
        return None

    def destroy_session(self):
        session.clear()
