import base64
import hashlib
import json
from datetime import datetime, timezone

import psycopg2


def is_probably_base64(s: str) -> bool:
    try:
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False


class TMObjects:
    def __init__(self, filename):
        self.filename = filename

        self.message_raw_objs = []
        self.message_raw_body_objs = []
        self.message_short_objs = []
        self.message_tmobile_objs = []
        self.message_tmobile_body_objs = []

        self.credential_objs = []
        self.validation_full_objs = []
        self.validation_enhance_objs = []

        self.unknown_objs = []
        self.skipped_count = 0

    def extend(self, obj):
        self.message_raw_objs.extend(obj.message_raw_objs)
        self.message_raw_body_objs.extend(obj.message_raw_body_objs)
        self.message_short_objs.extend(obj.message_short_objs)
        self.message_tmobile_objs.extend(obj.message_tmobile_objs)
        self.message_tmobile_body_objs.extend(obj.message_tmobile_body_objs)
        self.credential_objs.extend(obj.credential_objs)
        self.validation_full_objs.extend(obj.validation_full_objs)
        self.validation_enhance_objs.extend(obj.validation_enhance_objs)
        self.unknown_objs.extend(obj.unknown_objs)
        self.skipped_count += obj.skipped_count

    def display(self):
        print(f"[{self.filename}] found {len(self.message_raw_objs):,} raw messages")
        print(
            f"[{self.filename}] found {len(self.message_raw_body_objs):,} raw body messages"
        )
        print(
            f"[{self.filename}] found {len(self.message_short_objs):,} short messages"
        )
        print(
            f"[{self.filename}] found {len(self.message_tmobile_objs):,} T-Mobile messages"
        )
        print(
            f"[{self.filename}] found {len(self.message_tmobile_body_objs):,} T-Mobile body messages"
        )
        print(f"[{self.filename}] found {len(self.credential_objs):,} credentials")
        print(
            f"[{self.filename}] found {len(self.validation_full_objs):,} validation full objects"
        )
        print(
            f"[{self.filename}] found {len(self.validation_enhance_objs):,} validation enhancement objects"
        )
        print(f"[{self.filename}] found {len(self.unknown_objs):,} unknown objects")
        print(f"[{self.filename}] skipped {self.skipped_count:,} objects")

    def sql_insert(
        self,
        conn: psycopg2.extensions.connection,
        insert_sql: str,
        insert_values: tuple,
        select_sql: str = "",
        select_values: tuple = (),
    ) -> int | None:
        insert_sql = insert_sql.strip()
        with conn.cursor() as cursor:
            try:
                # Insert
                cursor.execute(insert_sql, insert_values)
                result = cursor.fetchone()
                id = result[0] if result is not None else None

                if not id and select_sql != "":
                    # If we didn't get an ID, it means the insert failed
                    # because of a conflict. So we need to select the ID
                    # from the database
                    if select_values == ():
                        select_values = insert_values
                    cursor.execute(select_sql, select_values)
                    result = cursor.fetchone()
                    id = result[0] if result is not None else None

                conn.commit()
                return id
            except psycopg2.IntegrityError:
                # Ignore duplicates
                conn.rollback()
                return
            except Exception as e:
                conn.rollback()
                print(
                    f"Error inserting: {e}\n- insert_sql: {insert_sql}\n- insert_values: {insert_values}\n- select_sql: {select_sql}\n- select_values: {select_values}"
                )

    def sql_insert_group(
        self,
        conn: psycopg2.extensions.connection,
        group_name: str,
        source_type: str = "",
        network_type: str = "",
    ) -> int:
        group_id = self.sql_insert(
            conn,
            """
            INSERT INTO telemessage_groups (group_name, source_type, network_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (group_name, source_type, network_type) DO NOTHING
            RETURNING id
            """,
            (
                group_name,
                source_type,
                network_type,
            ),
            "SELECT id FROM telemessage_groups WHERE group_name = %s AND source_type = %s AND network_type = %s",
        )
        return group_id

    def sql_insert_users(
        self,
        conn: psycopg2.extensions.connection,
        users: list,
        message_id: int,
        group_id: int | None = None,
    ):
        for user in users:
            user_id = self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_users (type, value, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (type, value) DO NOTHING
                RETURNING id
                """,
                (
                    str(user["type"]),
                    str(user["value"]),
                    user.get("first_name", ""),
                    user.get("last_name", ""),
                ),
                "SELECT id FROM telemessage_users WHERE type = %s AND value = %s",
                (
                    str(user["type"]),
                    str(user["value"]),
                ),
            )

            # Add the group to the users_groups table
            if group_id is not None and user_id is not None:
                self.sql_insert(
                    conn,
                    """
                    INSERT INTO telemessage_users_groups (user_id, group_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, group_id) DO NOTHING
                    RETURNING id
                    """,
                    (user_id, group_id),
                )

            # Add the message to the users_messages table
            if user_id is not None and message_id is not None:
                self.sql_insert(
                    conn,
                    """
                    INSERT INTO telemessage_users_messages (user_id, message_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, message_id) DO NOTHING
                    RETURNING id
                    """,
                    (user_id, message_id),
                )

        # Insert group message join table
        if group_id is not None and message_id is not None:
            self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_groups_messages (group_id, message_id)
                VALUES (%s, %s)
                ON CONFLICT (group_id, message_id) DO NOTHING
                RETURNING id
                """,
                (group_id, message_id),
            )

    def get_raw_users(self, obj: dict) -> list:
        """
        Get the users from the raw message object
        """
        # Keep track of all of the users in this message
        users = []

        # Extract the sender and sender users
        users.append(
            {
                "type": obj["sender"]["type"],
                "value": obj["sender"]["value"],
            }
        )
        if obj["owner"]["value"] != obj["sender"]["value"]:
            users.append(
                {
                    "type": obj["owner"]["type"],
                    "value": obj["owner"]["value"],
                }
            )

        # Extract the recipients
        for recipient in obj["recipients"]:
            users.append(
                {
                    "type": recipient["type"],
                    "value": recipient["value"],
                }
            )

        # Add names, if available
        if obj["participantEnrichments"] is not None:
            for key, value in obj["participantEnrichments"].items():
                # Key is a JSON string, and value containers firstName and lastName
                key_obj = json.loads(key)

                # Find the user in the list of users
                for user in users:
                    if (
                        user["type"] == key_obj["type"]
                        and user["value"] == key_obj["value"]
                    ):
                        # Add the first name and last name to the user
                        user["first_name"] = value.get("firstName", "")
                        user["last_name"] = value.get("lastName", "")
                        break

        if obj.get("body", {}).get("recipients", None) is not None:
            for recipient in obj["recipients"]:
                users.append({"type": recipient["type"], "value": recipient["value"]})

        return users

    def insert_objects(self, conn: psycopg2.extensions.connection, filename: str):
        """
        Insert objects into the database
        """
        # Insert raw messages
        for obj in self.message_raw_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            obj_type = "raw"

            is_encrypted = obj.get("securityContent", None) is not None
            has_attachments = obj.get("body", {}).get("attachment", None) is not None
            subject = obj.get("body", {}).get("subject", "")
            receipients_count = len(obj.get("body", {}).get("recipients", []))
            text = obj.get("body", {}).get("text", "")
            direction = obj.get("body", {}).get("direction", "")
            group_name = obj.get("body", {}).get("groupName", None)
            network_type = obj.get("networkType", None)
            network_source = obj.get("sourceType", None)
            message_time = obj.get("body", {}).get("messageTime", None)

            message_id = self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_messages (obj, checksum, obj_type, is_encrypted, subject, text, direction, recipients_count, group_name, network_type, source_type, message_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    obj_type,
                    is_encrypted,
                    subject,
                    text,
                    direction,
                    receipients_count,
                    group_name,
                    network_type,
                    network_source,
                    message_time,
                ),
                "SELECT id FROM telemessage_messages WHERE checksum = %s",
                (checksum,),
            )

            # Add the group, if there is one
            source_type = obj.get("sourceType", None)
            network_type = obj.get("networkType", None)
            if group_name:
                group_id = self.sql_insert_group(
                    conn, group_name, source_type, network_type
                )
            else:
                group_id = None

            # Add the users
            users = self.get_raw_users(obj.get("body", {}))
            self.sql_insert_users(conn, users, message_id, group_id)

            # raw messages don't have attachments that are available in the body

        # Insert raw body messages
        for obj in self.message_raw_body_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            obj_type = "raw_body"

            subject = obj.get("subject", "")
            receipients_count = len(obj.get("recipients", []))
            text = obj.get("text", "")
            direction = obj.get("direction", "")
            group_name = obj.get("groupName", None)
            message_time = obj.get("messageTime", None)

            # If text is base64, assume it's encrypted
            is_encrypted = is_probably_base64(text)

            message_id = self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_messages (obj, checksum, obj_type, is_encrypted, subject, text, direction, recipients_count, group_name, message_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    obj_type,
                    is_encrypted,
                    subject,
                    text,
                    direction,
                    receipients_count,
                    group_name,
                    message_time,
                ),
                "SELECT id FROM telemessage_messages WHERE checksum = %s",
                (checksum,),
            )

            # Add the group, if there is one
            if group_name:
                group_id = self.sql_insert_group(conn, group_name)
            else:
                group_id = None

            # Add the users
            users = self.get_raw_users(obj)
            self.sql_insert_users(conn, users, message_id, group_id)

            # raw messages don't have attachments that are available in the body

        # Insert short messages
        for obj in self.message_short_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            obj_type = "short"

            is_encrypted = obj.get("textSizeEncrypted", None) is not None
            has_attachments = bool(obj.get("attachment"))
            subject = obj.get("subject", "")
            receipients_count = len(obj.get("to", []))
            text = obj.get("textContent", "")
            if not is_encrypted and text != "":
                is_encrypted = is_probably_base64(text)
            direction = obj.get("direction", "")
            group_name = (
                obj.get("dialogGroupName", "")
                if obj.get("groupMessage", False)
                else None
            )

            # Convert message time to milliseconds
            message_time_str = obj.get("messageTime", None)
            if message_time_str:
                try:
                    dt = datetime.strptime(message_time_str, "%Y-%m-%dT%H:%M:%SZ")
                    dt = dt.replace(tzinfo=timezone.utc)
                    message_time = int(dt.timestamp() * 1000)
                except ValueError:
                    # I found one timestamp of "57300-06-03T18:46:03Z", which doesn't
                    # make sense, so I'm just setting it to None if it fails
                    message_time = None
            else:
                message_time = None

            message_id = self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_messages (obj, checksum, obj_type, is_encrypted, has_attachments, subject, text, direction, recipients_count, group_name, message_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    obj_type,
                    is_encrypted,
                    has_attachments,
                    subject,
                    text,
                    direction,
                    receipients_count,
                    group_name,
                    message_time,
                ),
                "SELECT id FROM telemessage_messages WHERE checksum = %s",
                (checksum,),
            )

            # Add the group, if there is one
            if group_name:
                group_id = self.sql_insert_group(
                    conn, group_name, source_type, network_type
                )
            else:
                group_id = None

            # Add the users
            users = []
            for recipient in obj.get("to", []):
                users.append(
                    {
                        "type": "",
                        "value": recipient,
                    }
                )

            users.append({"type": "", "value": obj.get("from", "")})

            # Add the first name and last name to the user
            enrichments = obj.get("participantEnrichments", [])
            from_enrichment = obj.get("fromEnriched", None)
            if from_enrichment:
                enrichments.append(from_enrichment)
            for enrichment in enrichments:
                first_name = enrichment.get("fullName", {}).get("firstName")
                last_name = enrichment.get("fullName", {}).get("lastName")

                if first_name or last_name:
                    for user in users:
                        if user["value"] == enrichment["value"]:
                            user["first_name"] = first_name
                            user["last_name"] = last_name
                            break

            self.sql_insert_users(conn, users, message_id, group_id)

            # Add attachments
            if message_id and obj.get("attachment") is not None:
                for attachment in obj.get("attachment"):
                    self.sql_insert(
                        conn,
                        """
                        INSERT INTO telemessage_attachments (name, content, attach_size, content_type, message_id)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            attachment.get("name", ""),
                            attachment.get("content", ""),
                            attachment.get("attachSize", ""),
                            attachment.get("contentType", ""),
                            message_id,
                        ),
                    )

        # Insert TMobile messages
        for obj in self.message_tmobile_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            obj_type = "tmobile"

            receipients_count = len(obj.get("tmobileMessage", {}).get("to", []))
            text = obj.get("tmobileMessage", {}).get("textContent", "")
            direction = obj.get("tmobileMessage", {}).get("direction", "")
            network_type = "T-Mobile"
            network_source = "T-Mobile"
            message_time = obj.get("tmobileMessage", {}).get("messageDate", None)

            is_encrypted = is_probably_base64(text)

            message_id = self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_messages (obj, checksum, obj_type, is_encrypted, recipients_count, text, direction, network_type, source_type, message_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    obj_type,
                    is_encrypted,
                    receipients_count,
                    text,
                    direction,
                    network_type,
                    source_type,
                    message_time,
                ),
                "SELECT id FROM telemessage_messages WHERE checksum = %s",
                (checksum,),
            )

            # Add the users
            users = []
            for username in obj.get("tmobileMessage", {}).get("to", []):
                users.append(
                    {
                        "type": "",
                        "value": username,
                    }
                )

            from_user = obj.get("tmobileMessage", {}).get("from", None)
            if from_user:
                users.append(
                    {
                        "type": "",
                        "value": from_user,
                    }
                )

            self.sql_insert_users(conn, users, message_id)

        # Insert TMobile body messages
        for obj in self.message_tmobile_body_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            obj_type = "tmobile_body"

            receipients_count = len(obj.get("to", []))
            text = obj.get("textContent", "")
            direction = obj.get("direction", "")
            network_type = "T-Mobile"
            network_source = "T-Mobile"
            message_time = obj.get("messageDate", None)

            is_encrypted = is_probably_base64(text)

            message_id = self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_messages (obj, checksum, obj_type, is_encrypted, recipients_count, text, direction, network_type, source_type, message_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    obj_type,
                    is_encrypted,
                    receipients_count,
                    text,
                    direction,
                    network_type,
                    source_type,
                    message_time,
                ),
                "SELECT id FROM telemessage_messages WHERE checksum = %s",
                (checksum,),
            )

            # Add the users
            users = []
            for username in obj.get("to", []):
                users.append(
                    {
                        "type": "",
                        "value": username,
                    }
                )

            from_user = obj.get("from", None)
            if from_user:
                users.append(
                    {
                        "type": "",
                        "value": from_user,
                    }
                )

            self.sql_insert_users(conn, users, message_id)

        # Insert credentials
        for obj in self.credential_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            username = obj.get("username", None)
            password = obj.get("password", None)

            self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_credentials (obj, checksum, username, password)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    username,
                    password,
                ),
            )

        # Insert validation objects (full)
        for obj in self.validation_full_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            obj_type = "full"

            enhancement_data = obj.get("enhancementData") or {}
            username = enhancement_data.get("userName", None)
            email = enhancement_data.get("email", None)
            active_identity_provider = (
                enhancement_data.get("activeIdentityProviderWithParams") or {}
            ).get("activeIdentityProvider", None)

            email_domain = email.split("@")[-1] if email else None

            self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_validations (obj, checksum, obj_type, username, email, email_domain, active_identity_provider)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    obj_type,
                    username,
                    email,
                    email_domain,
                    active_identity_provider,
                ),
            )

        # Insert validation objects (enhancement)
        for obj in self.validation_enhance_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            obj_type = "enhancementData"
            username = obj.get("userName", None)
            email = obj.get("email", None)
            active_identity_provider = (
                obj.get("activeIdentityProviderWithParams", {}) or {}
            ).get("activeIdentityProvider", None)

            email_domain = email.split("@")[-1] if email else None

            self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_validations (obj, checksum, obj_type, username, email, email_domain, active_identity_provider)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (
                    obj_str,
                    checksum,
                    obj_type,
                    username,
                    email,
                    email_domain,
                    active_identity_provider,
                ),
            )

        # Insert unknown objects
        for obj in self.unknown_objs:
            obj_str = json.dumps(obj)
            checksum = hashlib.sha256(obj_str.encode()).hexdigest()

            self.sql_insert(
                conn,
                """
                INSERT INTO telemessage_unknown (obj, checksum, filename)
                VALUES (%s, %s, %s)
                ON CONFLICT (checksum) DO NOTHING
                RETURNING id
                """,
                (obj_str, checksum, filename),
            )

    def analyze_object(self, obj):
        if isinstance(obj, list):
            for o in obj:
                self.analyze_object(o)

        elif isinstance(obj, dict):
            # Find messages (raw)
            if (
                obj.get("typ") == "RawMessage"
                and obj.get("gatewayReceivedDate") is not None
            ):
                self.message_raw_objs.append(obj)

            # Find messages (raw_body)
            elif (
                "messageType" in obj
                and "owner" in obj
                and "sender" in obj
                and "text" in obj
                and "direction" in obj
            ):
                self.message_raw_body_objs.append(obj)

            # Find messages (short)
            elif (
                "messageContext" in obj
                and "messageTime" in obj
                and "from" in obj
                and "direction" in obj
            ):
                self.message_short_objs.append(obj)

            # Find messages (tmobile)
            elif (
                "segmentedData" in obj
                and "tmobileMessage" in obj
                and "providerNetwork" in obj
            ):
                self.message_tmobile_objs.append(obj)

            # Find messages (tmobile_body)
            elif (
                "direction" in obj
                and "textContent" in obj
                and "messageContext" in obj
                and "messageDate" in obj
            ):
                self.message_tmobile_body_objs.append(obj)

            # Find credentials
            elif obj.get("username") is not None and obj.get("password") is not None:
                self.credential_objs.append(obj)

            # Find validation objects (full)
            elif (
                obj.get("validationData") is not None
                and obj.get("enhancementData") is not None
                and len(obj) == 2
            ):
                self.validation_full_objs.append(obj)

            # Find validation objects (enhancementData)
            elif (
                "data" in obj
                and "userName" in obj
                and "email" in obj
                and "activeIdentityProviderWithParams" in obj
            ):
                self.validation_enhance_objs.append(obj)

            # Plaintext objects might be base64 encoded
            elif (
                "plaintext" in obj
                and len(obj) == 1
                and isinstance(obj["plaintext"], str)
            ):
                # Try base64 decoding the plaintext field
                try:
                    decoded = base64.b64decode(obj["plaintext"])
                    decoded_obj = json.loads(decoded)
                    self.analyze_object(decoded_obj)
                except (base64.binascii.Error, json.JSONDecodeError):
                    # If decoding fails, just skip this object
                    pass

            # Skip other objects
            else:
                self.skip_object(obj)

    def skip_object(self, obj):
        """
        Skip objects that are not relevant. Only display the unidentified ones.
        """

        self.skipped_count += 1

        if (
            # Skip empty objects
            len(obj) == 0
            # Skip fullName objects
            or ("fullName" in obj and "value" in obj and len(obj) == 2)
            # Skip name objects
            or ("firstName" in obj and "lastName" in obj and len(obj) == 2)
            # Skip first name objects
            or ("firstName" in obj and len(obj) == 1)
            # Skip last name objects
            or ("lastName" in obj and len(obj) == 1)
            # Skip {{headerName}} objects
            or ("{{headerName}}" in obj and len(obj) == 1)
            # Skip log messages
            or (
                "@timestamp" in obj
                and "message" in obj
                and "logger_name" in obj
                and "level" in obj
            )
            # Skip status objects
            or ("status" in obj and "components" in obj and len(obj) == 2)
            # Skip piece of encrypted message
            or ("version" in obj and "internalDecryptionData" in obj and len(obj) == 2)
            # Skip piece of encrypted message 2
            or (
                "encryptionData" in obj
                and "integrityHeaderContent" in obj
                and len(obj) == 2
            )
            # Skip piece of encrypted message 3
            or ("keyVersionState" in obj and len(obj) == 1)
            # Skip simple reactive discovery client
            or ("Simple Reactive Discovery Client" in obj and len(obj) == 1)
            # Skip chains object
            or ("validChains" in obj and "invalidChains" in obj and len(obj) == 2)
            # Skip discovery client information objects 1
            or (
                "status" in obj
                and "groups" in obj
                and "components" in obj
                and len(obj) == 3
            )
            # Skip discovery client information objects 2
            or (
                "discoveryComposite" in obj
                and "diskSpace" in obj
                and "livenessState" in obj
                and "reactiveDiscoveryClients" in obj
            )
            # Skip discovery client information objects 3
            or (
                "status" in obj
                and "description" in obj
                and "components" in obj
                and len(obj) == 3
            )
            # Skip description/status objects
            or ("description" in obj and "status" in obj and len(obj) == 2)
            # Skip description/error objects
            or ("description" in obj and "error" in obj and len(obj) == 2)
            # Skip keyResult objects
            or ("keyResult" in obj and len(obj) == 1)
            # Skip errors objects
            or ("errors" in obj and len(obj) == 1)
            # Skip lease request objects
            or (
                "request_id" in obj
                and "lease_id" in obj
                and "renewable" in obj
                and "lease_duration" in obj
            )
            # Skip source objects
            or ("source" in obj and len(obj) == 1 and type(obj["source"]) is str)
            # Skip status objects
            or ("status" in obj and len(obj) == 1 and type(obj["status"]) is str)
            # Skip ciphertext objects
            or ("ciphertext" in obj and "key_version" in obj and len(obj) == 2)
            # Skip lonely group object
            or ("name" in obj and "id" in obj and "type" in obj and len(obj) == 3)
            # Skip lonely user object
            or ("value" in obj and "type" in obj and len(obj) == 2)
            # Skip lonely user object
            or ("value" in obj and len(obj) == 1)
            # Skip archive request object
            or (
                "archiveRequestState" in obj
                and "securityResult" in obj
                and len(obj) == 2
            )
            # Skip http response object
            or (
                "type" in obj
                and "title" in obj
                and "status" in obj
                and "detail" in obj
                and "instance" in obj
                and len(obj) == 5
            )
            # Skip participantEnrichments-like objects
            or (
                all(
                    isinstance(k, str)
                    and k.startswith('{"value":')
                    and k.endswith("}")
                    and isinstance(v, dict)
                    and "firstName" in v
                    and "lastName" in v
                    for k, v in obj.items()
                )
            )
            # Skip message fragment
            or ("typ" in obj and "data" in obj and len(obj) == 2)
            # Skip message fragment 2
            or ("extractor" in obj and "length" in obj and len(obj) == 2)
            # Skip message fragment 3
            or (
                "providerNetwork" in obj
                and "segmentedDataWrapper" in obj
                and "internalSecurityData" in obj
                and "kafkafied" in obj
                and len(obj) == 4
            )
            # Skip http headers
            or ("host" in obj and "user-agent" in obj)
            # Skip validated/reason objects
            or ("validated" in obj and "reason" in obj and len(obj) == 2)
            # Skip configuration objects
            or (
                "ConfigurationPropertiesRebinderAutoConfiguration" in obj
                and "EncryptionBootstrapConfiguration" in obj
            )
            # Skip aliases/scope/type/resource/dependencies objects
            or (
                "aliases" in obj
                and "scope" in obj
                and "type" in obj
                and "resource" in obj
                and "dependencies" in obj
                and len(obj) == 5
            )
            # Skip encryption fragment
            or ("ENC_SESSION_KEY" in obj and "PUBLIC_KEY_ID" in obj and len(obj) == 2)
            # Skip attachmentSizeType/sizeInBytes objects
            or ("attachmentSizeType" in obj and "sizeInBytes" in obj and len(obj) == 2)
            # Skip typ/value/type objects
            or ("typ" in obj and "value" in obj and "type" in obj and len(obj) == 3)
            # Skip extClassId objects
            or ("extClassId" in obj and len(obj) == 1)
            # Skip discoveryClient objects
            or ("discoveryClient" in obj and len(obj) == 1)
            # Skip total/free/threshold/path/exists objects
            or (
                "total" in obj
                and "free" in obj
                and "threshold" in obj
                and "path" in obj
                and "exists" in obj
                and len(obj) == 5
            )
            # Skip configuredLevel/effectiveLevel objects
            or ("configuredLevel" in obj and "effectiveLevel" in obj and len(obj) == 2)
            # Skip configuredLevel/members objects
            or ("configuredLevel" in obj and "members" in obj and len(obj) == 2)
            # Skip name/content/contentType/attachSize objects
            or (
                "name" in obj
                and "content" in obj
                and "contentType" in obj
                and "attachSize" in obj
                and len(obj) == 4
            )
            # Skip status/details objects
            or ("status" in obj and "details" in obj and len(obj) == 2)
            # skip readinessState objects
            or ("readinessState" in obj and len(obj) == 1)
            # Skip Spring Boot management objects
            or (
                "self" in obj
                and "circuitbreakers" in obj
                and "prometheus" in obj
                and "heapdump" in obj
            )
            # Skip handlerMethod/requestMappingConditions objects
            or (
                "handlerMethod" in obj
                and "requestMappingConditions" in obj
                and len(obj) == 2
            )
            # Skip object objects
            or (
                "object" in obj
                and len(obj) == 1
                and "parentFolderPath" in obj["object"]
                and "attributes" in obj["object"]
                and len(obj["object"]) == 2
            )
            # Skip timeLimiterEvents objects
            or ("timeLimiterEvents" in obj and len(obj) == 1)
            # Skip retries objects
            or ("retries" in obj and len(obj) == 1)
            # Skip value/predefined objects
            or ("value" in obj and "predefined" in obj and len(obj) == 2)
            # Skip identifier/processStatus/data/markerTtlMills/latestUseEpchMills objects
            or (
                "identifier" in obj
                and "processStatus" in obj
                and "data" in obj
                and "markerTtlMills" in obj
                and "latestUseEpchMills" in obj
                and len(obj) == 5
            )
            # Skip oauth objects
            or (
                "activeIdentityProvider" in obj
                and "identityProviderParams" in obj
                and len(obj) == 2
            )
            # Skip oauth object identityProviderParams fragments
            or (
                "NONCE" in obj
                and "EXPIRATION_DAYS" in obj
                and "SCOPE" in obj
                and "AUTHORIZATION_ENDPOINT" in obj
            )
            # Skip another oauth fragment
            or (
                "url" in obj
                and "configUrl" in obj
                and "validatorUrl" in obj
                and "oauth2RedirectUrl" in obj
            )
            # Skip appId objects
            or ("appId" in obj and len(obj) == 1)
            # Skip name/contentType/digest/content/attachmentSize/attachmentDate objects
            or (
                "name" in obj
                and "contentType" in obj
                and "digest" in obj
                and "content" in obj
                and "attachmentSize" in obj
                and "attachmentDate" in obj
                and len(obj) == 6
            )
            # Skip callID/recipientNum/callStatus/startTime/endTime objects
            or (
                "callID" in obj
                and "recipientNum" in obj
                and "callStatus" in obj
                and "startTime" in obj
                and "endTime" in obj
                and len(obj) == 5
            )
            # Skip keyId/encSessionKey fragments
            or ("keyId" in obj and "encSessionKey" in obj and len(obj) == 2)
            # Skip typ/params/encryptionType objects
            or (
                "typ" in obj
                and "params" in obj
                and "encryptionType" in obj
                and len(obj) == 3
            )
            # Skip attachSizeEncrypted/attachSize/name/content/contentType objects
            or (
                "attachSizeEncrypted" in obj
                and "attachSize" in obj
                and "name" in obj
                and "content" in obj
                and "contentType" in obj
                and len(obj) == 5
            )
            # Skip owner/sender/recipients/messageContent/callInfo fragments (even though these have have some message content)
            or (
                "owner" in obj
                and "sender" in obj
                and "recipients" in obj
                and "messageContent" in obj
                and "callInfo" in obj
                and len(obj) == 5
            )
            # Skip attachSize/name/contentType objects
            or (
                "attachSize" in obj
                and "name" in obj
                and "contentType" in obj
                and len(obj) == 3
            )
            # Skip name/value objects
            or ("name" in obj and "value" in obj and len(obj) == 2)
            # Skip type objects
            or ("type" in obj and len(obj) == 1)
            # Skip short messages without from
            or (
                "messageContext" in obj
                and "messageTime" in obj
                and "direction" in obj
                and "from" not in obj
            )
            # Skip objects with message field, string value
            or ("message" in obj and len(obj) == 1 and isinstance(obj["message"], str))
            # Skip attestation objects
            or (
                "os" in obj
                and "device" in obj
                and "success" in obj
                and "attestationCertChain" in obj
            )
            # Skip msisdn/firstName objects
            or ("msisdn" in obj and "firstName" in obj and len(obj) == 2)
            # Skip livenessState objects
            or ("livenessState" in obj and len(obj) == 1)
            # Skip address objects
            or (
                "address" in obj
                and len(obj) == 1
                and "totalsCollector" in obj["address"]
            )
            # Skip collectorList objects
            or ("collectorList" in obj and len(obj) == 1)
            # Skip {"kafkafied": true}
            or ("kafkafied" in obj and len(obj) == 1)
            # Skip mCanonicalRepresentation objects
            or ("mCanonicalRepresentation" in obj)
            # Skip host/path/port/query/scheme/fragment/authority/uriString objects
            or (
                "host" in obj
                and "path" in obj
                and "port" in obj
                and "query" in obj
                and "scheme" in obj
                and "fragment" in obj
                and "authority" in obj
                and "uriString" in obj
            )
            # Skip endTime/startTime/callStatus/callDurationInMillis objects
            or (
                "endTime" in obj
                and "startTime" in obj
                and "callStatus" in obj
                and "callDurationInMillis" in obj
            )
            # Skip spring.cloud.vault objects
            or ("spring.cloud.vault.uri" in obj and "spring.cloud.vault.host" in obj)
            # Skip value/origin objects
            or ("value" in obj and "origin" in obj and len(obj) == 2)
            # Skip objects with a single key and a string value
            or (
                len(obj) == 1
                and isinstance(list(obj.keys())[0], str)
                and isinstance(list(obj.values())[0], str)
            )
            # Skip segmented message fragments
            or (
                "pieceNumber" in obj
                and "segmentedId" in obj
                and "totalPieces" in obj
                and len(obj) == 3
            )
            # Skip name/lastName/firstName objects
            or (
                "name" in obj
                and "lastName" in obj
                and "firstName" in obj
                and len(obj) == 3
            )
            # Skip type/subject objects
            or ("type" in obj and "subject" in obj and len(obj) == 2)
            # Skip type/subject/direction objects
            or (
                "type" in obj
                and "subject" in obj
                and "direction" in obj
                and len(obj) == 3
            )
            # Skip extractor/kafkafied objects
            or (
                "extractor" in obj
                and "kafkafied" in obj
                and len(obj) == 2
                and "text" in obj["extractor"]
                and obj["extractor"]["text"] is None
            )
            # Skip _links objects
            or ("_links" in obj and len(obj) == 1 and isinstance(obj["_links"], dict))
            # Skip negated/mediaType objects
            or ("negated" in obj and "mediaType" in obj and len(obj) == 2)
            # Skip fileName/className/lineNumber/methodName/moduleName objects
            or (
                "fileName" in obj
                and "className" in obj
                and "lineNumber" in obj
                and "methodName" in obj
                and "moduleName" in obj
            )
            # Skip className/identityHashCode objects
            or ("className" in obj and "identityHashCode" in obj and len(obj) == 2)
            # Skip firstName/lastNname objects
            or ("firstName" in obj and "lastNname" in obj and len(obj) == 2)
            # Skip name/value/attachSize/attacheSizeEncrypted objects
            or (
                "name" in obj
                and "value" in obj
                and "attachSize" in obj
                and "attacheSizeEncrypted" in obj
                and len(obj) == 4
            )
        ):
            return

        # Found an unknown object
        self.unknown_objs.append(obj)
