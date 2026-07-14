"""bootstrap default group

Revision ID: 6186d6d560b8
Revises: 041ccdc22962
Create Date: 2026-07-14 00:17:28.814645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6186d6d560b8'
down_revision: Union[str, None] = '041ccdc22962'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Bootstrap the default group for existing users.
    
    This migration is idempotent and safe to re-run.
    It creates:
    1. A shared workspace for the default group
    2. The default group itself
    3. Group memberships for all existing users
    """
    
    # Get connection for executing raw SQL
    conn = op.get_bind()
    
    # Check if default group already exists
    result = conn.execute(
        sa.text("SELECT id FROM groups WHERE name = 'Default Group' LIMIT 1")
    )
    existing_group = result.fetchone()
    
    if existing_group is None:
        # Step 1: Create shared workspace for default group
        # Get the first admin user as owner, or first user if no admin
        result = conn.execute(
            sa.text("""
                SELECT id FROM users 
                WHERE 'admin' = ANY(roles) 
                ORDER BY id LIMIT 1
            """)
        )
        admin_user = result.fetchone()
        
        if admin_user is None:
            # Fallback: use first user
            result = conn.execute(
                sa.text("SELECT id FROM users ORDER BY id LIMIT 1")
            )
            admin_user = result.fetchone()
        
        if admin_user is not None:
            owner_id = admin_user[0]
            
            # Create shared workspace
            result = conn.execute(
                sa.text("""
                    INSERT INTO workspaces (name, owner_id, scope, created_at, updated_at)
                    VALUES ('Default Group Workspace', :owner_id, 'private', now(), now())
                    RETURNING id
                """),
                {"owner_id": owner_id}
            )
            workspace_id = result.fetchone()[0]
            
            # Step 2: Create default group
            result = conn.execute(
                sa.text("""
                    INSERT INTO groups (name, country_code, shared_workspace_id, created_at, updated_at)
                    VALUES ('Default Group', NULL, :workspace_id, now(), now())
                    RETURNING id
                """),
                {"workspace_id": workspace_id}
            )
            group_id = result.fetchone()[0]
            
            # Step 3: Add all existing users to the default group
            # Use INSERT ... ON CONFLICT to make this idempotent
            conn.execute(
                sa.text("""
                    INSERT INTO group_members (group_id, user_id, role, joined_at)
                    SELECT :group_id, u.id, 'member', now()
                    FROM users u
                    WHERE u.deleted_at IS NULL
                    ON CONFLICT (group_id, user_id) DO NOTHING
                """),
                {"group_id": group_id}
            )
            
            # Step 4: Add workspace membership for all users
            # This ensures users can access the shared workspace
            conn.execute(
                sa.text("""
                    INSERT INTO workspace_members (workspace_id, user_id, role)
                    SELECT :workspace_id, u.id, 'editor'
                    FROM users u
                    WHERE u.deleted_at IS NULL
                    ON CONFLICT (workspace_id, user_id) DO NOTHING
                """),
                {"workspace_id": workspace_id}
            )
    

def downgrade() -> None:
    """Remove the default group and its associated workspace.
    
    Note: This will not delete user data, only the group structure.
    """
    conn = op.get_bind()
    
    # Get default group info
    result = conn.execute(
        sa.text("""
            SELECT id, shared_workspace_id 
            FROM groups 
            WHERE name = 'Default Group' 
            LIMIT 1
        """)
    )
    group_info = result.fetchone()
    
    if group_info:
        group_id, workspace_id = group_info[0], group_info[1]
        
        # Delete group members first (FK constraint)
        conn.execute(
            sa.text("DELETE FROM group_members WHERE group_id = :group_id"),
            {"group_id": group_id}
        )
        
        # Delete group
        conn.execute(
            sa.text("DELETE FROM groups WHERE id = :group_id"),
            {"group_id": group_id}
        )
        
        # Delete workspace members
        conn.execute(
            sa.text("DELETE FROM workspace_members WHERE workspace_id = :workspace_id"),
            {"workspace_id": workspace_id}
        )
        
        # Delete workspace
        conn.execute(
            sa.text("DELETE FROM workspaces WHERE id = :workspace_id"),
            {"workspace_id": workspace_id}
        )
