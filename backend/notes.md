Finding distinct `sourceType`s:

```sql
SELECT DISTINCT message->'sourceType' FROM messages;
```

Finding distinct `networkType`s:

```sql
SELECT DISTINCT message->'networkType' FROM messages;
```

Finding text messages that mention Trump:

```sql
SELECT
    filename,
    message->'body'->>'messageTime' AS messageTime,
    message->>'networkType' AS networkType,
    message->>'sourceType' AS sourceType,
    message->'body'->>'subject' AS subject,
    message->'body'->>'groupName' AS groupName,
    message->'body'->>'text' AS text
FROM messages
WHERE
    message->'body'->>'text' LIKE '%trump%';
```

Finding texts with a specific participant:

```sql
SELECT
    filename,
    message->'body'->>'messageTime' AS messageTime,
    message->>'networkType' AS networkType,
    message->>'sourceType' AS sourceType,
    message->'body'->>'subject' AS subject,
    message->'body'->>'groupName' AS groupName,
    message->'body'->>'text' AS text,
    message
FROM messages
WHERE EXISTS (
    SELECT 1
    FROM jsonb_array_elements(message->'body'->'recipients') AS recipient
    WHERE recipient->>'value' = '13016769156'
)
ORDER BY messagetime
```


Finding texts with a specific participant, sender, or owner:

```sql
SELECT
    filename,
    message->'body'->>'messageTime' AS messageTime,
    message->>'networkType' AS networkType,
    message->>'sourceType' AS sourceType,
    message->'body'->>'subject' AS subject,
    message->'body'->>'groupName' AS groupName,
    message->'body'->>'text' AS text,
    message
FROM messages
WHERE
    EXISTS (
        SELECT 1
        FROM jsonb_array_elements(message->'body'->'recipients') AS recipient
        WHERE recipient->>'value' = '12038245553'
    ) OR
    message->'body'->'sender'->>'value' = '12038245553' OR
    message->'body'->'owner'->>'value' = '12038245553'
ORDER BY messagetime
```

Note that phone number `12038245553` is this guy: https://x.com/alpackaP/status/1856425712967647262

Multiple receipients:

```sql
SELECT
    filename,
    message->'body'->>'messageTime' AS messageTime,
    message->>'networkType' AS networkType,
    message->>'sourceType' AS sourceType,
    message->'body'->>'subject' AS subject,
    message->'body'->>'groupName' AS groupName,
    message->'body'->>'text' AS text,
    message
FROM messages
WHERE
    EXISTS (
        SELECT 1
        FROM jsonb_array_elements(message->'body'->'recipients') AS recipient
        WHERE recipient->>'value' = '17372282154'
    ) OR
    message->'body'->'sender'->>'value' = '17372282154' OR
    message->'body'->'owner'->>'value' = '17372282154' OR

    EXISTS (
        SELECT 1
        FROM jsonb_array_elements(message->'body'->'recipients') AS recipient
        WHERE recipient->>'value' = '15129036544'
    ) OR
    message->'body'->'sender'->>'value' = '15129036544' OR
    message->'body'->'owner'->>'value' = '15129036544'
ORDER BY messagetime
```

Filter out encrypted messages:

```sql
SELECT
    filename,
    message->'body'->>'messageTime' AS messageTime,
    message->>'networkType' AS networkType,
    message->>'sourceType' AS sourceType,
    message->'body'->>'subject' AS subject,
    message->'body'->>'groupName' AS groupName,
    message->'body'->>'text' AS text,
    message
FROM messages
WHERE
    message->>'securityContent' IS NULL AND
    message->'body'->>'text' ILIKE '%gun%'
ORDER BY messagetime
LIMIT 20000
```

## Interesting messages

- There are no undercovers out there. And I drove by that house in a black and white


==

Count of how many messages and groups each user has:

```sql
SELECT 
    u.id AS user_id,
    u.first_name,
    u.last_name,
    u.type,
    u.value,
    COALESCE(m.message_count, 0) AS message_count,
    COALESCE(g.group_count, 0) AS group_count
FROM 
    telemessage_users u
LEFT JOIN (
    SELECT 
        user_id,
        COUNT(DISTINCT message_id) AS message_count
    FROM 
        telemessage_users_messages
    GROUP BY 
        user_id
) m ON u.id = m.user_id
LEFT JOIN (
    SELECT 
        user_id,
        COUNT(DISTINCT group_id) AS group_count
    FROM 
        telemessage_users_groups
    GROUP BY 
        user_id
) g ON u.id = g.user_id
ORDER BY 
    group_count DESC;
```
