<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { type Group } from '@/types.ts';
import { API } from '@/api.ts';

import GroupListComponent from '@/components/GroupListComponent.vue';
import PaginationControls from '@/components/PaginationControls.vue';

const api = inject('api') as API;
const isLoading = ref(true);
const groups = ref<Group[]>([]);

const limit = ref(100);
const offset = ref(0);
const total = ref(0);
const q = ref('');
const sort = ref('id');
const order = ref('desc');

const sortOptions = [
    { value: 'id', label: 'ID' },
    { value: 'group_name', label: 'Group Name' },
    { value: 'source_type', label: 'Source Type' },
    { value: 'network_type', label: 'Network Type' },
    { value: 'message_count', label: 'Messages' },
    { value: 'user_count', label: 'Users' },
    { value: 'notes', label: 'Notes' },
];

async function loadGroups() {
    isLoading.value = true;
    const data = await api.getGroups(
      limit.value,
      offset.value,
      q.value,
      sort.value,
      order.value
    );
    groups.value = data.groups;
    total.value = data.pagination.total;
    isLoading.value = false;
}

function updateLimit(newLimit: number) {
    if (limit.value !== newLimit) {
        limit.value = newLimit;
        offset.value = 0;
        loadGroups();
    }
}
function updateOffset(newOffset: number) {
    if (offset.value !== newOffset) {
        offset.value = newOffset;
        loadGroups();
    }
}
function updateQ(newQ: string) {
    if (q.value !== newQ) {
        q.value = newQ;
        offset.value = 0;
        loadGroups();
    }
}
function updateSort(newSort: string) {
    if (sort.value !== newSort) {
        sort.value = newSort;
        offset.value = 0;
        loadGroups();
    }
}
function updateOrder(newOrder: string) {
    if (order.value !== newOrder) {
        order.value = newOrder;
        offset.value = 0;
        loadGroups();
    }
}

onMounted(loadGroups);
</script>

<template>
    <div>
        <h1>Groups</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
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

            <GroupListComponent :groups="groups" :total="total" />

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