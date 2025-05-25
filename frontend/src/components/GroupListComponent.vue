<script setup lang="ts">
import { type Group } from '@/types.ts';

defineProps<{
    total: number;
    groups: Group[];
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
                        <th class="text-nowrap">
                            ID
                        </th>
                        <th class="text-nowrap">
                            Group Name
                        </th>
                        <th class="text-nowrap">
                            Source Type
                        </th>
                        <th class="text-nowrap">
                            Messages
                        </th>
                        <th class="text-nowrap">
                            Users
                        </th>
                    </tr>
                </thead>
                <tbody class="list">
                    <tr v-if="total === 0">
                        <td colspan="5" class="text-center">No groups found</td>
                    </tr>
                    <tr v-for="group in groups" :key="group.id">
                        <td class="id">
                            <router-link :to="`/groups/${group.id}`" class="btn btn-secondary btn-sm">{{ group.id
                                }}</router-link>
                        </td>
                        <td class="group_name">{{ group.group_name }}</td>
                        <td class="source_type">{{ group.source_type }}</td>
                        <td class="message_count">{{ group.message_count.toLocaleString() }}</td>
                        <td class="user_count">{{ group.user_count.toLocaleString() }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<style></style>
