// Touch event handler for mobile devices
document.addEventListener('DOMContentLoaded', function() {
  // Add touchstart event listener to the document
  document.addEventListener('touchstart', function(event) {
    // Find if the touch is on an edit button or its children
    let target = event.target;
    while (target != null) {
      if (target.classList && target.classList.contains('edit-member-btn')) {
        console.log('Touch detected on edit button:', target.id);
        // Get member ID from button ID
        const memberId = target.id.replace('edit-member-btn-', '');
        // Navigate to edit page
        if (window.EDIT_MEMBER_URL) {
          event.preventDefault();
          console.log('Navigating to:', window.EDIT_MEMBER_URL.replace('{id}', memberId));
          window.location.href = window.EDIT_MEMBER_URL.replace('{id}', memberId);
        }
        break;
      }
      target = target.parentElement;
    }
  }, true);
});