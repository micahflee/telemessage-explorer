<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { useRoute } from 'vue-router';
import { type ValidationDetails } from '@/types.ts';
import { API } from '@/api.ts';

const route = useRoute();
const validationId = Number(route.params.validationId);

const api = inject('api') as API;
const isLoading = ref(true);
const validationDetails = ref<ValidationDetails>();

onMounted(async () => {
    isLoading.value = true;
    validationDetails.value = await api.getValidation(validationId);
    isLoading.value = false;
});
</script>

<template>
    <div>
        <h1>Validation: {{ validationDetails?.validation.email }}</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
            <template v-if="!validationDetails">
                <h2 class="text-muted text-center">Validation not found</h2>
            </template>
            <template v-else>
                <h3>Details</h3>
                <ul>
                    <li>
                        ID: <strong>{{ validationDetails.validation.id }}</strong>
                    </li>
                    <li>
                        Username: <strong>{{ validationDetails.validation.username }}</strong>
                    </li>
                    <li>
                        Email: <strong>{{ validationDetails.validation.email }}</strong>
                    </li>
                    <li>
                        Domain: <strong>{{ validationDetails.validation.email_domain }}</strong>
                    </li>
                    <li>
                        Provider: <strong>{{ validationDetails.validation.active_identity_provider }}</strong>
                    </li>
                </ul>
            </template>
        </template>
    </div>
</template>

<style scoped></style>
