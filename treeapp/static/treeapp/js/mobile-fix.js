// Mobile compatibility fixes
document.addEventListener('DOMContentLoaded', function() {
  // Fix for edit member button on mobile
  function addMobileEditButtonFix() {
    // Add click handlers to all edit member buttons
    document.addEventListener('click', function(event) {
      // Check if the clicked element is an edit button or inside one
      const editButton = event.target.closest('.edit-member-btn');
      if (editButton) {
        // Get the member ID from the button ID
        const memberId = editButton.id.replace('edit-member-btn-', '');
        // Navigate to the edit page
        if (window.EDIT_MEMBER_URL) {
          window.location.href = window.EDIT_MEMBER_URL.replace('{id}', memberId);
        }
        // Prevent default behavior
        event.preventDefault();
        event.stopPropagation();
      }
    }, true);
  }

  // Apply fixes
  addMobileEditButtonFix();
});