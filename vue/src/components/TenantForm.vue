<template>
  <!-- Main tenant form -->
  <el-form
    v-if="tenant"
    :model="tenant"
    label-position="top"
    @keydown.enter.prevent="isEditing && handleSave()"
    @keydown.esc.prevent="isEditing && handleCancelEdit()"
  >
    <el-form-item label="Tenant name">
      <el-input v-model="tenant.tenant_name" :disabled="!isEditing" />
    </el-form-item>
    <el-form-item label="URL">
      <el-input v-model="tenant.url" :disabled="!isEditing" />
    </el-form-item>
    <el-form-item label="Include ID">
      <el-input v-model="tenant.include_id" :disabled="!isEditing" />
    </el-form-item>
    <el-form-item label="Key">
      <el-input v-model="tenant.key" :disabled="!isEditing" />
    </el-form-item>
    <el-form-item label="Local directory" type="text">
      <el-input v-model="tenant.local_directory" :disabled="!isEditing">
        <template v-if="isEditing" #append>
          <el-button :icon="Folder" @click="handleAskDirectory" />
        </template>
      </el-input>
    </el-form-item>

    <el-row justify="end" class="action-buttons">
      <!-- Buttons -->
      <el-col>
        <el-space>
          <el-button v-if="!isEditing" type="primary" :icon="Download" @click="handleFetch" round
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
            :disabled="!tenantIsValid"
            type="primary"
            :icon="Check"
            @click="handleSave"
            round
            >Save</el-button
          >
          <el-button v-if="isEditing" type="info" :icon="Close" @click="handleCancelEdit" round
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
            <el-icon size="48" class="opening-state-icon"><Download /></el-icon>
            <el-text size="large" tag="h2">CRMScript Fetcher</el-text>
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
    v-if="tenant"
    title="Fetch Options"
    v-model="fetchOptionsDialogVisible"
    width="30%"
    id="fetch-options-dialog"
  >
    <el-form :model="tenant.fetch_options" label-position="left" label-width="180px">
      <el-form-item label="Fetch Scripts">
        <el-switch v-model="tenant.fetch_options.fetch_scripts" />
      </el-form-item>
      <el-form-item label="Fetch Triggers">
        <el-switch v-model="tenant.fetch_options.fetch_triggers" />
      </el-form-item>
      <el-form-item label="Fetch Screens">
        <el-switch v-model="tenant.fetch_options.fetch_screens" />
      </el-form-item>
      <el-form-item label="Fetch Screen Choosers">
        <el-switch v-model="tenant.fetch_options.fetch_screen_choosers" />
      </el-form-item>
      <el-form-item label="Fetch Scheduled Tasks">
        <el-switch v-model="tenant.fetch_options.fetch_scheduled_tasks" />
      </el-form-item>
      <el-form-item label="Fetch Extra Tables">
        <el-switch v-model="tenant.fetch_options.fetch_extra_tables" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button round type="primary" @click="handleSaveFetchOptions">Save</el-button>

      <el-button round @click="fetchOptionsDialogVisible = false">Cancel</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import type { TenantSettings } from "@/types/TenantSettings"
import { computed, ref, type ComputedRef, type PropType, type Ref } from "vue"
import {
  Edit,
  Check,
  Close,
  Download,
  Delete,
  More,
  FolderOpened,
  Setting,
  Folder,
} from "@element-plus/icons-vue"
import { ElMessage, ElMessageBox, ElLoading } from "element-plus"
import { useEel } from "@/composables/useEel"
import type { FetchResult } from "@/types/FetchResult"
import type { LoadingInstance } from "element-plus/es/components/loading/src/loading.mjs"

// Emits
const emit = defineEmits<{
  "tenant-created": [tenant: TenantSettings]
  "tenant-deleted": [tenant: TenantSettings]
}>()

// Model definitions
const tenant = defineModel("tenant", {
  required: true,
  type: [Object, null] as PropType<TenantSettings | null>,
})

const isEditing = defineModel("isEditing", {
  required: true,
  type: Boolean,
})

// Props
const props = defineProps({
  tenants: {
    required: true,
    type: Array as PropType<TenantSettings[]>,
  },
})

// Refs
const fetchOptionsDialogVisible: Ref<boolean> = ref(false)
const tenantBackup: Ref<TenantSettings | null> = ref(null)

// useEel let's us call the Python methods
const eel = useEel()

// Computed properties
const tenantIsValid: ComputedRef<boolean> = computed(() => {
  return Boolean(
    tenant.value &&
      tenant.value.tenant_name &&
      tenant.value.url &&
      tenant.value.include_id &&
      tenant.value.key &&
      tenant.value.local_directory,
  )
})

const tenantIsNew: ComputedRef<boolean> = computed(() => {
  return tenant.value?.id === 0
})

// Methods
async function handleFetch() {
  if (!tenant.value) return

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
    const result: FetchResult = await eel.fetch(tenant.value)

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

function handleEdit() {
  isEditing.value = true

  // Backup the tenant data to be able to restore it if the user cancels the edit
  tenantBackup.value = JSON.parse(JSON.stringify(tenant.value))
}

/** Creates or updates the tenant */
async function handleSave() {
  if (!isEditing.value || !tenant.value || !tenantIsValid.value) return

  // Remove all trailing slashes from URL
  tenant.value.url = tenant.value.url.replace(/\/+$/, "")

  if (tenantIsNew.value) {
    // Creating new tenant
    tenant.value = await eel.addTenant(tenant.value)
    emit("tenant-created", tenant.value)
    ElMessage.success("Tenant created")
  } else {
    // Updating existing tenant
    await eel.updateTenant(tenant.value)
    ElMessage.success("Tenant updated")
  }

  tenantBackup.value = null
  isEditing.value = false
}

function handleCancelEdit() {
  // Restore the tenant data from the backup
  if (tenantBackup.value) {
    tenant.value = JSON.parse(JSON.stringify(tenantBackup.value))
  } else {
    // Tenant was not created yet, so set it to null
    tenant.value = null
  }
  isEditing.value = false
}

// Checks if the directory is already used, and if so returns the name of the tenant that uses it
async function checkIfDirectoryIsUsed(directoryPath: string): Promise<string> {
  for (const tenant of props.tenants) {
    if (tenant.local_directory === directoryPath) {
      return tenant.tenant_name
    }
  }
  return ""
}

/** Opens the directory in the operating system's file explorer */
async function handleOpenDirectory() {
  if (!tenant.value) return

  document.body.style.cursor = "wait"
  await eel.openDirectory(tenant.value.local_directory)
  document.body.style.cursor = "default"
}

async function handleAskDirectory() {
  if (!tenant.value) return

  // Make Python ask user for the directory path
  ElMessage.info("Opening directory chooser...")
  const directoryPath: string = await eel.askDirectoryPath()

  // If user clicked cancel, directory path is returned as empty array for some reason?
  // This check makes sure they actually chose a path
  if (typeof directoryPath !== "string" || !directoryPath) return

  // Check if the directory is already used by another tenant
  const otherTenantName: string = await checkIfDirectoryIsUsed(directoryPath)

  if (otherTenantName) {
    ElMessage.error(`Could not set directory. Directory is already used by ${otherTenantName}`)
    return
  }

  // Set the directory path
  tenant.value.local_directory = directoryPath
}

function handleFetchOptions() {
  fetchOptionsDialogVisible.value = true
}

function handleSaveFetchOptions() {
  if (!tenant.value) return
  eel.updateTenant(tenant.value)
  fetchOptionsDialogVisible.value = false
}

async function handleDeleteTenant() {
  if (!tenant.value) {
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
    await eel.deleteTenant(tenant.value.id)
    emit("tenant-deleted", tenant.value) // To remove the tenant from the list

    // Reset selectedtenant and potential edit state
    tenant.value = null
    isEditing.value = false
    tenantBackup.value = null

    ElMessage.success("Tenant deleted")
  } catch {
    // User cancelled
  }
}
</script>

<style scoped>
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
