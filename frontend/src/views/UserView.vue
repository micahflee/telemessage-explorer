<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { useRoute } from 'vue-router';
import { type UserDetails } from '@/types.ts';
import { API } from '@/api.ts';

import GroupListComponent from '@/components/GroupListComponent.vue';
import MessageListComponent from '@/components/MessageListComponent.vue';

const route = useRoute();
const userId = Number(route.params.userId);

const api = inject('api') as API;
const isLoading = ref(true);
const userDetails = ref<UserDetails>();

onMounted(async () => {
    isLoading.value = true;
    userDetails.value = await api.getUser(userId);
    isLoading.value = false;
});
</script>

<template>
    <div>
        <h1>User: {{ userDetails?.user.value }} ({{ userDetails?.user.type }})</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
            <template v-if="!userDetails">
                <h2 class="text-muted text-center">User not found</h2>
            </template>
            <template v-else>
                <h3>Details</h3>
                <ul>
                    <li>
                        ID: <strong>{{ userDetails.user.id }}</strong>
                    </li>
                    <li>
                        Type: <strong>{{ userDetails.user.type }}</strong>
                    </li>
                    <li>
                        Value: <strong>{{ userDetails.user.value }}</strong>
                    </li>
                    <li>
                        First Name: <strong>{{ userDetails.user.first_name }}</strong>
                    </li>
                    <li>
                        Last Name: <strong>{{ userDetails.user.last_name }}</strong>
                    </li>
                </ul>

                <template v-if="userDetails.groups.length > 0">
                    <h3>Groups</h3>
                    <GroupListComponent :groups="userDetails.groups" :total="userDetails.groups.length" />
                </template>

                <h3>Messages</h3>
                <MessageListComponent :messages="userDetails.messages" :total="userDetails.messages.length" />
            </template>
        </template>
    </div>
</template>

<style scoped></style>
