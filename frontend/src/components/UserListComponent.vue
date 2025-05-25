<script setup lang="ts">
import { type User } from '@/types.ts';

defineProps<{
    total: number;
    users: User[];
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
                        <th class="text-nowrap">Type</th>
                        <th class="text-nowrap">Value</th>
                        <th class="text-nowrap">First Name</th>
                        <th class="text-nowrap">Last Name</th>
                        <th class="text-nowrap">Groups</th>
                        <th class="text-nowrap">Messages</th>
                    </tr>
                </thead>
                <tbody class="list">
                    <tr v-if="total === 0">
                        <td colspan="8" class="text-center">No users found</td>
                    </tr>
                    <tr v-for="user in users" :key="user.id">
                        <td class="id">
                            <router-link :to="`/users/${user.id}`" class="btn btn-secondary btn-sm">{{ user.id
                                }}</router-link>
                        </td>
                        <td class="type">{{ user.type }}</td>
                        <td class="value">{{ user.value }}</td>
                        <td class="first_name">{{ user.first_name }}</td>
                        <td class="last_name">{{ user.last_name }}</td>
                        <td class="group_count">{{ user.group_count.toLocaleString() }}</td>
                        <td class="message_count">{{ user.message_count.toLocaleString() }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<style></style>