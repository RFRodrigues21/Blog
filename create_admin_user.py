# create_admin_user.py
import click
from flask.cli import with_appcontext
from app import app, db  # Adjust these import statements based on your project structure
from app import User  # Adjust this import statement based on your project structure

@click.command("create_admin_user")
@with_appcontext
def create_admin_user_command():
    """Create an admin user."""
    with app.app_context():
        # Prompt the user for input
        username = click.prompt("Enter admin username")
        password = click.prompt("Enter admin password", hide_input=True, confirmation_prompt=True)

        # Create the admin user
        admin_user = User(username=username, is_admin=True)
        admin_user.set_password(password)

        # Add and commit to the database
        db.session.add(admin_user)
        db.session.commit()

        click.echo(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    create_admin_user_command()
