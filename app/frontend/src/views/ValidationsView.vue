<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { type Validation } from '@/types.ts';
import { API } from '@/api.ts';

import ValidationListComponent from '@/components/ValidationListComponent.vue';
import PaginationControls from '@/components/PaginationControls.vue';

const api = inject('api') as API;
const isLoading = ref(true);
const validations = ref<Validation[]>([]);

const limit = ref(100);
const offset = ref(0);
const total = ref(0);
const q = ref('');
const sort = ref('id');
const order = ref('desc');
const distinctEmails = ref(false);

const sortOptions = [
    { value: 'id', label: 'ID' },
    { value: 'username', label: 'Username' },
    { value: 'email', label: 'Email' },
    { value: 'email_domain', label: 'Domain' },
    { value: 'active_identity_provider', label: 'Provider' },
];

async function loadValidations() {
    isLoading.value = true;
    const data = await api.getValidations(
        limit.value,
        offset.value,
        q.value,
        sort.value,
        order.value,
        distinctEmails.value
    );
    validations.value = data.validations;
    total.value = data.pagination.total;
    isLoading.value = false;
}

function updateLimit(newLimit: number) {
    if (limit.value !== newLimit) {
        limit.value = newLimit;
        offset.value = 0;
        loadValidations();
    }
}
function updateOffset(newOffset: number) {
    if (offset.value !== newOffset) {
        offset.value = newOffset;
        loadValidations();
    }
}
function updateQ(newQ: string) {
    if (q.value !== newQ) {
        q.value = newQ;
        offset.value = 0;
        loadValidations();
    }
}
function updateSort(newSort: string) {
    if (sort.value !== newSort) {
        sort.value = newSort;
        offset.value = 0;
        loadValidations();
    }
}
function updateOrder(newOrder: string) {
    if (order.value !== newOrder) {
        order.value = newOrder;
        offset.value = 0;
        loadValidations();
    }
}
function updateDistinctEmails(val: boolean) {
    distinctEmails.value = val;
    offset.value = 0;
    loadValidations();
}

onMounted(loadValidations);
</script>

<template>
    <div>
        <h1>Validations</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
            <div class="mb-2 d-flex gap-3 align-items-center justify-content-center">
                <label class="form-check-label">
                    <input type="checkbox" class="form-check-input" v-model="distinctEmails"
                        @change="updateDistinctEmails(distinctEmails)" />
                    Show only distinct emails
                </label>
            </div>
            <PaginationControls class="mb-3" :total="total" :limit="limit" :offset="offset" :q="q" :sort="sort"
                :order="order" :sortOptions="sortOptions" @update:limit="updateLimit" @update:offset="updateOffset"
                @update:q="updateQ" @update:sort="updateSort" @update:order="updateOrder" />

            <ValidationListComponent :validations="validations" :total="total" />

            <PaginationControls class="mt-3" :total="total" :limit="limit" :offset="offset" :q="q" :sort="sort"
                :order="order" :sortOptions="sortOptions" @update:limit="updateLimit" @update:offset="updateOffset"
                @update:q="updateQ" @update:sort="updateSort" @update:order="updateOrder" />
        </template>
    </div>
</template>

<style scoped></style>