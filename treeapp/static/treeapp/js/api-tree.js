document.addEventListener("DOMContentLoaded", function() {
  // Skip if tree data is already loaded
  if (window.USER_TREE_DATA) {
    console.log("Tree data already loaded from template");
    return;
  }
  
  const treeContainer = document.getElementById("tree-container");
  if (!treeContainer) return;
  
  console.log("Loading tree data via API...");
  
  // Function to fetch tree data from API
  function fetchTreeData() {
    return fetch('/api/tree/')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .catch(error => {
        console.error("Error fetching tree data:", error);
        throw error;
      });
  }
  
  // Initialize tree with fetched data
  fetchTreeData()
    .then(data => {
      console.log("Tree data loaded successfully");
      window.USER_TREE_DATA = data;
      
      // Use the correct function from fixed-tree.js
      if (typeof window.loadTreeData === 'function') {
        window.loadTreeData();
      } else {
        // If loadTreeData isn't available yet, wait for fixed-tree.js to load
        window.addEventListener('load', function() {
          if (typeof window.loadTreeData === 'function') {
            window.loadTreeData();
          }
        });
      }
    })
    .catch(error => {
      console.error("Failed to load tree data:", error);
    });
});