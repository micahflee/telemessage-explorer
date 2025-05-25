<template>
  <div class="pagination-controls d-flex align-items-center gap-2 flex-wrap">
    <input
      type="search"
      class="form-control form-control-sm w-auto"
      placeholder="Search"
      v-model="localQ"
      @change="changeQ"
      @keyup.enter="changeQ"
      style="min-width: 180px;"
    />

    <span class="ms-2">Sort by:</span>
    <select v-model="localSort" @change="changeSort" class="form-select form-select-sm w-auto">
      <option v-for="option in sortOptions" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>

    <select v-model="localOrder" @change="changeOrder" class="form-select form-select-sm w-auto">
      <option value="asc">Asc</option>
      <option value="desc">Desc</option>
    </select>

    <button class="btn btn-secondary btn-sm" @click="prevPage" :disabled="offset === 0">Previous</button>
    <span>
      Page {{ currentPage }} of {{ totalPages }}
    </span>
    <button class="btn btn-secondary btn-sm" @click="nextPage" :disabled="offset + limit >= total">Next</button>
    <span class="ms-3">Per page:</span>
    <select v-model.number="localLimit" @change="changeLimit" class="form-select form-select-sm w-auto">
      <option v-for="option in limitOptions" :key="option" :value="option">{{ option }}</option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  total: number,
  limit: number,
  offset: number,
  q: string,
  sort: string,
  order: string,
  sortOptions: { value: string, label: string }[],
  limitOptions?: number[]
}>();
const emit = defineEmits([
  'update:limit',
  'update:offset',
  'update:q',
  'update:sort',
  'update:order'
]);

const limitOptions = props.limitOptions ?? [20, 100, 200, 500, 1000];

const localLimit = ref(props.limit);
const localQ = ref(props.q);
const localSort = ref(props.sort);
const localOrder = ref(props.order);

watch(() => props.limit, (newLimit) => { localLimit.value = newLimit; });
watch(() => props.q, (newQ) => { localQ.value = newQ; });
watch(() => props.sort, (newSort) => { localSort.value = newSort; });
watch(() => props.order, (newOrder) => { localOrder.value = newOrder; });

const currentPage = computed(() => Math.floor(props.offset / props.limit) + 1);
const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)));

function prevPage() {
  if (props.offset - props.limit >= 0) {
    emit('update:offset', props.offset - props.limit);
  }
}
function nextPage() {
  if (props.offset + props.limit < props.total) {
    emit('update:offset', props.offset + props.limit);
  }
}
function changeLimit() {
  emit('update:limit', localLimit.value);
  emit('update:offset', 0); // Reset to first page when limit changes
}
function changeQ() {
  emit('update:q', localQ.value);
  emit('update:offset', 0); // Reset to first page when searching
}
function changeSort() {
  emit('update:sort', localSort.value);
  emit('update:offset', 0);
}
function changeOrder() {
  emit('update:order', localOrder.value);
  emit('update:offset', 0);
}
</script>

<style scoped>
.pagination-controls {
  justify-content: center;
  flex-wrap: wrap;
}
</style>