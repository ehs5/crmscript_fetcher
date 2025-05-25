vue
<template>
  <el-container class="app-container">
    <el-header class="header">
      <el-row align="middle" style="height: 100%">
        <el-col :span="24">
          <h1 class="app-title">CRMScript Fetcher</h1>
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
                  ref="tenantTableRef"
                  :data="filteredTenants"
                  @row-click="handleRowClick"
                  :highlight-current-row="true"
                  :default-sort="{ prop: 'tenant_name', order: 'ascending' }"
                  class="tenant-table"
                >
                  <el-table-column prop="tenant_name" label="Tenants" sortable />
                </el-table>
              </el-col>
            </el-row>
          </div>
          <el-footer id="tenant-list-footer" height="auto">
            <el-row>
              <el-col :span="24">
                <el-space>
                  <el-button
                    type="primary"
                    round
                    :icon="Plus"
                    @click="handleNewTenant"
                    :disabled="isEditing"
                    >New</el-button
                  >
                  <el-button type="info" :icon="DocumentCopy" @click="handleCopyFetcherScript" round
                    >Copy Fetcher Script</el-button
                  >
                </el-space>
              </el-col>
            </el-row>
          </el-footer>
        </el-container>
      </el-aside>

      <el-main>
        <TenantForm
          v-model:tenant="selectedTenant"
          v-model:isEditing="isEditing"
          :tenants="tenants"
          @tenant-created="handleTenantCreatedEvent"
          @tenant-deleted="handleTenantDeletedEvent"
        />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted, ref, type Ref, computed, type ComputedRef, watch } from "vue"
import type { TenantSettings } from "./types/TenantSettings"
import { DocumentCopy, Search, Plus } from "@element-plus/icons-vue"
import { ElMessage, ElTable } from "element-plus"
import { useEel } from "@/composables/useEel"
import TenantForm from "./components/TenantForm.vue"

// Refs
const tenants: Ref<TenantSettings[]> = ref([])
const selectedTenant: Ref<TenantSettings | null> = ref(null)
const searchQuery: Ref<string> = ref("")
const isEditing: Ref<boolean> = ref(false)
const tenantTableRef = ref<InstanceType<typeof ElTable> | null>(null)

// useEel let's us call the Python methods
const eel = useEel()

// Computed properties
/**
 * This is the tenants that is actually displayed in the left side of the screen.
 * Uses searchQuery ref to filter tenants by both name and URL.
 */
const filteredTenants: ComputedRef<TenantSettings[]> = computed(() => {
  if (!searchQuery.value) return tenants.value

  const query: string = searchQuery.value.toLowerCase()

  return tenants.value.filter(
    (tenant) =>
      tenant.tenant_name.toLowerCase().includes(query) || tenant.url.toLowerCase().includes(query),
  )
})

// Watchers
/** Watches for changes in selectedTenant and updates the current row in the table */
watch(
  () => selectedTenant.value?.id,
  () => tenantTableRef.value?.setCurrentRow(selectedTenant.value),
)

// Calls Python which loads tenant settings from JSON
async function getTenantSettings(): Promise<TenantSettings[]> {
  return await eel.getAllTenants()
}

function handleRowClick(row: TenantSettings) {
  if (isEditing.value) {
    ElMessage.info("You cannot select another tenant while editing")
    tenantTableRef.value?.setCurrentRow(selectedTenant.value) // Reset the current row to the selected tenant
    return
  }
  selectedTenant.value = row
  tenantTableRef.value?.setCurrentRow(selectedTenant.value) // Reset the current row to the selected tenant
}

/**
 * Is called when a new tenant has been created in TenantForm.
 * Adds the new tenant to the list.
 */
function handleTenantCreatedEvent(tenant: TenantSettings) {
  tenants.value.push(tenant)
  tenantTableRef.value?.setCurrentRow(tenant)
}

/** Deletes the tenant from the list */
function handleTenantDeletedEvent(tenant: TenantSettings) {
  tenants.value = tenants.value.filter((t) => t.id !== tenant.id)
  tenantTableRef.value?.setCurrentRow(null)
}

function getDefaultTenant(): TenantSettings {
  return {
    id: 0,
    tenant_name: "",
    url: "https://online.superoffice.com/CustXXXXX/CS",
    include_id: "crmscript-fetcher",
    key: "",
    local_directory: "",
    fetch_options: {
      fetch_scripts: true,
      fetch_triggers: true,
      fetch_screens: true,
      fetch_screen_choosers: true,
      fetch_scheduled_tasks: true,
      fetch_extra_tables: true,
    },
  }
}

/** Create a new tenant (in screen, not in actual JSON) and sets it as the selected tenant */
function handleNewTenant() {
  selectedTenant.value = getDefaultTenant()
  tenantTableRef.value?.setCurrentRow(null)
  isEditing.value = true
}

/** Gets CRMScript Fetcher from file via Python and copies it to clipboard */
async function handleCopyFetcherScript() {
  const script: string = await eel.getFetcherScript()
  navigator.clipboard.writeText(script)
  ElMessage.success("Fetcher script copied to clipboard")
}

onMounted(async () => {
  tenants.value = await getTenantSettings()
})
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

h1,
h2 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.text-right {
  text-align: right;
}
</style>

<style>
/* Global styles for Element Plus components */
.el-dropdown-menu {
  font-family: "Inter", sans-serif !important;
}

.app-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--el-text-color-secondary);
  margin: 0;
}
</style>
