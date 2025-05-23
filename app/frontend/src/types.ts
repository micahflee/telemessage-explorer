export type Group = {
    id: number;
    group_name: string;
    source_type: string;
    network_type: string;
    notes: string;
    message_count: number;
    user_count: number;
};

export type User = {
    id: number;
    type: string;
    value: string;
    first_name: string;
    last_name: string;
    notes: string;
    group_count: number;
    message_count: number;
};

export type Message = {
    id: number;
    is_encrypted: boolean;
    has_attachments: boolean;
    subject: string;
    text: string;
    direction: string;
    recipients_count: number;
    group_name: string;
    network_type: string;
    source_type: string;
    message_time: number;
    obj?: object;
    obj_type?: string;
};

export type Attachment = {
    id: number;
    name: string;
    content: string;
    attach_size: string;
    content_type: string;
}

export type Validation = {
    id: number;
    username: string;
    email: string;
    email_domain: string;
    active_identity_provider: string;
};

export type GroupDetails = {
    group: Group;
    users: User[];
    messages: Message[];
};

export type UserDetails = {
    user: User;
    groups: Group[];
    messages: Message[];
};

export type MessageDetails = {
    message: Message;
    groups: Group[];
    users: User[];
    attachments: Attachment[];
};

export type ValidationDetails = {
    validation: Validation;
    obj?: object;
    obj_type?: string;
};