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
      <!-- Left side tenant list-->
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
                  :disabled="isEditing"
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

      <!-- Main tenant form -->
      <el-main>
        <el-text v-if="formTenant" size="large" tag="h2" style="min-height: 40px">
          {{ selectedTenant?.tenant_name }}
        </el-text>

        <!-- NOTE: We use formTenant, which switches between tenant and tenantUnderEdit based on if we are in edit mode or not -->
        <el-form
          v-if="formTenant"
          :model="formTenant"
          label-position="top"
          @keydown.enter.prevent="isEditing && handleSave()"
          @keydown.esc.prevent="isEditing && handleCancelEdit()"
        >
          <el-form-item label="Tenant name">
            <el-input v-model="formTenant.tenant_name" :disabled="!isEditing" />
          </el-form-item>
          <el-form-item label="URL">
            <el-input v-model="formTenant.url" :disabled="!isEditing" />
          </el-form-item>
          <el-form-item label="Include ID">
            <el-input v-model="formTenant.include_id" :disabled="!isEditing" />
          </el-form-item>
          <el-form-item label="Key">
            <el-input v-model="formTenant.key" :disabled="!isEditing" />
          </el-form-item>
          <el-form-item label="Local directory" type="text">
            <el-input v-model="formTenant.local_directory" :disabled="!isEditing">
              <template v-if="isEditing" #append>
                <el-button :icon="Folder" @click="handleAskDirectory" />
              </template>
            </el-input>
          </el-form-item>

          <el-row justify="end" class="action-buttons">
            <!-- Tenant action buttons -->
            <el-col>
              <el-space>
                <el-button
                  v-if="!isEditing"
                  type="primary"
                  :icon="Download"
                  @click="handleFetch"
                  round
                  >Fetch</el-button
                >
                <el-button v-if="!isEditing" :icon="Edit" @click="handleEdit" round>Edit</el-button>
                <el-dropdown v-if="!isEditing">
                  <el-button :icon="More" round />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="handleOpenDirectory">
                        <el-icon><FolderOpened /></el-icon>
                        Open Directory
                      </el-dropdown-item>
                      <el-dropdown-item @click="handleFetchOptions">
                        <el-icon><Setting /></el-icon>
                        Fetch Options
                      </el-dropdown-item>
                      <el-dropdown-item divided @click="handleDeleteTenant" type="danger">
                        <el-icon><Delete /></el-icon>
                        Delete
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button
                  v-if="isEditing"
                  :disabled="!tenantUnderEditIsvalid || awaitingFolderInput"
                  type="primary"
                  :icon="Check"
                  @click="handleSave"
                  round
                  >Save</el-button
                >
                <el-button
                  v-if="isEditing"
                  type="info"
                  :icon="Close"
                  @click="handleCancelEdit"
                  :disabled="awaitingFolderInput"
                  round
                  >Cancel</el-button
                >
              </el-space>
            </el-col>
          </el-row>
        </el-form>

        <!-- Opening image/text when no tenant is selected -->
        <el-container v-else class="opening-state">
          <el-main>
            <el-row type="flex" justify="center" align="middle" class="opening-state-row">
              <el-col :span="24">
                <el-space direction="vertical" alignment="center" size="large">
                  <el-image :src="iconImage3" style="width: 100px; height: 100px" />
                  <el-text size="large" tag="h2"> CRMScript Fetcher</el-text>
                  <el-text class="empty-state-description">
                    Select an existing tenant from the list, or create a new one, on the left side.
                  </el-text>
                </el-space>
              </el-col>
            </el-row>
          </el-main>
        </el-container>

        <!-- Fetch options dialog -->
        <el-dialog
          v-if="selectedTenant"
          title="Fetch Options"
          v-model="fetchOptionsDialogVisible"
          width="30%"
          id="fetch-options-dialog"
        >
          <el-form :model="selectedTenant.fetch_options" label-position="left" label-width="180px">
            <el-form-item label="Fetch Scripts">
              <el-switch v-model="selectedTenant.fetch_options.fetch_scripts" />
            </el-form-item>
            <el-form-item label="Fetch Triggers">
              <el-switch v-model="selectedTenant.fetch_options.fetch_triggers" />
            </el-form-item>
            <el-form-item label="Fetch Screens">
              <el-switch v-model="selectedTenant.fetch_options.fetch_screens" />
            </el-form-item>
            <el-form-item label="Fetch Screen Choosers">
              <el-switch v-model="selectedTenant.fetch_options.fetch_screen_choosers" />
            </el-form-item>
            <el-form-item label="Fetch Scheduled Tasks">
              <el-switch v-model="selectedTenant.fetch_options.fetch_scheduled_tasks" />
            </el-form-item>
            <el-form-item label="Fetch Extra Tables">
              <el-switch v-model="selectedTenant.fetch_options.fetch_extra_tables" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button round type="primary" @click="handleSaveFetchOptions">Save</el-button>

            <el-button round @click="fetchOptionsDialogVisible = false">Cancel</el-button>
          </template>
        </el-dialog>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted, ref, type Ref, computed, type ComputedRef, watch } from "vue"
import type { TenantSettings } from "./types/TenantSettings"
/*
import iconImage from "@/assets/icon.png"
import iconImage2 from "@/assets/icon2.png"
*/
import iconImage3 from "@/assets/icon3.png"
import {
  DocumentCopy,
  Search,
  Plus,
  Folder,
  Download,
  Edit,
  More,
  Check,
  Close,
  FolderOpened,
  Setting,
  Delete,
} from "@element-plus/icons-vue"
import { ElLoading, ElMessage, ElMessageBox, ElTable } from "element-plus"
import { useEel } from "@/composables/useEel"
import type { LoadingInstance } from "element-plus/es/components/loading/src/loading.mjs"
import type { FetchResult } from "./types/FetchResult"

// Refs
const allTenants: Ref<TenantSettings[]> = ref([]) // All the tenants in JSON file. See filteredTenants for the tenants that are displayed in the left side of the screen.
const selectedTenant: Ref<TenantSettings | null> = ref(null)
const tenantUnderEdit: Ref<TenantSettings | null> = ref(null)
const searchQuery: Ref<string> = ref("")
const isEditing: Ref<boolean> = ref(false)
const awaitingFolderInput: Ref<boolean> = ref(false)
const fetchOptionsDialogVisible: Ref<boolean> = ref(false)
const tenantTableRef = ref<InstanceType<typeof ElTable> | null>(null)

// useEel let's us call the Python methods
const eel = useEel()

// Computed properties
/**
 * This is the tenants that is actually displayed in the left side of the screen.
 * Uses searchQuery ref to filter tenants by both name and URL.
 */
const filteredTenants: ComputedRef<TenantSettings[]> = computed(() => {
  if (!searchQuery.value) return allTenants.value

  const query: string = searchQuery.value.toLowerCase()

  return allTenants.value.filter(
    (tenant) =>
      tenant.tenant_name.toLowerCase().includes(query) || tenant.url.toLowerCase().includes(query),
  )
})

/** Switches the tenant set in form based on if we are in edit mode or not */
const formTenant: ComputedRef<TenantSettings | null> = computed(() => {
  return isEditing.value ? tenantUnderEdit.value : selectedTenant.value
})

/** Makes sure all fields are filled in when editing */
const tenantUnderEditIsvalid: ComputedRef<boolean> = computed(() => {
  return Boolean(
    tenantUnderEdit.value &&
      tenantUnderEdit.value.tenant_name &&
      tenantUnderEdit.value.url &&
      tenantUnderEdit.value.include_id &&
      tenantUnderEdit.value.key &&
      tenantUnderEdit.value.local_directory,
  )
})

// Watchers

/**
 * Updates the current row in the table when selectedTenant changes, this highlights the row in the table.
 *
 * When restoring tenant from backup (when canceling edit), a new object is created with the same data.
 * The table needs the original object from its data to highlight the row,
 * so we find it in filteredTenants (which is the same as the table's data).
 */
watch(
  () => selectedTenant.value,
  (currentTenant) => {
    if (!currentTenant) {
      tenantTableRef.value?.setCurrentRow(null)
      return
    }

    // Find the original object in the table's data that matches our current tenant
    const matchingTenant: TenantSettings | null =
      filteredTenants.value.find((t) => t.id === currentTenant.id) ?? null

    tenantTableRef.value?.setCurrentRow(matchingTenant)
    console.log("Watcher set current row to", matchingTenant)
  },
  { deep: true },
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

/** Returns tenant object with default values */
function createDefaultTenant(): TenantSettings {
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
  selectedTenant.value = createDefaultTenant()
  tenantUnderEdit.value = createDefaultTenant()
  isEditing.value = true
}

/** Gets CRMScript Fetcher from file via Python and copies it to clipboard */
async function handleCopyFetcherScript() {
  const script: string = await eel.getFetcherScript()
  navigator.clipboard.writeText(script)
  ElMessage.success("Fetcher script copied to clipboard")
}

async function handleFetch() {
  if (!selectedTenant.value) return

  let loadingInstance: LoadingInstance | null = null

  try {
    // First show warning dialog.
    await ElMessageBox.confirm(
      "You are about to fetch data from SuperOffice.<br><br>" +
        "Note: Any files or folders inside folders generated by CRMScript Fetcher that are not present in Superoffice will be deleted.<br><br>" +
        "Do you want to continue?",
      "Fetch data",
      {
        confirmButtonText: "Fetch",
        cancelButtonText: "Cancel",
        type: "warning",
        confirmButtonClass: "el-button--primary",
        cancelButtonClass: "el-button--default",
        roundButton: true,
        dangerouslyUseHTMLString: true,
      },
    )

    // User clicked Fetch, set loading overlay.
    loadingInstance = ElLoading.service({
      text: "Fetching data from SuperOffice...",
      background: "rgba(0, 0, 0, 0.7)",
    })

    document.body.style.cursor = "wait"
    const result: FetchResult = await eel.fetch(selectedTenant.value)

    // Reset cursor and close loading overlay
    document.body.style.cursor = "default"
    loadingInstance.close()

    // Handle validation errors.
    if (result.validation_error) {
      await ElMessageBox.alert(result.error, "Validation Error", {
        type: "error",
        roundButton: true,
        dangerouslyUseHTMLString: true,
      })
      return
    }

    // Handle general errors.
    if (!result.success) {
      await ElMessageBox.alert(result.error, "Error", {
        type: "error",
        roundButton: true,
        dangerouslyUseHTMLString: true,
      })
      return
    }

    // Fetch was succesful.
    // Handle success (show info first if exists, this only happens on invalid crmscript version).
    if (result.info) {
      await ElMessageBox.alert(result.info, "Note", {
        type: "warning",
        roundButton: true,
        dangerouslyUseHTMLString: true,
      })
    }

    ElMessage.success("Fetch successful!")
  } catch (error) {
    // Reset cursor and close loading overlay
    document.body.style.cursor = "default"
    if (loadingInstance) loadingInstance.close()

    // User clicked Cancel or closed the dialog
    if (error === "cancel" || error === "close") return

    // Unexpected error
    await ElMessageBox.alert(`An unexpected error occurred: ${error}`, "Error", {
      type: "error",
      roundButton: true,
      dangerouslyUseHTMLString: true,
    })
  }
}

/** Handles Edit button click. */
function handleEdit() {
  // Create a copy of the tenant - this copy is the one we will be editing
  tenantUnderEdit.value = JSON.parse(JSON.stringify(selectedTenant.value))
  isEditing.value = true
}

/**
 * Checks if the directory is already used,
 * and if so returns the name of the tenant that uses it
 */
async function directoryIsTaken(currentTenantId: number, directoryPath: string): Promise<string> {
  const normalizedPath = directoryPath.toLowerCase()

  const existingTenant = allTenants.value.find(
    (tenant) =>
      tenant.id !== currentTenantId && tenant.local_directory.toLowerCase() === normalizedPath,
  )
  return existingTenant ? existingTenant.tenant_name : ""
}

/** Creates or updates the tenant */
async function handleSave() {
  // Check for invalid state
  if (!isEditing.value) throw new Error("Not in edit mode")
  if (!tenantUnderEdit.value) throw new Error("No tenant under edit")
  if (!selectedTenant.value) throw new Error("No tenant selected")
  if (!tenantUnderEditIsvalid.value) throw new Error("Invalid tenant")

  // Remove all trailing slashes from URL
  tenantUnderEdit.value.url = tenantUnderEdit.value.url.replace(/\/+$/, "")

  // Make sure no other tenant has the same directory
  const otherTenantName: string = await directoryIsTaken(
    tenantUnderEdit.value.id,
    tenantUnderEdit.value.local_directory,
  )

  if (otherTenantName) {
    ElMessage.error(`Could not save tenant. Local directory is already used by ${otherTenantName}`)
    return
  }

  if (tenantUnderEdit.value.id > 0) {
    // Updating existing tenant
    await eel.updateTenant(tenantUnderEdit.value)
  } else {
    // Creating new tenant
    tenantUnderEdit.value = await eel.addTenant(tenantUnderEdit.value)
    allTenants.value.push(tenantUnderEdit.value)
    tenantTableRef.value?.setCurrentRow(tenantUnderEdit.value)
    ElMessage.success("Tenant created")
  }

  // Replace values in "selectedTenant" with values in "tenantUnderEdit"
  Object.assign(selectedTenant.value, tenantUnderEdit.value)
  tenantUnderEdit.value = null
  isEditing.value = false
}

/** Handles Cancel button click. */
function handleCancelEdit() {
  // Nullify tenantUnderEdit. Computed property formTenant will switch to selectedTenant
  tenantUnderEdit.value = null
  isEditing.value = false

  // For new tenants, null out selectedTenant too
  if (selectedTenant.value?.id === 0) {
    selectedTenant.value = null
  }
}

async function handleAskDirectory() {
  if (!tenantUnderEdit.value) return

  // Make Python ask user for the directory path
  ElMessage.info("Opening directory chooser...")
  awaitingFolderInput.value = true
  const directoryPath: string = await eel.askDirectoryPath()

  // If user clicked cancel, directory path is returned as empty array for some reason?
  // This check makes sure user actually chose a path
  if (typeof directoryPath === "string" && directoryPath) {
    tenantUnderEdit.value.local_directory = directoryPath
  }

  awaitingFolderInput.value = false
}

/** Opens the directory in the operating system's file explorer */
async function handleOpenDirectory() {
  if (!selectedTenant.value) return

  document.body.style.cursor = "wait"
  await eel.openDirectory(selectedTenant.value.local_directory)
  document.body.style.cursor = "default"
}

function handleFetchOptions() {
  fetchOptionsDialogVisible.value = true
}

/** Fetch Options is not part of editing mode, so this uses "selectedTenant" instead of tenantUnderEdit */
function handleSaveFetchOptions() {
  if (!selectedTenant.value) return
  eel.updateTenant(selectedTenant.value)
  fetchOptionsDialogVisible.value = false
  ElMessage.success("Fetch options saved")
}

async function handleDeleteTenant() {
  if (!selectedTenant.value) {
    throw new Error("No tenant selected") // This should never happen
  }

  try {
    await ElMessageBox.confirm("Are you sure you want to delete this tenant?", "Warning", {
      confirmButtonText: "Delete",
      cancelButtonText: "Cancel",
      type: "warning",
      confirmButtonClass: "el-button--danger",
      roundButton: true,
    })

    // User confirmed
    await eel.deleteTenant(selectedTenant.value.id)

    // Remove the tenant from the list
    const selectedTenantId: number = selectedTenant.value.id
    allTenants.value = allTenants.value.filter((t) => t.id !== selectedTenantId)
    tenantTableRef.value?.setCurrentRow(null)

    // Reset selectedtenant and potential edit state
    selectedTenant.value = null
    tenantUnderEdit.value = null
    isEditing.value = false

    ElMessage.success("Tenant deleted")
  } catch {
    // User cancelled
  }
}

onMounted(async () => {
  allTenants.value = await getTenantSettings()

  // Inject CRMScript Fetcher version into the page title
  const currentVersion: string = await eel.getCurrentVersion()
  document.title = `CRMScript Fetcher v${currentVersion}`
})
</script>

<style scoped>
.app-container {
  height: 100%;
}

.header {
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

#aside {
  min-width: 25%;
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

.input-with-button {
  display: flex;
  gap: 8px;
}

.input-with-button .el-input {
  flex: 1;
}

/** Reverses the order of the buttons in the message box */
:deep(.el-message-box__btns) {
  flex-direction: row-reverse;
}

.opening-state,
.opening-state-row {
  height: 100%;
  text-align: center;
}

.opening-state-icon {
  color: var(--el-color-primary);
}
</style>
