<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { type User } from '@/types.ts';
import { API } from '@/api.ts';

import UserListComponent from '@/components/UserListComponent.vue';
import PaginationControls from '@/components/PaginationControls.vue';

const api = inject('api') as API;
const isLoading = ref(true);
const users = ref<User[]>([]);

const limit = ref(100);
const offset = ref(0);
const total = ref(0);
const q = ref('');
const sort = ref('id');
const order = ref('desc');

const sortOptions = [
    { value: 'id', label: 'ID' },
    { value: 'type', label: 'Type' },
    { value: 'value', label: 'Value' },
    { value: 'first_name', label: 'First Name' },
    { value: 'last_name', label: 'Last Name' },
    { value: 'group_count', label: 'Groups' },
    { value: 'message_count', label: 'Messages' },
];

async function loadUsers() {
    isLoading.value = true;
    const data = await api.getUsers(
        limit.value,
        offset.value,
        q.value,
        sort.value,
        order.value
    );
    users.value = data.users;
    total.value = data.pagination.total;
    isLoading.value = false;
}

function updateLimit(newLimit: number) {
    if (limit.value !== newLimit) {
        limit.value = newLimit;
        offset.value = 0;
        loadUsers();
    }
}
function updateOffset(newOffset: number) {
    if (offset.value !== newOffset) {
        offset.value = newOffset;
        loadUsers();
    }
}
function updateQ(newQ: string) {
    if (q.value !== newQ) {
        q.value = newQ;
        offset.value = 0;
        loadUsers();
    }
}
function updateSort(newSort: string) {
    if (sort.value !== newSort) {
        sort.value = newSort;
        offset.value = 0;
        loadUsers();
    }
}
function updateOrder(newOrder: string) {
    if (order.value !== newOrder) {
        order.value = newOrder;
        offset.value = 0;
        loadUsers();
    }
}

onMounted(loadUsers);
</script>

<template>
    <div>
        <h1>Users</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
            <PaginationControls class="mb-3" :total="total" :limit="limit" :offset="offset" :q="q" :sort="sort"
                :order="order" :sortOptions="sortOptions" @update:limit="updateLimit" @update:offset="updateOffset"
                @update:q="updateQ" @update:sort="updateSort" @update:order="updateOrder" />

            <UserListComponent :users="users" :total="total" />

            <PaginationControls class="mt-3" :total="total" :limit="limit" :offset="offset" :q="q" :sort="sort"
                :order="order" :sortOptions="sortOptions" @update:limit="updateLimit" @update:offset="updateOffset"
                @update:q="updateQ" @update:sort="updateSort" @update:order="updateOrder" />
        </template>
    </div>
</template>

<style scoped></style>