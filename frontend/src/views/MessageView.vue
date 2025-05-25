<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { useRoute } from 'vue-router';
import { type MessageDetails, type Attachment } from '@/types.ts';
import { API } from '@/api.ts';
import { formatDate } from '@/utils.ts';

import GroupListComponent from '@/components/GroupListComponent.vue';
import UserListComponent from '@/components/UserListComponent.vue';

const route = useRoute();
const messageId = Number(route.params.messageId);

const api = inject('api') as API;
const isLoading = ref(true);
const messageDetails = ref<MessageDetails>();

function downloadAttachment(attachment: Attachment) {
    // Sometimes attachment.content is surrounded with quotes, if so
    // remove them before base64 decoding
    if (attachment.content.startsWith('"') && attachment.content.endsWith('"')) {
        attachment.content = attachment.content.slice(1, -1);
    }

    // Decode base64 to binary
    const byteCharacters = atob(attachment.content);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);

    // Create a Blob with the correct content type
    const blob = new Blob([byteArray], { type: attachment.content_type || 'application/octet-stream' });

    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = attachment.name || 'attachment';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}

onMounted(async () => {
    isLoading.value = true;
    messageDetails.value = await api.getMessage(messageId);
    isLoading.value = false;
});
</script>

<template>
    <div>
        <h1>Message: {{ messageDetails?.message.source_type }} ({{ messageDetails?.message.id }})</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
            <template v-if="!messageDetails">
                <h2 class="text-muted text-center">Message not found</h2>
            </template>
            <template v-else>
                <h3 class="mt-5">Details</h3>
                <ul>
                    <li>
                        ID: <strong>{{ messageDetails.message.id }}</strong>
                    </li>
                    <li>
                        Is Encrypted: <strong>{{ messageDetails.message.is_encrypted ? 'Yes' : 'No' }}</strong>
                    </li>
                    <li>
                        Has Attachments: <strong>{{ messageDetails.message.has_attachments ? 'Yes' : 'No' }}</strong>
                    </li>
                    <li>
                        Subject: <strong>{{ messageDetails.message.subject }}</strong>
                    </li>
                    <li>
                        Text: <strong>{{ messageDetails.message.text }}</strong>
                    </li>
                    <li>
                        Direction: <strong>{{ messageDetails.message.direction }}</strong>
                    </li>
                    <li>
                        Message Time: <strong>{{ formatDate(messageDetails.message.message_time) }}</strong>
                    </li>
                    <li>
                        Source Type: <strong>{{ messageDetails.message.source_type }}</strong>
                    </li>
                    <li>
                        Network Type: <strong>{{ messageDetails.message.network_type }}</strong>
                    </li>
                </ul>

                <template v-if="messageDetails.groups.length > 0">
                    <h3 class="mt-5">Groups</h3>
                    <GroupListComponent :groups="messageDetails.groups" :total="messageDetails.groups.length" />
                </template>

                <h3 class="mt-5">Users</h3>
                <UserListComponent :users="messageDetails.users" :total="messageDetails.users.length" />

                <template v-if="messageDetails.attachments.length > 0">
                    <h3 class="mt-5">Attachments</h3>
                    <ul>
                        <li v-for="attachment in messageDetails.attachments" :key="attachment.id">
                            <button class="btn btn-primary btn-sm m-1" @click="downloadAttachment(attachment)">
                                <template v-if="messageDetails.message.is_encrypted">
                                    Download (encrypted, so not very useful)
                                </template>
                                <template v-else>
                                    Download
                                </template>
                            </button>
                            <ul>
                                <li>
                                    ID: <strong>{{ attachment.id }}</strong>
                                </li>
                                <li>
                                    Name: <strong>{{ attachment.name }}</strong>
                                </li>
                                <li>
                                    Content Type: <strong>{{ attachment.content_type }}</strong>
                                </li>
                                <li>
                                    Size: <strong>{{ attachment.attach_size }}</strong>
                                </li>
                            </ul>
                        </li>
                    </ul>
                </template>

                <h3 class="mt-5">JSON object ({{ messageDetails.message.obj_type }})</h3>
                <pre><code class="language-json">{{ JSON.stringify(messageDetails.message.obj, null, 2) }}</code></pre>
            </template>
        </template>
    </div>
</template>

<style scoped>
code {
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-all;
}
pre {
    white-space: pre-wrap;
    word-break: break-all;
}
</style>
