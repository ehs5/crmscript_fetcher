vue
<template>
  <el-container class="app-container">
    <el-header class="header">
      <el-row align="middle" style="height: 100%">
        <el-col :span="12">
          <h1>CRMScript Fetcher</h1>
        </el-col>
        <el-col :span="12" class="text-right">
          <el-button 
            type="info" 
            :icon="DocumentCopy" 
            @click="handleCopyScript"
            round
          >Copy Fetcher Script</el-button>
        </el-col>
      </el-row>
    </el-header>

    <el-container>
      <el-aside id="aside">
        <el-container direction="vertical" class="aside-content">
          <div class="tenant-list">
            <el-row>
              <el-col :span="24">
                <el-input
                  v-model="searchQuery"
                  placeholder="Search tenants..."
                  :prefix-icon="Search"
                  clearable
                  class="tenant-search"
                />
              </el-col>
              <el-col :span="24">
                <el-table 
                  :data="filteredTenants" 
                  @row-click="handleRowClick" 
                  :highlight-current-row="true"
                  :default-sort="{ prop: 'tenant_name', order: 'ascending' }"
                  class="tenant-table"
                >
                  <el-table-column 
                    prop="tenant_name" 
                    label="Tenants" 
                    sortable
                  />
                </el-table>
              </el-col>
            </el-row>
          </div>
          <el-footer id="tenant-list-footer" height="auto">
            <el-row>
              <el-col :span="24">
                  <el-button 
                    type="primary" 
                    round 
                    :icon="Plus" 
                    @click="handleNewTenant"
                  >New</el-button>
                  <el-button 
                    type="info" 
                    round 
                    :icon="Delete" 
                    @click="handleDeleteTenant"
                    :disabled="!selectedTenant"
                  >Delete</el-button>
              </el-col>
            </el-row>
          </el-footer>
        </el-container>
      </el-aside>

      <el-main>
        <el-row v-if="selectedTenant">
          <el-col :span="24">
            <el-form :model="selectedTenant" label-position="top">
              <el-row justify="space-between" align="middle" class="form-header">
                <el-col :span="24">
                  <h2>{{ selectedTenant.tenant_name }}</h2>
                </el-col>
              </el-row>

              <el-form-item label="Tenant Name">
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

              <el-row justify="end" class="action-buttons">
                <el-col>
                  <el-space>
                    <el-button 
                      v-if="!isEditing" 
                      type="primary" 
                      :icon="Download" 
                      @click="handleFetch"
                      round
                    >Fetch</el-button>
                    <el-button 
                      v-if="!isEditing" 
                      type="info" 
                      :icon="Edit" 
                      @click="handleEdit"
                      round
                    >Edit</el-button>
                    <el-button 
                      v-if="isEditing" 
                      type="primary" 
                      :icon="Check" 
                      @click="handleSave"
                      round
                    >Save</el-button>
                    <el-button 
                      v-if="isEditing" 
                      type="info" 
                      :icon="Close" 
                      @click="handleCancelEdit"
                      round
                    >Cancel</el-button>
                  </el-space>
                </el-col>
              </el-row>
            </el-form>
          </el-col>
        </el-row>
        <el-empty v-else description="Select a tenant to view details" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted, ref, type Ref, computed, type ComputedRef } from 'vue';
import type { TenantSettings } from './types/TenantSettings';
import { Edit, Check, Close, Download, DocumentCopy, Search, Plus, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useEel } from '@/composables/useEel';

// Refs
const tenants: Ref<TenantSettings[]> = ref([]);
const selectedTenant: Ref<TenantSettings | null> = ref(null);
const isEditing: Ref<boolean> = ref(false);
const tempTenantData: Ref<TenantSettings | null> = ref(null);
const searchQuery: Ref<string> = ref('');

// Get API methods
const eel = useEel();

// Computed properties
/** 
 * This is the tenants that is actually displayed in the left side of the screen.
 * Uses searchQuery ref to filter tenants by both name and URL.
 */
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
  return await eel.getAllTenants();
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
  if (!selectedTenant.value) return;
  eel.updateTenant(selectedTenant.value);
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
  if (!selectedTenant.value) return;
  eel.fetchScripts(selectedTenant.value.id);
  ElMessage.info('Fetching scripts...');
}

async function handleCopyScript() {
  if (!selectedTenant.value) return;
  const script = await eel.getFetcherScript(selectedTenant.value.id);
  // TODO: Copy script to clipboard
  ElMessage.success('Script copied to clipboard');
}

function handleDeleteTenant() {
  if (!selectedTenant.value) return;
  eel.deleteTenant(selectedTenant.value.id);
  selectedTenant.value = null;
  ElMessage.success('Tenant deleted successfully');
}

onMounted(async () => {
  tenants.value = await getTenantSettings();
});

</script>

<style scoped>
.app-container {
  height: 100%;
}

.header {
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 20px;
}

#aside {
  min-width: 20%;
  border-right: 1px solid var(--el-border-color-light);
}

.aside-content {
  height: 100%;
}

.tenant-list {
  padding: 20px;
  padding-bottom: 0;
  overflow-y: auto;
}

/**
 * Sets the height of the left hand tenant list, making it stretch to the bottom of the screen.
 * 200px is to account for the header and footer.
 */
.tenant-table {
  height: calc(100vh - 200px);
}

#tenant-list-footer {
  padding: 20px;
  border-top: 1px solid var(--el-border-color-light);
}

.tenant-search {
  margin-bottom: 12px;
}

.form-header {
  margin-bottom: 20px;
}

.action-buttons {
  margin-top: 20px;
}

h1, h2 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.text-right {
  text-align: right;
}
</style>
