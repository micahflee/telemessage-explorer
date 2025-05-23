import type {
    Group,
    GroupDetails,
    User,
    UserDetails,
    Message,
    MessageDetails,
    Validation,
    ValidationDetails
} from './types.ts'

export class API {
    private baseUrl: string;

    constructor() {
        if (import.meta.env.DEV) {
            // In development mode, use the app container
            this.baseUrl = "http://localhost:8080/api";
        } else {
            // In prod mode, load from the same origin
            this.baseUrl = "/api";
        }
        console.log(`API base URL: ${this.baseUrl}`);
    }

    async apiFetch(endpoint: string): Promise<Response> {
        const url = `${this.baseUrl}${endpoint}`;
        console.log(`Fetching ${url}`);
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Error fetching ${endpoint}: ${response.statusText}`);
        }
        return response;
    }

    async getGroups(
        limit = 500,
        offset = 0,
        q = "",
        sort = "id",
        order = "desc"
    ): Promise<{ groups: Group[], pagination: { total: number, limit: number, offset: number } }> {
        const params = new URLSearchParams({
            limit: String(limit),
            offset: String(offset),
            q,
            sort,
            order,
        });
        const response = await this.apiFetch(`/groups?${params.toString()}`);
        const data = await response.json();
        return data;
    }
    async getGroup(groupId: number): Promise<GroupDetails> {
        const response = await this.apiFetch(`/groups/${groupId}`);
        const groupDetails: GroupDetails = await response.json();
        return groupDetails;
    }

    async getUsers(
        limit = 500,
        offset = 0,
        q = "",
        sort = "id",
        order = "desc"
    ): Promise<{ users: User[], pagination: { total: number, limit: number, offset: number } }> {
        const params = new URLSearchParams({
            limit: String(limit),
            offset: String(offset),
            q,
            sort,
            order,
        });
        const response = await this.apiFetch(`/users?${params.toString()}`);
        const data = await response.json();
        return data;
    }

    async getUser(userId: number): Promise<UserDetails> {
        const response = await this.apiFetch(`/users/${userId}`);
        const userDetails: UserDetails = await response.json();
        return userDetails;
    }

    async getMessages(
        limit = 500,
        offset = 0,
        q = "",
        sort = "id",
        order = "desc",
        hideEncrypted = false,
        showAttachments = false
    ): Promise<{ messages: Message[], pagination: { total: number, limit: number, offset: number } }> {
        const params = new URLSearchParams({
            limit: String(limit),
            offset: String(offset),
            q,
            sort,
            order,
            hide_encrypted: hideEncrypted ? "true" : "false",
            show_attachments: showAttachments ? "true" : "false",
        });
        const response = await this.apiFetch(`/messages?${params.toString()}`);
        const data = await response.json();
        return data;
    }

    async getMessage(messageId: number): Promise<MessageDetails> {
        const response = await this.apiFetch(`/messages/${messageId}`);
        const messageDetails: MessageDetails = await response.json();
        return messageDetails;
    }

    async getValidations(
        limit = 500,
        offset = 0,
        q = "",
        sort = "id",
        order = "desc"
    ): Promise<{ validations: Validation[], pagination: { total: number, limit: number, offset: number } }> {
        const params = new URLSearchParams({
            limit: String(limit),
            offset: String(offset),
            q,
            sort,
            order,
        });
        const response = await this.apiFetch(`/validations?${params.toString()}`);
        const data = await response.json();
        return data;
    }

    async getValidation(validationId: number): Promise<ValidationDetails> {
        const response = await this.apiFetch(`/validations/${validationId}`);
        const validation: ValidationDetails = await response.json();
        return validation;
    }
}
