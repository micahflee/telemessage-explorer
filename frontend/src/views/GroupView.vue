<script setup lang="ts">
import { onMounted, ref, inject } from 'vue'
import { useRoute } from 'vue-router';
import { type GroupDetails } from '@/types.ts';
import { API } from '@/api.ts';

import UserListComponent from '@/components/UserListComponent.vue';
import MessageListComponent from '@/components/MessageListComponent.vue';

const route = useRoute();
const groupId = Number(route.params.groupId);

const api = inject('api') as API;
const isLoading = ref(true);
const groupDetails = ref<GroupDetails>();

onMounted(async () => {
    isLoading.value = true;
    groupDetails.value = await api.getGroup(groupId);
    isLoading.value = false;
});
</script>

<template>
    <div>
        <h1>Group: {{ groupDetails?.group.group_name }}</h1>

        <template v-if="isLoading">
            <h2 class="text-muted text-center">Loading...</h2>
        </template>
        <template v-else>
            <template v-if="!groupDetails">
                <h2 class="text-muted text-center">Group not found</h2>
            </template>
            <template v-else>
                <h3>Details</h3>
                <ul>
                    <li>
                        ID: <strong>{{ groupDetails.group.id }}</strong>
                    </li>
                    <li>
                        Group Name: <strong>{{ groupDetails.group.group_name }}</strong>
                    </li>
                    <li>
                        Source Type: <strong>{{ groupDetails.group.source_type }}</strong>
                    </li>
                    <li>
                        Network Type: <strong>{{ groupDetails.group.network_type }}</strong>
                    </li>
                </ul>

                <h3>Users</h3>
                <UserListComponent :users="groupDetails.users" :total="groupDetails.users.length" />

                <h3>Messages</h3>
                <MessageListComponent :messages="groupDetails.messages" :total="groupDetails.messages.length" />
            </template>
        </template>
    </div>
</template>

<style scoped></style>
