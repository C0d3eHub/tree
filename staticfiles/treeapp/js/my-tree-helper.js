// Helper function to highlight the user's node
function highlightUserNode(nodeId) {
  if (!nodeId) return;
  
  // Find the node in the tree
  const findNodeById = (nodes) => {
    if (!nodes || !nodes.length) return null;
    
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      if (node.data && node.data.id === nodeId) return node;
      
      if (node.children) {
        const found = findNodeById(node.children);
        if (found) return found;
      }
    }
    
    return null;
  };
  
  // If d3root is available, find and highlight the node
  if (window.d3root) {
    const node = findNodeById([window.d3root]);
    if (node) {
      // Select the node and trigger highlighting
      window.selectedNode = node;
      highlightSpineAndSubtree(node);
    }
  }
}

// Expose the function globally
window.highlightUserNode = highlightUserNode;