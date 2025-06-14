document.addEventListener("DOMContentLoaded", function () {
  console.log("my-tree.js loaded");
  
  if (!window.USER_TREE_DATA) {
    console.error("Tree data not found");
    return;
  }

  // Make sure d3 is loaded
  if (typeof d3 === 'undefined') {
    console.error("D3.js library not loaded");
    const d3Script = document.createElement("script");
    d3Script.src = "https://d3js.org/d3.v7.min.js";
    d3Script.onload = loadTreeScript;
    document.body.appendChild(d3Script);
    return;
  }
  
  loadTreeScript();
  
  function loadTreeScript() {
    // Set a global flag to indicate we're in my-tree mode
    window.IS_MY_TREE = true;
    
    // Load the fixed-tree.js script
    const script = document.createElement("script");
    script.src = "/static/treeapp/js/fixed-tree.js";
    script.onerror = function() {
      console.error("Failed to load tree script");
    };
    document.body.appendChild(script);
  }
});