vue
<template>
    <el-container class="app-container">
      <el-header class="header">
        <div class="header-content">
          <h1>CRMScript Fetcher</h1>
          <el-button type="primary" @click="handleNewTenant">New Tenant</el-button>
        </div>
      </el-header>
      <el-container>
        <el-aside id="aside">
          <el-row>
            <el-col :span="24">
              <div class="tenant-header">
                <el-text class="tenant-title">Tenants</el-text>
                <el-input
                  v-model="searchQuery"
                  placeholder="Search tenants..."
                  :prefix-icon="Search"
                  clearable
                  class="tenant-search"
                />
              </div>
            </el-col>
            <el-col :span="24">
              <el-table 
                :data="filteredTenants" 
                @row-click="handleRowClick" 
                :highlight-current-row="true"
                :default-sort="{ prop: 'tenant_name', order: 'ascending' }"
              >
                <el-table-column 
                  prop="tenant_name" 
                  label="Name" 
                  sortable
                />
              </el-table>
            </el-col>
          </el-row>
        </el-aside>
        <el-main>
          <el-form v-if="selectedTenant" :model="selectedTenant" label-position="top">
            <div class="form-header">
              <h2>Tenant Settings</h2>
              <div class="form-actions">
                <el-button-group>
                  <el-button type="primary" :icon="Edit" @click="handleEdit" v-if="!isEditing">Edit</el-button>
                  <el-button type="success" :icon="Check" @click="handleSave" v-if="isEditing">Save</el-button>
                  <el-button type="danger" :icon="Close" @click="handleCancelEdit" v-if="isEditing">Cancel</el-button>
                </el-button-group>
              </div>
            </div>

            <el-form-item label="Tenant Name" >
              <el-input v-model="selectedTenant.tenant_name" :disabled="!isEditing" />
            </el-form-item>
            <el-form-item label="URL">
              <el-input v-model="selectedTenant.url" :disabled="!isEditing" />
            </el-form-item>
            <el-form-item label="Include ID">
              <el-input v-model="selectedTenant.include_id" :disabled="!isEditing" />
            </el-form-item>
            <el-form-item label="Key">
              <el-input v-model="selectedTenant.key" :disabled="!isEditing" />
            </el-form-item>
            <el-form-item label="Local Directory">
              <el-input v-model="selectedTenant.local_directory" :disabled="!isEditing" />
            </el-form-item>

            <div class="action-buttons">
              <el-button-group>
                <el-button type="primary" :icon="Download" @click="handleFetch">Fetch Scripts</el-button>
                <el-button type="info" :icon="DocumentCopy" @click="handleCopyScript">Copy Fetcher Script</el-button>
              </el-button-group>
            </div>
          </el-form>
          <el-empty v-else description="Select a tenant to view details" />
        </el-main>
      </el-container>
    </el-container>
</template>

<script setup lang="ts">
import { onMounted, ref, type Ref, computed, type ComputedRef } from 'vue';
import type { TenantSettings } from './types/TenantSettings';
import { Edit, Check, Close, Download, DocumentCopy, Search } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// Declare eel variable just to let TypeScript know it exists 
// It's imported in index.html.
declare const eel: any;

// Refs
const tenants: Ref<TenantSettings[]> = ref([]);
const selectedTenant: Ref<TenantSettings | null> = ref(null);
const isEditing: Ref<boolean> = ref(false);
const tempTenantData: Ref<TenantSettings | null> = ref(null);
const searchQuery: Ref<string> = ref('');

// Computed properties
const filteredTenants: ComputedRef<TenantSettings[]> = computed(() => {
  if (!searchQuery.value) return tenants.value;
  
  const query: string = searchQuery.value.toLowerCase();

  return tenants.value.filter(tenant => 
    tenant.tenant_name.toLowerCase().includes(query) ||
    tenant.url.toLowerCase().includes(query)
  );
});

// Calls Python which loads tenant settings from JSON
async function getTenantSettings(): Promise<TenantSettings[]> {
  return await eel.get_tenant_settings()();
}

function handleRowClick(row: TenantSettings) {
  if (isEditing.value) return;
  selectedTenant.value = row;
}

function handleEdit() {
  isEditing.value = true;
  tempTenantData.value = JSON.parse(JSON.stringify(selectedTenant.value));
}

function handleSave() {
  // TODO: Implement save functionality
  isEditing.value = false;
  ElMessage.success('Changes saved successfully');
}

function handleCancelEdit() {
  if (tempTenantData.value) {
    selectedTenant.value = JSON.parse(JSON.stringify(tempTenantData.value));
  }
  isEditing.value = false;
}

function handleNewTenant() {
  const newTenant: TenantSettings = {
    id: 0,
    tenant_name: '',
    url: '',
    include_id: '',
    key: '',
    local_directory: '',
    fetch_options: {
      fetch_scripts: false,
      fetch_triggers: false,
      fetch_screens: false,
      fetch_screen_choosers: false,
      fetch_scheduled_tasks: false,
      fetch_extra_tables: false
    }
  };
  selectedTenant.value = newTenant;
  isEditing.value = true;
}

function handleFetch() {
  // TODO: Implement fetch functionality
  ElMessage.info('Fetching scripts...');
}

function handleCopyScript() {
  // TODO: Implement copy script functionality
  ElMessage.success('Script copied to clipboard');
}

onMounted(async () => {
  tenants.value = await getTenantSettings();
});

</script>

<style scoped>
.app-container {
  height: 100vh; /* TODO: Fix height to avoid scrollbar */
}
#aside {
  min-width: 20%;
  border-right: 1px solid var(--el-border-color-light);
  padding: 20px;
}

.header {
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.tenant-header {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tenant-title {
  font-size: 1.2em;
  font-weight: bold;
}

.tenant-search {
  margin-top: 8px;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.form-actions {
  display: flex;
  gap: 10px;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-form-item__label) {
  font-weight: bold;
}

h1 {
  margin: 0;
  color: var(--el-text-color-primary);
}

h2 {
  margin: 0;
  color: var(--el-text-color-primary);
}
</style>
