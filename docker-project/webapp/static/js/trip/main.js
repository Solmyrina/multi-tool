// Main Trip Detail Page Controller
// This file contains core functionality and delegates to specialized modules

// Global variables (set by template)
// - tripId
// - tripCity
// - tripCountry
// - tripStartDate  
// - tripEndDate

let userPermissions = null;
let isOwner = false;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Trip detail main.js initializing...');
    loadTripPermissions();
    setupTabListeners();
});

// Load trip permissions
async function loadTripPermissions() {
    try {
        const response = await fetch(`/api/travel/trips/${tripId}`);
        const data = await response.json();
        
        if (data.success) {
            isOwner = data.trip.is_owner || false;
            userPermissions = data.trip.permissions || {};
            applyPermissionControls();
            
            // Hide budget if no permission
            if (!hasPermission('budget', 'read')) {
                hideBudgetFields();
            }
        }
    } catch (error) {
        console.error('Error loading permissions:', error);
    }
}

// Check if user has specific permission
function hasPermission(category, action) {
    if (isOwner) return true;
    if (!userPermissions || !userPermissions[category]) return false;
    
    const perm = userPermissions[category];
    if (action === 'read') return perm.can_read;
    if (action === 'write') return perm.can_write;
    if (action === 'delete') return perm.can_delete;
    return false;
}

// Apply permission controls to UI
function applyPermissionControls() {
    if (!isOwner) {
        const editTripBtn = document.querySelector('[onclick="editTrip()"]');
        const deleteTripBtn = document.querySelector('[onclick="deleteTrip()"]');
        if (editTripBtn) editTripBtn.style.display = 'none';
        if (deleteTripBtn) deleteTripBtn.style.display = 'none';
    }
    
    if (!hasPermission('activities', 'write')) {
        const addActivityBtn = document.querySelector('[onclick="openActivityModal()"]');
        if (addActivityBtn) addActivityBtn.style.display = 'none';
    }
    
    if (!hasPermission('accommodations', 'write')) {
        const addAccommodationBtn = document.querySelector('[onclick="openAccommodationModal()"]');
        if (addAccommodationBtn) addAccommodationBtn.style.display = 'none';
    }
    
    if (!hasPermission('budget', 'write')) {
        const addExpenseBtn = document.querySelector('[onclick="openExpenseModal()"]');
        if (addExpenseBtn) addExpenseBtn.style.display = 'none';
    }
    
    if (!hasPermission('packing_list', 'write')) {
        const addPackingBtn = document.querySelector('[onclick="openPackingModal()"]');
        if (addPackingBtn) addPackingBtn.style.display = 'none';
    }
}

// Hide budget fields
function hideBudgetFields() {
    document.querySelectorAll('.budget-field').forEach(el => {
        el.style.display = 'none';
    });
    
    document.querySelectorAll('.activity-cost, .cost-display, [data-field="cost"], .accommodation-cost, .route-cost').forEach(el => {
        el.style.display = 'none';
    });
    
    const budgetTab = document.querySelector('#budget-tab');
    if (budgetTab) {
        budgetTab.closest('li').style.display = 'none';
    }
    
    const budgetTabContent = document.querySelector('#budget');
    if (budgetTabContent) {
        budgetTabContent.style.display = 'none';
    }
}

// Setup tab event listeners
function setupTabListeners() {
    // These will be implemented in separate module files
    // Just set up the basic listeners here
    
    const overviewTab = document.getElementById('overview-tab');
    const activitiesTab = document.getElementById('activities-tab');
    const accommodationsTab = document.getElementById('accommodations-tab');
    const timelineTab = document.getElementById('timeline-tab');
    const calendarTab = document.getElementById('calendar-tab');
    const budgetTab = document.getElementById('budget-tab');
    const packingTab = document.getElementById('packing-tab');
    
    if (overviewTab) {
        overviewTab.addEventListener('shown.bs.tab', function() {
            console.log('Overview tab shown');
            // Map initialization handled in init.js
        });
    }
    
    if (activitiesTab) {
        activitiesTab.addEventListener('shown.bs.tab', function() {
            if (typeof loadActivities === 'function') loadActivities();
        });
    }
    
    if (accommodationsTab) {
        accommodationsTab.addEventListener('shown.bs.tab', function() {
            if (typeof loadAccommodations === 'function') loadAccommodations();
        });
    }
    
    if (timelineTab) {
        timelineTab.addEventListener('shown.bs.tab', function() {
            if (typeof loadGanttChart === 'function') loadGanttChart();
        });
    }
    
    if (budgetTab) {
        budgetTab.addEventListener('shown.bs.tab', function() {
            if (typeof loadBudget === 'function') loadBudget();
        });
    }
    
    if (packingTab) {
        packingTab.addEventListener('shown.bs.tab', function() {
            if (typeof loadPackingList === 'function') loadPackingList();
        });
    }
}

// Placeholder functions - These will be implemented in activity/accommodation modules
// but we need them defined here for the template onclick handlers
function openActivityModal() {
    console.log('openActivityModal called');
    if (typeof addActivity === 'function') addActivity();
}

function openAccommodationModal() {
    console.log('openAccommodationModal called');
    if (typeof addAccommodation === 'function') addAccommodation();
}

function openExpenseModal() {
    console.log('openExpenseModal called');
    if (typeof addExpense === 'function') addExpense();
}

function openPackingModal() {
    console.log('openPackingModal called');
    if (typeof addPackingItem === 'function') addPackingItem();
}

function editTrip() {
    console.log('editTrip called');
    alert('Edit trip functionality to be implemented');
}

function deleteTrip() {
    if (confirm('Are you sure you want to delete this trip?')) {
        console.log('deleteTrip called');
        alert('Delete trip functionality to be implemented');
    }
}

// Export to window for global access
window.hasPermission = hasPermission;
window.isOwner = isOwner;
window.userPermissions = userPermissions;
window.openActivityModal = openActivityModal;
window.openAccommodationModal = openAccommodationModal;
window.openExpenseModal = openExpenseModal;
window.openPackingModal = openPackingModal;
window.editTrip = editTrip;
window.deleteTrip = deleteTrip;
