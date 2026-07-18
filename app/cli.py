"""
Custom Flask CLI commands, registered in run.py:

    flask seed-roles      -> creates default roles + permissions
    flask create-admin    -> creates (or resets) the bootstrap admin user
"""
import click

from app.extensions import db
from app.core.security.roles import DEFAULT_ROLE_PERMISSIONS
from app.core.security.password import hash_password


def register_cli(app):
    @app.cli.command("seed-roles")
    def seed_roles():
        """Create the default roles and permissions if they don't already exist."""
        from app.models.role import Role
        from app.models.permission import Permission

        for role_name, perm_codes in DEFAULT_ROLE_PERMISSIONS.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f"Default {role_name} role")
                db.session.add(role)
                db.session.flush()

            permissions = []
            for code in perm_codes:
                if code == "*":
                    continue
                perm = Permission.query.filter_by(code=code).first()
                if not perm:
                    perm = Permission(code=code)
                    db.session.add(perm)
                    db.session.flush()
                permissions.append(perm)
            role.permissions = permissions

        db.session.commit()
        click.echo("Default roles and permissions seeded.")

    @app.cli.command("create-admin")
    @click.option("--username", default="admin")
    @click.option("--password", default="admin123", help="Change this immediately after first login.")
    @click.option("--full-name", default="System Administrator")
    @click.option("--email", default=None)
    def create_admin(username, password, full_name, email):
        """Create (or reset the password of) the bootstrap admin account."""
        from app.models.role import Role
        from app.models.user import User

        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
            click.echo("Run `flask seed-roles` first.")
            return

        user = User.query.filter_by(username=username).first()
        if user:
            user.password_hash = hash_password(password)
            click.echo(f"Password reset for existing admin user '{username}'.")
        else:
            user = User(
                username=username, full_name=full_name, email=email,
                password_hash=hash_password(password), role_id=admin_role.id,
            )
            db.session.add(user)
            click.echo(f"Admin user '{username}' created.")

        db.session.commit()
        click.echo(f"Login with username='{username}' password='{password}' (change it right away).")
