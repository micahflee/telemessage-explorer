<script setup lang="ts">
import { provide } from 'vue'
import { API } from './api.ts';

const api = new API();
provide('api', api);
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light p-3">
    <a class="navbar-brand" href="#">TeleMessage Explorer</a>
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav"
      aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav">
        <li class="nav-item">
          <router-link to="/" class="nav-link">Groups</router-link>
        </li>
        <li class="nav-item">
          <router-link to="/users" class="nav-link">Users</router-link>
        </li>
        <li class="nav-item">
          <router-link to="/messages" class="nav-link">Messages</router-link>
        </li>
      </ul>
    </div>
  </nav>
  <div class="p-3">
    <router-view />
  </div>
</template>

<style>
.list {
  width: 100%;
  overflow-x: auto;
}

.list table .sortable {
  cursor: pointer;
}
</style>
