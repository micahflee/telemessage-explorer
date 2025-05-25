#!/usr/bin/env python3
import os
import sys
import psycopg2
import psycopg2.extras

from flask import Flask, jsonify, request
from flask_cors import CORS

# Database connection
print("Connecting to the database...")
sys.stdout.flush()
try:
    conn = psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "54320"),
    )
except psycopg2.OperationalError as e:
    print(f"Error connecting to the database: {e}")
    sys.stdout.flush()
    exit(1)

print("Connected to the database")
sys.stdout.flush()

# Flask app
print("Starting web service")
app = Flask(__name__, static_folder="frontend/dist/assets", static_url_path="/assets")

# Enable CORS only in development mode
if os.environ.get("FLASK_ENV") == "development":
    CORS(app)


select_fields_messages = [
    "id",
    "is_encrypted",
    "has_attachments",
    "subject",
    "text",
    "direction",
    "recipients_count",
    "group_name",
    "network_type",
    "source_type",
    "message_time",
]
select_fields_groups = [
    "id",
    "group_name",
    "source_type",
    "network_type",
    "notes",
]
select_fields_users = [
    "id",
    "type",
    "value",
    "first_name",
    "last_name",
    "notes",
]

select_fields_validations = ["id", "username", "email", "email_domain", "active_identity_provider"]

default_pagination_limit = 500


@app.route("/api/messages", methods=["GET"])
def get_messages():
    """Get all messages, with optional search, sort, order, and extra filters."""
    try:
        limit = int(request.args.get("limit", default_pagination_limit))
        offset = int(request.args.get("offset", 0))
        q = request.args.get("q", "")
        sort = request.args.get("sort", "id")
        if sort not in [
            "id",
            "is_encrypted",
            "has_attachments",
            "subject",
            "text",
            "direction",
            "recipients_count",
            "group_name",
            "network_type",
            "source_type",
            "message_time",
        ]:
            return jsonify({"error": "Invalid sort parameter"}), 400
        sort = f"m.{sort}"
        order = request.args.get("order", "desc")
        if order not in ["asc", "desc"]:
            return jsonify({"error": "Invalid order parameter"}), 400

        hide_encrypted = request.args.get("hide_encrypted", "false").lower() == "true"
        show_attachments = request.args.get("show_attachments", "false").lower() == "true"
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    filters = []
    params = []

    if q:
        filters.append(
            "(m.subject ILIKE %s OR m.text ILIKE %s OR m.group_name ILIKE %s OR m.network_type ILIKE %s OR m.source_type ILIKE %s)"
        )
        params.extend([f"%{q}%"] * 5)
    if hide_encrypted:
        filters.append("m.is_encrypted = FALSE")
    if show_attachments:
        filters.append("m.has_attachments = TRUE")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Total count
        cursor.execute(
            f"SELECT COUNT(*) FROM telemessage_messages m {where_clause}",
            params,
        )
        total = cursor.fetchone()["count"]

        # Paginated messages
        cursor.execute(
            f"""
            SELECT {", ".join([f"m.{f}" for f in select_fields_messages])}
            FROM telemessage_messages m
            {where_clause}
            ORDER BY {sort} {order}
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        messages = cursor.fetchall()

    return jsonify(
        {
            "messages": messages,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }
    )


@app.route("/api/messages/<int:message_id>", methods=["GET"])
def get_message_details(message_id):
    """Get details of a specific message, including the associated group and users."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Get message
        cursor.execute(
            f"SELECT {', '.join(select_fields_messages)}, obj, obj_type FROM telemessage_messages WHERE id = %s",
            (message_id,),
        )
        message = cursor.fetchone()
        if not message:
            return jsonify({"error": "Message not found"}), 404

        # Get associated groups
        cursor.execute(
            f"""
            SELECT 
                {", ".join([f"g.{f}" for f in select_fields_groups])},
                COUNT(DISTINCT gm2.message_id) AS message_count,
                COUNT(DISTINCT ug.user_id) AS user_count
            FROM telemessage_groups g
            JOIN telemessage_groups_messages gm ON g.id = gm.group_id
            LEFT JOIN telemessage_groups_messages gm2 ON g.id = gm2.group_id
            LEFT JOIN telemessage_users_groups ug ON g.id = ug.group_id
            WHERE gm.message_id = %s
            GROUP BY g.id, g.group_name, g.source_type, g.network_type, g.notes
            """,
            (message_id,),
        )
        groups = cursor.fetchall()

        # Get associated users
        cursor.execute(
            f"""
            SELECT
                {", ".join([f"u.{f}" for f in select_fields_users])},
                COUNT(DISTINCT ug.group_id) AS group_count,
                COUNT(DISTINCT um2.message_id) AS message_count
            FROM telemessage_users u
            JOIN telemessage_users_messages um ON u.id = um.user_id
            LEFT JOIN telemessage_users_groups ug ON u.id = ug.user_id
            LEFT JOIN telemessage_users_messages um2 ON u.id = um2.user_id
            WHERE um.message_id = %s
            GROUP BY u.id, u.type, u.value, u.first_name, u.last_name, u.notes
            """,
            (message_id,),
        )
        users = cursor.fetchall()

        # Get associated attachments
        cursor.execute(
            """
            SELECT 
                id, name, content, attach_size, content_type
            FROM telemessage_attachments
            WHERE message_id = %s
            """,
            (message_id,),
        )
        attachments = cursor.fetchall()
        if not attachments:
            attachments = []

    return jsonify(
        {
            "message": message,
            "groups": groups,
            "users": users,
            "attachments": attachments,
        }
    )


@app.route("/api/users", methods=["GET"])
def get_users():
    """Get all users, with optional search, sort, and order."""
    try:
        limit = int(request.args.get("limit", default_pagination_limit))
        offset = int(request.args.get("offset", 0))
        q = request.args.get("q", "")
        sort = request.args.get("sort", "id")
        if sort not in [
            "id",
            "type",
            "value",
            "first_name",
            "last_name",
            "group_count",
            "message_count",
            "notes",
        ]:
            return jsonify({"error": "Invalid sort parameter"}), 400
        if sort not in ["group_count", "message_count"]:
            sort = f"u.{sort}"
        order = request.args.get("order", "desc")
        if order not in ["asc", "desc"]:
            return jsonify({"error": "Invalid order parameter"}), 400
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        if q == "":
            # Get total count for pagination metadata
            cursor.execute("SELECT COUNT(*) FROM telemessage_users")
            total = cursor.fetchone()["count"]

            # Get paginated users
            cursor.execute(
                f"""
                SELECT 
                    {", ".join([f"u.{f}" for f in select_fields_users])},
                    COUNT(DISTINCT ug.group_id) AS group_count,
                    COUNT(DISTINCT um.message_id) AS message_count
                FROM telemessage_users u
                LEFT JOIN telemessage_users_groups ug ON u.id = ug.user_id
                LEFT JOIN telemessage_users_messages um ON u.id = um.user_id
                GROUP BY u.id, u.type, u.value, u.first_name, u.last_name, u.notes
                ORDER BY {sort} {order}
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            users = cursor.fetchall()
        else:
            # Get total count for pagination metadata
            cursor.execute(
                """
                SELECT COUNT(*) FROM telemessage_users
                WHERE
                    type ILIKE %s OR
                    value ILIKE %s OR
                    first_name ILIKE %s OR
                    last_name ILIKE %s OR
                    notes ILIKE %s
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
            )
            total = cursor.fetchone()["count"]

            # Get paginated users
            cursor.execute(
                f"""
                SELECT 
                    {", ".join([f"u.{f}" for f in select_fields_users])},
                    COUNT(DISTINCT ug.group_id) AS group_count,
                    COUNT(DISTINCT um.message_id) AS message_count
                FROM telemessage_users u
                LEFT JOIN telemessage_users_groups ug ON u.id = ug.user_id
                LEFT JOIN telemessage_users_messages um ON u.id = um.user_id
                WHERE
                    u.type ILIKE %s OR
                    u.value ILIKE %s OR
                    u.first_name ILIKE %s OR
                    u.last_name ILIKE %s OR
                    u.notes ILIKE %s
                GROUP BY u.id, u.type, u.value, u.first_name, u.last_name, u.notes
                ORDER BY {sort} {order}
                LIMIT %s OFFSET %s
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", limit, offset),
            )
            users = cursor.fetchall()

    return jsonify(
        {
            "users": users,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }
    )


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user_details(user_id):
    """Get details of a specific user, including the associated group and messages."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Get user
        cursor.execute(
            f"""
            SELECT 
                {", ".join([f"u.{f}" for f in select_fields_users])},
                COUNT(DISTINCT ug.group_id) AS group_count,
                COUNT(DISTINCT um.message_id) AS message_count
            FROM telemessage_users u
            LEFT JOIN telemessage_users_groups ug ON u.id = ug.user_id
            LEFT JOIN telemessage_users_messages um ON u.id = um.user_id
            WHERE u.id = %s
            GROUP BY u.id, u.type, u.value, u.first_name, u.last_name, u.notes
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get associated groups
        cursor.execute(
            f"""
            SELECT 
                {", ".join([f"g.{f}" for f in select_fields_groups])},
                COUNT(DISTINCT gm.message_id) AS message_count,
                COUNT(DISTINCT ug2.user_id) AS user_count
            FROM telemessage_groups g
            JOIN telemessage_users_groups ug ON g.id = ug.group_id
            LEFT JOIN telemessage_groups_messages gm ON g.id = gm.group_id
            LEFT JOIN telemessage_users_groups ug2 ON g.id = ug2.group_id
            WHERE ug.user_id = %s
            GROUP BY g.id, g.group_name, g.source_type, g.network_type, g.notes
            """,
            (user_id,),
        )
        groups = cursor.fetchall()
        if not groups:
            groups = []

        # Get associated messages
        cursor.execute(
            f"""
            SELECT {", ".join([f"m.{f}" for f in select_fields_messages])}
            FROM telemessage_messages m
            JOIN telemessage_users_messages um ON m.id = um.message_id
            WHERE um.user_id = %s
            """,
            (user_id,),
        )
        messages = cursor.fetchall()

    return jsonify(
        {
            "user": user,
            "groups": groups,
            "messages": messages,
        }
    )


@app.route("/api/groups", methods=["GET"])
def get_groups():
    """Get all groups."""
    try:
        limit = int(request.args.get("limit", default_pagination_limit))
        offset = int(request.args.get("offset", 0))
        q = request.args.get("q", "")
        sort = request.args.get("sort", "id")
        if sort not in [
            "id",
            "group_name",
            "source_type",
            "network_type",
            "message_count",
            "user_count",
            "notes",
        ]:
            return jsonify({"error": "Invalid sort parameter"}), 400
        if sort not in ["message_count", "user_count"]:
            sort = f"g.{sort}"
        order = request.args.get("order", "desc")
        if order not in ["asc", "desc"]:
            return jsonify({"error": "Invalid order parameter"}), 400
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        if q == "":
            # Get total count for pagination metadata
            cursor.execute("SELECT COUNT(*) FROM telemessage_groups")
            total = cursor.fetchone()["count"]

            # Get paginated groups
            cursor.execute(
                f"""
                SELECT 
                    {", ".join([f"g.{f}" for f in select_fields_groups])},
                    COUNT(DISTINCT gm.message_id) AS message_count,
                    COUNT(DISTINCT ug.user_id) AS user_count
                FROM telemessage_groups g
                LEFT JOIN telemessage_groups_messages gm ON g.id = gm.group_id
                LEFT JOIN telemessage_users_groups ug ON g.id = ug.group_id
                GROUP BY g.id, g.group_name, g.source_type, g.network_type, g.notes
                ORDER BY {sort} {order}
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            groups = cursor.fetchall()
        else:
            # Get total count for pagination metadata
            cursor.execute(
                """
                SELECT COUNT(*) FROM telemessage_groups
                WHERE
                    group_name ILIKE %s OR
                    source_type ILIKE %s OR
                    network_type ILIKE %s OR
                    notes ILIKE %s
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
            )
            total = cursor.fetchone()["count"]

            # Get paginated groups
            cursor.execute(
                f"""
                SELECT 
                    {", ".join([f"g.{f}" for f in select_fields_groups])},
                    COUNT(DISTINCT gm.message_id) AS message_count,
                    COUNT(DISTINCT ug.user_id) AS user_count
                FROM telemessage_groups g
                LEFT JOIN telemessage_groups_messages gm ON g.id = gm.group_id
                LEFT JOIN telemessage_users_groups ug ON g.id = ug.group_id
                WHERE
                    g.group_name ILIKE %s OR
                    g.source_type ILIKE %s OR
                    g.network_type ILIKE %s OR
                    g.notes ILIKE %s
                GROUP BY g.id, g.group_name, g.source_type, g.network_type, g.notes
                ORDER BY {sort} {order}
                LIMIT %s OFFSET %s
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", limit, offset),
            )
            groups = cursor.fetchall()

    return jsonify(
        {
            "groups": groups,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }
    )


@app.route("/api/groups/<int:group_id>", methods=["GET"])
def get_group_details(group_id):
    """Get details of a specific group, including associated users and messages."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Get group
        cursor.execute(
            f"""
            SELECT 
                {", ".join([f"g.{f}" for f in select_fields_groups])},
                COUNT(DISTINCT gm.message_id) AS message_count,
                COUNT(DISTINCT ug.user_id) AS user_count
            FROM telemessage_groups g
            LEFT JOIN telemessage_groups_messages gm ON g.id = gm.group_id
            LEFT JOIN telemessage_users_groups ug ON g.id = ug.group_id
            WHERE g.id = %s
            GROUP BY g.id, g.group_name, g.source_type, g.network_type, g.notes
            """,
            (group_id,),
        )
        group = cursor.fetchone()

        # Get associated users
        cursor.execute(
            f"""
            SELECT 
                {", ".join([f"u.{f}" for f in select_fields_users])},
                COUNT(DISTINCT ug2.group_id) AS group_count,
                COUNT(DISTINCT um.message_id) AS message_count
            FROM telemessage_users u
            JOIN telemessage_users_groups ug ON u.id = ug.user_id
            LEFT JOIN telemessage_users_groups ug2 ON u.id = ug2.user_id
            LEFT JOIN telemessage_users_messages um ON u.id = um.user_id
            WHERE ug.group_id = %s
            GROUP BY u.id, u.type, u.value, u.first_name, u.last_name, u.notes
            """,
            (group_id,),
        )
        users = cursor.fetchall()

        # Get associated messages
        cursor.execute(
            f"""
            SELECT {", ".join([f"m.{f}" for f in select_fields_messages])}
            FROM telemessage_messages m
            JOIN telemessage_groups_messages gm ON m.id = gm.message_id
            WHERE gm.group_id = %s
            """,
            (group_id,),
        )
        messages = cursor.fetchall()

    if not group:
        return jsonify({"error": "Group not found"}), 404

    return jsonify(
        {
            "group": group,
            "users": users,
            "messages": messages,
        }
    )


@app.route("/api/validations", methods=["GET"])
def get_validations():
    """Get all validations, with optional search, sort, order, and distinct emails. Also includes user_count, message_count, group_count."""
    try:
        limit = int(request.args.get("limit", default_pagination_limit))
        offset = int(request.args.get("offset", 0))
        q = request.args.get("q", "")
        sort = request.args.get("sort", "id")
        if sort not in [
            "id",
            "username",
            "email",
            "email_domain",
            "active_identity_provider",
            "user_count",
            "message_count",
            "group_count",
        ]:
            return jsonify({"error": "Invalid sort parameter"}), 400
        order = request.args.get("order", "desc")
        if order not in ["asc", "desc"]:
            return jsonify({"error": "Invalid order parameter"}), 400

        distinct_emails = request.args.get("distinct_emails", "false").lower() == "true"
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Compose the select fields with aggregates
        agg_select = """
            (
                SELECT COUNT(*) FROM telemessage_users u WHERE u.value = v.username
            ) AS user_count,
            (
                SELECT COUNT(DISTINCT um.message_id)
                FROM telemessage_users u
                LEFT JOIN telemessage_users_messages um ON u.id = um.user_id
                WHERE u.value = v.username
            ) AS message_count,
            (
                SELECT COUNT(DISTINCT ug.group_id)
                FROM telemessage_users u
                LEFT JOIN telemessage_users_groups ug ON u.id = ug.user_id
                WHERE u.value = v.username
            ) AS group_count
        """
        base_select = f"{', '.join([f'v.{f}' for f in select_fields_validations])}, {agg_select}"

        if distinct_emails:
            # Use a subquery to allow arbitrary ordering after deduplication
            subquery = f"""
                SELECT DISTINCT ON (email) {base_select}
                FROM telemessage_validations v
                {
                "WHERE "
                + " OR ".join(
                    [
                        "username ILIKE %s",
                        "email ILIKE %s",
                        "email_domain ILIKE %s",
                        "active_identity_provider ILIKE %s",
                    ]
                )
                if q
                else ""
            }
                ORDER BY email, {sort} {order}
            """
            params = [f"%{q}%"] * 4 if q else []
            # Get total count for pagination metadata
            if q:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT DISTINCT email
                        FROM telemessage_validations
                        WHERE
                            username ILIKE %s OR
                            email ILIKE %s OR
                            email_domain ILIKE %s OR
                            active_identity_provider ILIKE %s
                    ) sub
                    """,
                    params,
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT email FROM telemessage_validations) sub")
            total = cursor.fetchone()["count"]

            # Now apply arbitrary ordering and pagination on the deduplicated set
            cursor.execute(
                f"""
                SELECT * FROM (
                    {subquery}
                ) AS deduped
                ORDER BY {sort} {order}
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            validations = cursor.fetchall()
        else:
            # Get total count for pagination metadata
            if q:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM telemessage_validations
                    WHERE
                        username ILIKE %s OR
                        email ILIKE %s OR
                        email_domain ILIKE %s OR
                        active_identity_provider ILIKE %s
                    """,
                    (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM telemessage_validations")
            total = cursor.fetchone()["count"]

            # Get paginated validations
            if q:
                cursor.execute(
                    f"""
                    SELECT {base_select}
                    FROM telemessage_validations v
                    WHERE
                        username ILIKE %s OR
                        email ILIKE %s OR
                        email_domain ILIKE %s OR
                        active_identity_provider ILIKE %s
                    ORDER BY {sort} {order}
                    LIMIT %s OFFSET %s
                    """,
                    (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", limit, offset),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT {base_select}
                    FROM telemessage_validations v
                    ORDER BY {sort} {order}
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
            validations = cursor.fetchall()

    return jsonify(
        {
            "validations": validations,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }
    )


@app.route("/api/validations/<int:validation_id>", methods=["GET"])
def get_validation(validation_id):
    """Get details of a specific validation by ID, including associated users."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Get the validation row
        cursor.execute(
            f"""
            SELECT {", ".join(select_fields_validations)}
            FROM telemessage_validations
            WHERE id = %s
            """,
            (validation_id,),
        )
        validation = cursor.fetchone()
        if not validation:
            return jsonify({"error": "Validation not found"}), 404

        # Get associated users where validation.username = users.value, including group_count and message_count
        cursor.execute(
            f"""
            SELECT 
                {", ".join([f"u.{f}" for f in select_fields_users])},
                COUNT(DISTINCT ug.group_id) AS group_count,
                COUNT(DISTINCT um.message_id) AS message_count
            FROM telemessage_users u
            LEFT JOIN telemessage_users_groups ug ON u.id = ug.user_id
            LEFT JOIN telemessage_users_messages um ON u.id = um.user_id
            WHERE u.value = %s
            GROUP BY u.id, u.type, u.value, u.first_name, u.last_name, u.notes
            """,
            (validation["username"],),
        )
        users = cursor.fetchall()

    return jsonify({"validation": validation, "users": users})
