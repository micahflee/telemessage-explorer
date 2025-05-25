<script setup lang="ts">
import { type Message } from '@/types.ts';
import { formatDate } from '@/utils.ts';

defineProps<{
    total: number;
    messages: Message[];
}>();
</script>

<template>
    <div>
        <div class="text-end text-muted">
            found {{ total.toLocaleString() }} rows
        </div>

        <div class="list">
            <table class="table">
                <thead>
                    <tr>
                        <th class="text-nowrap">ID</th>
                        <th class="text-nowrap">Message Time</th>
                        <th class="text-nowrap">Subject</th>
                        <th class="text-nowrap">Text</th>
                        <th class="text-nowrap">Dir</th>
                        <th class="text-nowrap">Recipients</th>
                        <th class="text-nowrap">Group Name</th>
                        <th class="text-nowrap">
                            <i class="fa-solid fa-paperclip"></i>
                        </th>
                        <th class="text-nowrap">Network Type</th>
                        <th class="text-nowrap">Source Type</th>
                    </tr>
                </thead>
                <tbody class="list">
                    <tr v-if="total === 0">
                        <td colspan="10" class="text-center">No messages found</td>
                    </tr>
                    <tr v-for="message in messages" :key="message.id">
                        <td class="id">
                            <router-link :to="`/messages/${message.id}`" class="btn btn-secondary btn-sm">{{ message.id }}</router-link>
                        </td>
                        <td class="message_time">{{ formatDate(message.message_time) }}</td>
                        <td class="subject">{{ message.subject }}</td>
                        <td class="text">
                            <template v-if="message.is_encrypted">
                                <span class="text-muted fst-italic">
                                    <i class="fa-solid fa-lock me-2"></i>
                                    encrypted
                                </span>
                            </template>
                            <template v-else>{{ message.text }}</template>
                        </td>
                        <td class="direction">{{ message.direction }}</td>
                        <td class="recipients_count">{{ message.recipients_count }}</td>
                        <td class="group_name">{{ message.group_name }}</td>
                        <td class="has_attachments">
                            <template v-if="message.has_attachments">
                                <i class="fa-solid fa-circle-check"></i>
                            </template>
                            <template v-else>
                                <i class="fa-solid fa-circle-xmark"></i>
                            </template>
                        </td>
                        <td class="network_type">{{ message.network_type }}</td>
                        <td class="source_type">{{ message.source_type }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<style scoped>
.subject {
    max-width: 200px;
    word-wrap: break-word;
}

.text {
    min-width: 200px;
    max-width: 350px;
    word-wrap: break-word;
}
</style>