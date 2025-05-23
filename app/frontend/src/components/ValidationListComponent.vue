<script setup lang="ts">
import { type Validation } from '@/types.ts';

defineProps<{
    total: number;
    validations: Validation[];
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
                        <th class="text-nowrap">Username</th>
                        <th class="text-nowrap">Email</th>
                        <th class="text-nowrap">Domain</th>
                        <th class="text-nowrap">Provider</th>
                        <th class="text-nowrap">Users</th>
                        <th class="text-nowrap">Messages</th>
                        <th class="text-nowrap">Groups</th>
                    </tr>
                </thead>
                <tbody class="list">
                    <tr v-if="total === 0">
                        <td colspan="8" class="text-center">No validations found</td>
                    </tr>
                    <tr v-for="validation in validations" :key="validation.id">
                        <td class="id">
                            <router-link :to="`/validations/${validation.id}`" class="btn btn-secondary btn-sm">{{
                                validation.id }}</router-link>
                        </td>
                        <td class="username">{{ validation.username }}</td>
                        <td class="email">{{ validation.email }}</td>
                        <td class="email_domain">{{ validation.email_domain }}</td>
                        <td class="active_identity_provider">{{ validation.active_identity_provider }}</td>
                        <td class="user_count">{{ validation.user_count.toLocaleString() }}</td>
                        <td class="message_count">{{ validation.message_count.toLocaleString() }}</td>
                        <td class="group_count">{{ validation.group_count.toLocaleString() }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<style></style>