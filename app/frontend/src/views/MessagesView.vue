<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { type Message } from '@/types.ts';
import { API } from '@/api.ts';

import MessageListComponent from '@/components/MessageListComponent.vue';
import PaginationControls from '@/components/PaginationControls.vue';

const api = inject('api') as API;
const isLoading = ref(true);
const messages = ref<Message[]>([]);

const limit = ref(100);
const offset = ref(0);
const total = ref(0);
const q = ref('');
const sort = ref('message_time');
const order = ref('desc');
const hideEncrypted = ref(false);
const showAttachments = ref(false);

const sortOptions = [
  { value: 'id', label: 'ID' },
  { value: 'subject', label: 'Subject' },
  { value: 'text', label: 'Text' },
  { value: 'direction', label: 'Direction' },
  { value: 'recipients_count', label: 'Recipients' },
  { value: 'group_name', label: 'Group Name' },
  { value: 'network_type', label: 'Network Type' },
  { value: 'source_type', label: 'Source Type' },
  { value: 'message_time', label: 'Message Time' },
  { value: 'is_encrypted', label: 'Is Encrypted' },
  { value: 'has_attachments', label: 'Has Attachments' },
];

async function loadMessages() {
    isLoading.value = true;
    const data = await api.getMessages(
      limit.value,
      offset.value,
      q.value,
      sort.value,
      order.value,
      hideEncrypted.value,
      showAttachments.value
    );
    messages.value = data.messages;
    total.value = data.pagination.total;
    isLoading.value = false;
}

function updateLimit(newLimit: number) {
    if (limit.value !== newLimit) {
        limit.value = newLimit;
        offset.value = 0;
        loadMessages();
    }
}
function updateOffset(newOffset: number) {
    if (offset.value !== newOffset) {
        offset.value = newOffset;
        loadMessages();
    }
}
function updateQ(newQ: string) {
    if (q.value !== newQ) {
        q.value = newQ;
        offset.value = 0;
        loadMessages();
    }
}
function updateSort(newSort: string) {
    if (sort.value !== newSort) {
        sort.value = newSort;
        offset.value = 0;
        loadMessages();
    }
}
function updateOrder(newOrder: string) {
    if (order.value !== newOrder) {
        order.value = newOrder;
        offset.value = 0;
        loadMessages();
    }
}

function updateHideEncrypted(val: boolean) {
    hideEncrypted.value = val;
    offset.value = 0;
    loadMessages();
}
function updateShowAttachments(val: boolean) {
    showAttachments.value = val;
    offset.value = 0;
    loadMessages();
}

onMounted(loadMessages);
</script>

<template>
    <div>
        <h1>Messages</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
            <div class="mb-2 d-flex gap-3 align-items-center justify-content-center">
                <label class="form-check-label">
                    <input type="checkbox" class="form-check-input" v-model="hideEncrypted" @change="updateHideEncrypted(hideEncrypted)" />
                    Hide encrypted
                </label>
                <label class="form-check-label">
                    <input type="checkbox" class="form-check-input" v-model="showAttachments" @change="updateShowAttachments(showAttachments)" />
                    Show only with attachments
                </label>
            </div>
            <PaginationControls
                class="mb-3"
                :total="total"
                :limit="limit"
                :offset="offset"
                :q="q"
                :sort="sort"
                :order="order"
                :sortOptions="sortOptions"
                @update:limit="updateLimit"
                @update:offset="updateOffset"
                @update:q="updateQ"
                @update:sort="updateSort"
                @update:order="updateOrder"
            />

            <MessageListComponent :messages="messages" :total="total" />

            <PaginationControls
                class="mt-3"
                :total="total"
                :limit="limit"
                :offset="offset"
                :q="q"
                :sort="sort"
                :order="order"
                :sortOptions="sortOptions"
                @update:limit="updateLimit"
                @update:offset="updateOffset"
                @update:q="updateQ"
                @update:sort="updateSort"
                @update:order="updateOrder"
            />
        </template>
    </div>
</template>

<style scoped>
.subject {
    max-width: 200px;
    word-wrap: break-word;
}

.message_text {
    max-width: 350px;
    word-wrap: break-word;
}
</style>