// Direct link for edit member buttons
document.addEventListener('DOMContentLoaded', function() {
  // Create direct links for all edit member buttons
  function createDirectLinks() {
    // Find all info modals that might contain edit buttons
    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length) {
          // Check if any added nodes contain edit member buttons
          mutation.addedNodes.forEach(function(node) {
            if (node.nodeType === 1 && node.querySelector) {
              const editButtons = node.querySelectorAll('.edit-member-btn');
              editButtons.forEach(function(btn) {
                console.log('Found edit button:', btn.id);
                const memberId = btn.getAttribute('data-id');
                if (memberId && window.EDIT_MEMBER_URL) {
                  const url = window.EDIT_MEMBER_URL.replace('{id}', memberId);
                  // Create a direct link that will be shown on mobile
                  const directLink = document.createElement('a');
                  directLink.href = url;
                  directLink.className = 'direct-edit-link';
                  directLink.innerHTML = 'Edit Member';
                  directLink.style.cssText = `
                    display: block;
                    margin-top: 15px;
                    background: #4caf50;
                    color: white;
                    text-align: center;
                    padding: 12px;
                    border-radius: 8px;
                    font-weight: bold;
                    text-decoration: none;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                  `;
                  // Insert after the info content
                  const infoContent = btn.closest('.modal-overlay');
                  if (infoContent) {
                    const actionRow = infoContent.querySelector('.modal-action-row');
                    if (actionRow) {
                      actionRow.parentNode.insertBefore(directLink, actionRow);
                    }
                  }
                }
              });
            }
          });
        }
      });
    });
    
    // Start observing the document body for added nodes
    observer.observe(document.body, { childList: true, subtree: true });
  }
  
  createDirectLinks();
});