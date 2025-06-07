// Direct override for tree behavior
document.addEventListener('DOMContentLoaded', function() {
    // Apply fixes immediately and again after a delay to ensure they take effect
    applyFixes();
    setTimeout(applyFixes, 1000);
    setTimeout(applyFixes, 2000);
});

function applyFixes() {
    console.log("Applying tree interaction fixes");
    
    // Override the info button click handler
    const infoButtons = document.querySelectorAll('.info-btn');
    infoButtons.forEach(function(btn) {
        // Remove existing event listeners
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // Add new click handler with high z-index and proper pointer events
        newBtn.style.pointerEvents = 'auto';
        newBtn.style.cursor = 'pointer';
        newBtn.style.zIndex = '1000';
        newBtn.addEventListener('click', function(event) {
            event.stopPropagation();
            if (typeof showTab === 'function') {
                showTab('posts');
            }
        });
    });
    
    // Find all edit member buttons in the tree
    const editButtons = document.querySelectorAll('[id^="edit-member-btn-"]');
    editButtons.forEach(function(btn) {
        // Remove existing event listeners
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // Add direct click handler
        newBtn.style.pointerEvents = 'auto';
        newBtn.style.cursor = 'pointer';
        newBtn.style.zIndex = '1000';
        newBtn.style.position = 'relative';
        
        // Make edit button more prominent
        newBtn.style.background = '#4caf50';
        newBtn.style.color = 'white';
        newBtn.style.padding = '8px 15px';
        newBtn.style.borderRadius = '6px';
        newBtn.style.fontWeight = 'bold';
        newBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
    });
    
    // Override modal close button to prevent it from blocking other interactions
    const closeButtons = document.querySelectorAll('#close-info-modal');
    closeButtons.forEach(function(btn) {
        btn.style.display = 'none';
    });
    
    // Make sure modals don't block interactions
    const modals = document.querySelectorAll('.modal-overlay');
    modals.forEach(function(modal) {
        modal.style.pointerEvents = 'none';
    });
    
    // Make sure the tree SVG doesn't block button clicks
    const treeSvg = document.querySelector('#tree-svg');
    if (treeSvg) {
        treeSvg.style.pointerEvents = 'none';
    }
}