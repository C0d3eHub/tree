// Mobile compatibility fixes
document.addEventListener('DOMContentLoaded', function() {
  // Add mobile-specific styles
  function addMobileStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .edit-member-btn {
        display: inline-block !important;
        width: auto !important;
        min-width: 120px !important;
        min-height: 40px !important;
        -webkit-appearance: none !important;
        appearance: none !important;
        cursor: pointer !important;
        touch-action: manipulation !important;
        -webkit-tap-highlight-color: transparent !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        position: relative !important;
        z-index: 100 !important;
        text-decoration: none !important;
        text-align: center !important;
        line-height: 40px !important;
        border: none !important;
        outline: none !important;
        background: #4caf50 !important;
        color: white !important;
        font-weight: bold !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
        transition: all 0.2s ease !important;
      }

      .edit-member-btn:active {
        transform: scale(0.98) !important;
        background: #43a047 !important;
      }

      @media (max-width: 768px) {
        .edit-member-btn {
          padding: 12px 24px !important;
          font-size: 16px !important;
          margin: 10px 0 !important;
          width: 100% !important;
          max-width: 200px !important;
          border-radius: 8px !important;
        }
      }
    `;
    document.head.appendChild(style);

    // Add touch event logging and handling
    document.addEventListener('touchstart', function(event) {
      const editButton = event.target.closest('.edit-member-btn');
      if (editButton) {
        console.log('Touch detected on edit button');
        print('edit clicked');
        print('edit member touch detected');
        
        // Get the onclick handler content
        const onclickAttr = editButton.getAttribute('onclick');
        console.log('Button onclick:', onclickAttr);
        
        if (onclickAttr && onclickAttr.includes('window.location.href')) {
          // Extract the URL from the onclick handler
          const urlMatch = onclickAttr.match(/window\.location\.href='([^']+)'/);
          if (urlMatch && urlMatch[1]) {
            const url = urlMatch[1];
            console.log('Extracted URL:', url);
            
            if (url.includes('/edit-member/')) {
              const memberId = url.split('/edit-member/')[1].split('/')[0];
              console.log('Member ID:', memberId);
              
              if (memberId && memberId !== '') {
                print('Navigating to edit page for member:', memberId);
                // Use setTimeout to ensure the event is processed
                setTimeout(() => {
                  window.location.href = url;
                }, 100);
              }
            }
          }
        }
        
        // Prevent default to handle navigation ourselves
        event.preventDefault();
        event.stopPropagation();
      }
    }, { capture: true, passive: false });
  }

  // Apply fixes
  addMobileStyles();
});