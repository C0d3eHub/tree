console.log('fixed-tree.js loaded');
document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("tree-container");
  if (!container) return;

  const svg = d3
    .select("#tree-svg")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr(
      "viewBox",
      `0 0 ${container.clientWidth * 2} ${container.clientHeight * 2}`
    )
    .attr("preserveAspectRatio", "xMidYMid meet");

  svg.select("defs").remove();
  const defs = svg.append("defs");
  defs
    .append("marker")
    .attr("id", "arrowhead")
    .attr("viewBox", "0 -6 12 12")
    .attr("refX", 7)
    .attr("refY", 0)
    .attr("markerWidth", 12)
    .attr("markerHeight", 12)
    .attr("orient", "auto")
    .attr("markerUnits", "userSpaceOnUse")
    .append("path")
    .attr("d", "M0,-6L12,0L0,6Z")
    .attr("fill", "#cc3366");
  defs
    .append("filter")
    .attr("id", "button-shadow")
    .html(
      `<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#bbb" flood-opacity="0.6"/>`
    );

  let g = svg.append("g").attr("class", "tree-group");

  const MIN_NODE_WIDTH = 60,
    MIN_NODE_HEIGHT = 36;
  const NODE_HORIZ_PADDING = 18,
    NODE_VERT_PADDING = 14;
  const NODE_MARGIN_X = 10,
    NODE_MARGIN_Y = 36;

  let treeLayout, rootData, d3root;
  let selectedNode = null;
  let highlightMode = false;
  let compareMode = false,
    firstNode = null,
    comparisonTimeout = null;

  let currentZoomTransform = d3.zoomIdentity;

  const compareBtn = document.getElementById("comparenode-btn");
  const correctionBtn = document.getElementById("correctionname-btn");
  const modalRoot = document.getElementById("dynamic-modal-root");

  // Replace the existing zoom implementation with this:

  const zoom = d3
    .zoom()
    .scaleExtent([0.05, 25]) // Allow zooming out further
    .translateExtent([
      [-20000, -20000],
      [20000, 20000],
    ]) // Expand the pan area
    .on("zoom", (event) => {
      currentZoomTransform = event.transform;
      g.attr("transform", event.transform);
    });

  // Enable zoom behavior
  svg.call(zoom);

  // Prevent default touch behaviors that might interfere
  svg.on("touchstart", function (event) {
    // Only prevent default for multi-touch (pinch) gestures
    if (event.touches.length >= 2) {
      event.preventDefault();
    }
  });
  svg.on("touchmove", function (event) {
    // Check if tree is still visible after the move
    const bounds = g.node().getBBox();
    const transformed = currentZoomTransform.apply([
      bounds.x + bounds.width / 2,
      bounds.y + bounds.height / 2,
    ]);

    const svgWidth = container.clientWidth;
    const svgHeight = container.clientHeight;

    // If center point is outside viewport, recenter
    if (
      transformed[0] < 0 ||
      transformed[0] > svgWidth ||
      transformed[1] < 0 ||
      transformed[1] > svgHeight
    ) {
      // Calculate new transform to center the tree
      const centerX = bounds.x + bounds.width / 2;
      const centerY = bounds.y + bounds.height / 2;
      const scale = currentZoomTransform.k;

      svg
        .transition()
        .duration(300)
        .call(
          zoom.transform,
          d3.zoomIdentity
            .translate(
              svgWidth / 2 - centerX * scale,
              svgHeight / 2 - centerY * scale
            )
            .scale(scale)
        );
    }
  });

  // Also add this meta tag to your HTML head if not already present
  // <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, minimum-scale=0.5, user-scalable=yes">

  function getColorByDepth(depth) {
    const colors = [
      "#1abc9c",
      "#3498db",
      "#e67e22",
      "#9b59b6",
      "#e74c3c",
      "#f1c40f",
    ];
    return colors[depth % colors.length];
  }
  function getDarkerColor(hex) {
    return d3.color(hex).darker(1.5).toString();
  }
  function resetZoom() {
    console.log('Resetting zoom');
    const bounds = g.node().getBBox();
    const svgWidth = container.clientWidth;
    const svgHeight = container.clientHeight;

    if (bounds.width === 0 || bounds.height === 0) return;

    const padding = 40;
    const width = bounds.width + padding * 2;
    const height = bounds.height + padding * 2;

    let scale = Math.min(svgWidth / width, svgHeight / height);
    scale = Math.max(scale, 0.1); // Prevent zooming out too far

    const translateX = svgWidth / 2 - (bounds.x + bounds.width / 2) * scale;
    const translateY = svgHeight / 2 - (bounds.y + bounds.height / 2) * scale;

    svg
      .transition()
      .duration(600)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(translateX, translateY).scale(scale)
      );

    currentZoomTransform = d3.zoomIdentity
      .translate(translateX, translateY)
      .scale(scale);
  }

  function constrainZoom(transform) {
    // Get the current bounds of the tree
    const bounds = g.node().getBBox();
    const svgWidth = container.clientWidth;
    const svgHeight = container.clientHeight;

    // When zooming out too far, force the tree to stay centered
    if (transform.k < 0.3) {
      const centerX = bounds.x + bounds.width / 2;
      const centerY = bounds.y + bounds.height / 2;
      transform.x = svgWidth / 2 - centerX * transform.k;
      transform.y = svgHeight / 2 - centerY * transform.k;
    }

    return transform;
  }

  function focusOnNodes(nodes) {
    if (!nodes.length) return;
    const minX = d3.min(nodes, (d) => d.x),
      maxX = d3.max(nodes, (d) => d.x);
    const minY = d3.min(nodes, (d) => d.y),
      maxY = d3.max(nodes, (d) => d.y);
    const padding = 80;
    const width = maxX - minX + padding * 2;
    const height = maxY - minY + padding * 2;
    const svgWidth = container.clientWidth,
      svgHeight = container.clientHeight;
    const scale = Math.min(svgWidth / width, svgHeight / height) * 0.85;
    const translateX = svgWidth / 2 - ((minX + maxX) / 2) * scale;
    const translateY = svgHeight / 2 - ((minY + maxY) / 2) * scale;
    svg
      .transition()
      .duration(600)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(translateX, translateY).scale(scale)
      );
    currentZoomTransform = d3.zoomIdentity
      .translate(translateX, translateY)
      .scale(scale);
  }

  function updateActionButtons() {
    // Skip if we're in my_tree view
    if (window.IS_MY_TREE) return;
    
    // Only proceed if the buttons exist
    if (!compareBtn || !correctionBtn) return;
    
    if (selectedNode && !compareMode) {
      compareBtn.style.display = "inline-block";
      correctionBtn.style.display = "inline-block";
    } else {
      compareBtn.style.display = "none";
      correctionBtn.style.display = "none";
    }
  }

  // Collapse/expand logic
  function collapse(d) {
    console.log('Collapsing node:', d.data.name);
    if (d.children) {
      d._children = d.children;
      d._children.forEach(collapse);
      d.children = null;
    }
  }
  function expand(d) {
    console.log('Expanding node:', d.data.name);
    if (d._children) {
      d.children = d._children;
      d.children.forEach(expand);
      d._children = null;
    }
  }

  function renderTree(data, focusIdOrName, preserveZoom = false) {
    d3root = d3.hierarchy(data, (d) => d.children || d._children);

    // Measure text
    const tempSvg = d3
      .select("body")
      .append("svg")
      .style("visibility", "hidden");
    (function recMeasure(node) {
      const textElem = tempSvg
        .append("text")
        .attr("font-family", "sans-serif")
        .attr("font-size", 16)
        .text(node.data.name);
      const bbox = textElem.node().getBBox();
      node.data._textWidth = bbox.width;
      node.data._textHeight = bbox.height;
      textElem.remove();
      if (node.children) node.children.forEach(recMeasure);
      if (node._children) node._children.forEach(recMeasure);
    })(d3root);
    tempSvg.remove();

    let maxNodeWidth = Math.max(
      ...d3root
        .descendants()
        .map((d) =>
          Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH)
        )
    );
    let maxNodeHeight = Math.max(
      ...d3root
        .descendants()
        .map((d) =>
          Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT)
        )
    );
    treeLayout = d3
      .tree()
      .nodeSize([maxNodeWidth + NODE_MARGIN_X, maxNodeHeight + NODE_MARGIN_Y]);
    treeLayout(d3root);
    drawNodesAndLinks(d3root);

    if (preserveZoom) {
      svg.transition().duration(0).call(zoom.transform, currentZoomTransform);
    } else {
      setTimeout(() => {
        const bounds = g.node().getBBox();
        const svgWidth = container.clientWidth;
        const svgHeight = container.clientHeight;

        if (bounds.width === 0 || bounds.height === 0) return;

        const padding = 40;
        const width = bounds.width + padding * 2;
        const height = bounds.height + padding * 2;

        let scale = Math.min(svgWidth / width, svgHeight / height);
        scale = Math.max(scale, 0.1); // Prevent invisibly small tree

        // Center the tree horizontally and vertically
        const translateX = svgWidth / 2 - (bounds.x + bounds.width / 2) * scale;
        const translateY = svgHeight / 2 - (bounds.y + bounds.height / 2) * scale;

        svg
          .transition()
          .duration(500)
          .call(
            zoom.transform,
            d3.zoomIdentity.translate(translateX, translateY).scale(scale)
          );

        currentZoomTransform = d3.zoomIdentity
          .translate(translateX, translateY)
          .scale(scale);
      }, 0);
    }
    updateActionButtons();

    // If we have a selected node to re-highlight after reload, do it.
    if (selectedNode) {
      let match = null;
      if (selectedNode.data.id) {
        match = d3root
          .descendants()
          .find((n) => n.data.id && n.data.id === selectedNode.data.id);
      }
      if (!match && selectedNode.data.name) {
        match = d3root
          .descendants()
          .find((n) => n.data.name === selectedNode.data.name);
      }

      if (match) {
        selectedNode = match;
        highlightSpineAndSubtree(selectedNode);
      }
    } else if (window.IS_MY_TREE && window.userNodeId) {
      // For my_tree view, highlight the user's node if found
      const userNode = d3root
        .descendants()
        .find((n) => n.data.id && n.data.id === window.userNodeId);
      
      if (userNode) {
        selectedNode = userNode;
        highlightSpineAndSubtree(selectedNode);
        
        // Clear the userNodeId to avoid re-selecting on subsequent renders
        window.userNodeId = null;
      }
    }
  }

  function drawNodesAndLinks(root, spine = [], subtree = []) {
    g.selectAll("*").remove();

    const visibleNodes = [];
    function collectVisible(node) {
      visibleNodes.push(node);
      if (node.children) node.children.forEach(collectVisible);
    }
    collectVisible(root);

    const visibleLinks = [];
    visibleNodes.forEach((node) => {
      if (node.children) {
        node.children.forEach((child) => {
          visibleLinks.push({ source: node, target: child });
        });
      }
    });

    g.selectAll(".link")
      .data(visibleLinks)
      .enter()
      .append("path")
      .attr("class", "link")
      .attr("fill", "none")
      .attr("stroke", (d) => {
        if (spine.includes(d.source) && spine.includes(d.target)) return "lime";
        if (subtree.includes(d.source) && subtree.includes(d.target))
          return "#ff0";
        return getDarkerColor(getColorByDepth(d.source.depth));
      })
      .attr("stroke-width", (d) => {
        if (spine.includes(d.source) && spine.includes(d.target)) return 3;
        if (subtree.includes(d.source) && subtree.includes(d.target)) return 2;
        return 2;
      })
      .attr("opacity", (d) =>
        spine.length > 0
          ? (spine.includes(d.source) && spine.includes(d.target)) ||
            (subtree.includes(d.source) && subtree.includes(d.target))
            ? 1
            : 0.08
          : 1
      )
      .attr("marker-end", "url(#arrowhead)")
      .attr("d", function (d) {
        const sourceWidth = Math.max(
          d.source.data._textWidth + NODE_HORIZ_PADDING,
          MIN_NODE_WIDTH
        );
        const sourceHeight = Math.max(
          d.source.data._textHeight + NODE_VERT_PADDING,
          MIN_NODE_HEIGHT
        );
        const targetWidth = Math.max(
          d.target.data._textWidth + NODE_HORIZ_PADDING,
          MIN_NODE_WIDTH
        );
        const targetHeight = Math.max(
          d.target.data._textHeight + NODE_VERT_PADDING,
          MIN_NODE_HEIGHT
        );
        const startX = d.source.x;
        const startY = d.source.y + sourceHeight / 2 - 3;
        const endX = d.target.x;
        const endY = d.target.y - targetHeight / 2 - 3;
        const elbowY = (startY + endY) / 2;
        return `M${startX},${startY} V${elbowY} H${endX} V${endY}`;
      });

    // Draw nodes
    const nodes = g
      .selectAll(".node")
      .data(visibleNodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`)
      .style("cursor", "pointer");

    // Draw node rectangles
    nodes
      .insert("rect", "text")
      .attr(
        "x",
        (d) =>
          -Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH) / 2
      )
      .attr(
        "y",
        (d) =>
          -Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT) / 2
      )
      .attr("width", (d) =>
        Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH)
      )
      .attr("height", (d) =>
        Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT)
      )
      .attr("rx", 10)
      .attr("fill", (d) => getColorByDepth(d.depth))
      .attr("stroke", (d) => {
        if (spine.includes(d)) return "lime";
        if (subtree.includes(d)) return "#ff0";
        return null;
      })
      .attr("stroke-width", (d) => {
        if (spine.includes(d)) return 3;
        if (subtree.includes(d)) return 2;
        return null;
      });

    // Draw node text
    nodes
      .append("text")
      .attr("dy", 5)
      .attr("text-anchor", "middle")
      .attr("fill", "#fff")
      .attr("font-family", "sans-serif")
      .attr("font-size", 16)
      .text((d) => d.data.name);

    // Node click event (after +/- button to avoid highlight on collapse/expand)
    nodes.on("click", function (event, d) {
      if (event.target.closest(".collapse-toggle")) {
        event.stopPropagation();
        return;
      }
      if (compareMode) return;
      // Show info modal
      if (!modalRoot) return;
      const picUrl = d.data.picture || "/static/treeapp/images/123.jpg";
      // Only show मृत्यु वर्ष if it exists (not null, undefined, or empty string)
      const showDeathYear =
        d.data.year_of_death !== null &&
        d.data.year_of_death !== undefined &&
        d.data.year_of_death !== "";
      const html = `
        <div class="modal-overlay" id="info-modal" style="user-select: none; pointer-events: all;">
          <div class="modal-title" style="margin-bottom:12px; font-size:1.25rem; color:#2c3e50;">
            <span style="background:linear-gradient(90deg,#9be7ff,#d1c4e9);padding:4px 18px;border-radius:8px;">
              ${d.data.name || "-"} जी के बारे में जानकारी
            </span>
            ${window.EDIT_MEMBER_URL && d.data && d.data.id ? 
              `<button 
                  onclick="window.location.href='/edit-member/${d.data.id}/'"
                  class="edit-member-btn"
                  style="display:inline-block; margin-left:10px; background:#4caf50; color:white; 
                         border-radius:6px; padding:8px 15px; text-align:center; 
                         text-decoration:none; font-weight:bold; box-shadow:0 2px 5px rgba(0,0,0,0.2);
                         font-size:15px; transition: all 0.2s ease; cursor:pointer; z-index:2000;
                         -webkit-tap-highlight-color: transparent; touch-action: manipulation;
                         position: relative; min-width: 120px; min-height: 40px; border:none;">
                         <span style="font-size:18px; margin-right:6px; vertical-align:middle; 
                         background:#fff; color:#4caf50; border-radius:50%; width:22px; height:22px; 
                         display:inline-block; line-height:22px; text-align:center;">✏️</span>Edit Member</button>` 
              : ''}
          </div>
          <div class="modal-content" style="background:white; padding:20px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
            <div style="display:flex; gap:20px; align-items:start;">
              <img src="${picUrl}" alt="${d.data.name}" style="width:120px; height:120px; object-fit:cover; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1);">
              <div style="flex:1;">
                <p style="margin:0 0 8px; font-size:1.1rem;"><strong>नाम:</strong> ${d.data.name || "-"}</p>
                <p style="margin:0 0 8px; font-size:1.1rem;"><strong>पिता का नाम:</strong> ${d.data.father_name || "-"}</p>
                <p style="margin:0 0 8px; font-size:1.1rem;"><strong>जन्म वर्ष:</strong> ${d.data.date_of_birth ? (function(dateStr){ var d=new Date(dateStr); return (('0'+d.getDate()).slice(-2)+'/'+('0'+(d.getMonth()+1)).slice(-2)+'/'+d.getFullYear()); })(d.data.date_of_birth) : (d.data.year_of_birth || "-")}</p>
                ${showDeathYear ? `<p style="margin:0 0 8px; font-size:1.1rem;"><strong>मृत्यु वर्ष:</strong> ${d.data.year_of_death}</p>` : ''}
              </div>
            </div>
          </div>
          <div class="modal-action-row" style="margin-top:16px; text-align:right;">
            <button id="close-info-modal" style="
              background:linear-gradient(90deg,#64b5f6,#81d4fa);
              color:#fff;
              font-size:1rem;
              border:none;
              border-radius:6px;
              padding:6px 22px;
              box-shadow:0 1px 5px #b2ebf2;
              font-weight:600;
              cursor:pointer;
            ">OK</button>
          </div>
        </div>`;
      modalRoot.innerHTML = html;
      makeModalDraggable(document.getElementById("info-modal"));
      // Use direct onclick assignment instead of addEventListener
      setTimeout(function() {
        const closeBtn = document.getElementById("close-info-modal");
        if (closeBtn) {
          closeBtn.onclick = function() {
            modalRoot.innerHTML = "";
            return false;
          };
        }
      }, 0);
      event.stopPropagation();
    });

    // Add Info (🌳) Button outside the node at the top left
    nodes
      .append("text")
      .attr(
        "x",
        (d) =>
          -Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH) /
            2 +
          6
      )
      .attr(
        "y",
        (d) =>
          -Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT) /
            2 -
          4
      )
      .attr("font-size", 16)
      .attr("font-family", "sans-serif")
      .attr("fill", "#3498db")
      .attr("cursor", "pointer")
      .style("user-select", "none")
      .text("🌳")
      .attr("tabindex", 0)
      .attr("aria-label", "सूचना देखें")
      .on("click", function (event, d) {
        event.stopPropagation();
        if (compareMode) return;
        resetHighlight();
        let match = null;
        if (d.data.id) {
          match = d3root.descendants().find((n) => n.data.id === d.data.id);
        }
        if (!match && d.data.name) {
          match = d3root.descendants().find((n) => n.data.name === d.data.name);
        }
        if (match) {
          selectedNode = match;
          highlightSpineAndSubtree(match);
          updateActionButtons();
          if (modalRoot) modalRoot.innerHTML = "";
        }
        event.stopPropagation();
      });

    // Add collapse/expand button (➕/➖) outside to the right of the node
    nodes
      .filter((d) => {
        return (
          (d.data.children && d.data.children.length > 0) ||
          (d.data._children && d.data._children.length > 0)
        );
      })
      .append("g")
      .attr("class", "collapse-toggle")
      .each(function (d) {
        const boxWidth = Math.max(
          d.data._textWidth + NODE_HORIZ_PADDING,
          MIN_NODE_WIDTH
        );

        // Position button at the top right of the arrowhead
        const x = boxWidth / 2 - 20; // 3px right of arrowhead
        const y = -27; // Move up by 15px to position at the top

        const group = d3
          .select(this)
          .attr("transform", `translate(${x},${y})`)
          .style("pointer-events", "all");

        const circle = group
          .append("circle")
          .attr("r", 8) // Make even smaller
          .attr("fill", "#fff")
          .attr("stroke", "#666")
          .attr("stroke-width", 1.5)
          .attr("filter", "url(#button-shadow)")
          .attr("cursor", "pointer");

        const sign = group
          .append("text")
          .attr("text-anchor", "middle")
          .attr("dy", 4) // Adjusted for smaller circle
          .attr("font-size", 14) // Smaller font size
          .attr("font-family", "sans-serif")
          .text(() => {
            if (d.data.children && d.data.children.length > 0) return "➖";
            if (d.data._children && d.data._children.length > 0) return "➕";
            return "";
          });

        function collapseExpandHandler(event) {
          event.preventDefault();
          event.stopPropagation();

          // Collapse: only if children are present
          if (d.data.children && d.data.children.length > 0) {
            // Store children in _children
            d.data._children = d.data.children;
            // Clear children
            d.data.children = [];
            console.log("Collapsed node:", d.data.name);

            // Re-render the tree
            renderTree(rootData, d.data.id, true);
            return;
          }

          // Expand: only if _children are present
          if (d.data._children && d.data._children.length > 0) {
            // Restore children from _children
            d.data.children = d.data._children;
            // Clear _children
            d.data._children = [];

            // Recursively expand all children
            function expandAllChildren(node) {
              if (node._children && node._children.length > 0) {
                node.children = node._children;
                node._children = [];
                node.children.forEach(expandAllChildren);
              }
            }
            
            // Expand all children of the current node
            d.data.children.forEach(expandAllChildren);
            
            console.log("Expanded node:", d.data.name);

            // Re-render the tree
            renderTree(rootData, d.data.id, true);
            return;
          }
        }

        group.on("click touchstart", collapseExpandHandler);
        circle.on("click touchstart", collapseExpandHandler);
        sign.on("click touchstart", collapseExpandHandler);
      });

    // Add Share to WhatsApp button only for My Tree view
    if (window.IS_MY_TREE) {
      const shareButton = d3.select("#tree-container")
        .append("button")
        .attr("id", "share-whatsapp-btn")
        .style("position", "absolute")
        .style("top", "10px")
        .style("right", "10px")
        .style("background", "rgb(37, 211, 102)")
        .style("color", "white")
        .style("border", "none")
        .style("border-radius", "6px")
        .style("padding", "8px 16px")
        .style("font-size", "14px")
        .style("cursor", "pointer")
        .style("display", "flex")
        .style("align-items", "center")
        .style("gap", "8px")
        .style("box-shadow", "rgba(0, 0, 0, 0.2) 0px 2px 4px")
        .style("z-index", "1000")
        .html('<span style="font-size: 18px;">📱</span><span class="share-text">Share Tree</span>');

      // Add media query for small screens
      const mediaQuery = window.matchMedia('(max-width: 768px)');
      function handleScreenChange(e) {
        if (e.matches) {
          // Small screen - show only emoji
          shareButton.style("padding", "8px")
            .select(".share-text")
            .style("display", "none");
        } else {
          // Large screen - show full text
          shareButton.style("padding", "8px 16px")
            .select(".share-text")
            .style("display", "inline");
        }
      }
      mediaQuery.addListener(handleScreenChange);
      handleScreenChange(mediaQuery);

      // Function to hide share button
      function hideShareButton() {
        shareButton.style('display', 'none');
      }

      // Function to show share button
      function showShareButton() {
        shareButton.style('display', 'flex');
      }

      // Hide share button when info modal opens
      document.addEventListener('click', function(event) {
        // Check if clicking info button or node
        if (event.target.classList.contains('info-btn') || 
            event.target.closest('.info-btn') ||
            event.target.classList.contains('node') ||
            event.target.closest('.node')) {
          hideShareButton();
        }
      });

      // Show share button when info modal closes
      document.addEventListener('click', function(event) {
        if (event.target.id === 'close-info-modal' || 
            event.target.closest('#close-info-modal') ||
            event.target.classList.contains('modal-overlay')) {
          showShareButton();
        }
      });

      // Also hide share button when modal is shown through other means
      const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
          if (mutation.addedNodes.length) {
            mutation.addedNodes.forEach(function(node) {
              if (node.classList && node.classList.contains('modal-overlay')) {
                hideShareButton();
              }
            });
          }
        });
      });

      // Start observing the document body for modal additions
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      let isDownloading = false;

      const downloadTreeImage = async () => {
        if (isDownloading) return;
        isDownloading = true;

        try {
          // Get the SVG element
          const svg = document.querySelector("#tree-svg");
          if (!svg) return;

          // Create a clone of the SVG
          const clonedSvg = svg.cloneNode(true);
          
          // Set background color and dimensions
          clonedSvg.style.backgroundColor = "white";
          const bbox = svg.getBBox();
          const width = bbox.width + 40; // Add padding
          const height = bbox.height + 40; // Add padding
          
          // Set viewBox and dimensions
          clonedSvg.setAttribute("viewBox", `${bbox.x - 20} ${bbox.y - 20} ${width} ${height}`);
          clonedSvg.setAttribute("width", width);
          clonedSvg.setAttribute("height", height);
          
          // Convert SVG to string
          const svgData = new XMLSerializer().serializeToString(clonedSvg);
          
          // Create canvas
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          
          // Set canvas size
          canvas.width = width;
          canvas.height = height;
          
          // Create image from SVG
          const img = new Image();
          img.onload = function() {
            // Draw white background
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw the image
            ctx.drawImage(img, 0, 0);
            
            // Convert to blob
            canvas.toBlob(function(blob) {
              // Create a download link
              const url = URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.download = 'family-tree.png';
              
              // Trigger download
              link.click();
              
              // Clean up
              setTimeout(() => {
                URL.revokeObjectURL(url);
                isDownloading = false;
              }, 100);
            }, 'image/png', 1.0);
          };
          
          // Set image source to SVG data URL
          img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
        } catch (error) {
          console.error('Error sharing tree:', error);
          alert('Error sharing tree. Please try again.');
          isDownloading = false;
        }
      };

      shareButton.on("click", function() {
        // Show instructions modal
        if (modalRoot) {
          modalRoot.innerHTML = `
            <div class="modal-overlay" style="user-select: none; pointer-events: all;">
              <div class="modal-content" style="background:white; padding:20px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin-top:0; color:#2c3e50;">Share Your Family Tree</h3>
                <p style="margin-bottom:20px;">To share your family tree:</p>
                <ol style="margin-left:20px; margin-bottom:20px;">
                  <li>Click the "Download Image" button below</li>
                  <li>Open WhatsApp</li>
                  <li>Select the contact or group</li>
                  <li>Share the downloaded image</li>
                </ol>
                <div style="display:flex; gap:10px; justify-content:flex-end;">
                  <button id="download-tree-btn" style="
                    background:#25D366;
                    color:white;
                    border:none;
                    border-radius:6px;
                    padding:8px 16px;
                    cursor:pointer;
                  ">Download Image</button>
                  <button id="close-share-modal" style="
                    background:#e0e0e0;
                    color:#333;
                    border:none;
                    border-radius:6px;
                    padding:8px 16px;
                    cursor:pointer;
                  ">Cancel</button>
                </div>
              </div>
            </div>
          `;

          // Add event listeners to modal buttons
          document.getElementById('download-tree-btn').addEventListener('click', function() {
            downloadTreeImage();
            modalRoot.innerHTML = '';
          });

          document.getElementById('close-share-modal').addEventListener('click', function() {
            modalRoot.innerHTML = '';
          });
        }
      });
    }
  }

  function highlightSpineAndSubtree(selectedNode) {
    highlightMode = true;
    let spine = [];
    let curr = selectedNode;
    while (curr) {
      spine.push(curr);
      curr = curr.parent;
    }
    spine = spine.reverse();

    const x0 = spine[0].x;
    let yStart = spine[0].y;
    for (let i = 0; i < spine.length; ++i) {
      spine[i].x = x0;
      spine[i].y = yStart + i * (MIN_NODE_HEIGHT + NODE_MARGIN_Y);
    }

    let subtree = [];
    selectedNode.each((n) => subtree.push(n));
    let subtreeRoot = d3.hierarchy(
      selectedNode.data,
      (d) => d.children || d._children
    );
    const tempSvg = d3
      .select("body")
      .append("svg")
      .style("visibility", "hidden");
    (function recMeasure(node) {
      const textElem = tempSvg
        .append("text")
        .attr("font-family", "sans-serif")
        .attr("font-size", 16)
        .text(node.data.name);
      const bbox = textElem.node().getBBox();
      node.data._textWidth = bbox.width;
      node.data._textHeight = bbox.height;
      textElem.remove();
      if (node.children) node.children.forEach(recMeasure);
      if (node._children) node._children.forEach(recMeasure);
    })(subtreeRoot);
    tempSvg.remove();
    const subtreeTree = d3
      .tree()
      .nodeSize([
        MIN_NODE_WIDTH + NODE_MARGIN_X,
        MIN_NODE_HEIGHT + NODE_MARGIN_Y,
      ]);
    subtreeTree(subtreeRoot);
    let yOffset = spine[spine.length - 1].y;
    let xOffset = x0 + MIN_NODE_WIDTH + 80;
    subtreeRoot.each((d, i) => {
      if (i === 0) return;
      let realNode = subtree.find(
        (n) =>
          n.data.name === d.data.name &&
          n.depth === selectedNode.depth + d.depth
      );
      if (realNode) {
        realNode.x = xOffset + d.x;
        realNode.y = yOffset + d.y;
      }
    });

    drawNodesAndLinks(d3root, spine, subtree);

    g.selectAll(".highlight-spine").remove();
    g.append("line")
      .attr("class", "highlight-spine")
      .attr("x1", x0)
      .attr("x2", x0)
      .attr("y1", spine[0].y)
      .attr("y2", spine[spine.length - 1].y)
      .attr("stroke", "lime")
      .attr("stroke-width", 7)
      .attr("opacity", 0.18)
      .lower();

    g.selectAll(".node rect").attr("opacity", (d) =>
      spine.includes(d) || subtree.includes(d) ? 1 : 0.35
    );
    g.selectAll(".link").attr("opacity", (d) =>
      (spine.includes(d.source) && spine.includes(d.target)) ||
      (subtree.includes(d.source) && subtree.includes(d.target))
        ? 1
        : 0.25
    );
    g.selectAll("text").attr("opacity", (d) =>
      spine.includes(d) || subtree.includes(d) ? 1 : 0.38
    );

    focusOnNodes(spine.concat(subtree));
  }

  function resetHighlight() {
    highlightMode = false;
    selectedNode = null;
    renderTree(rootData, null, true);
    g.selectAll(".highlight-spine").remove();
    updateActionButtons();
    if (modalRoot) modalRoot.innerHTML = "";
  }

  document.addEventListener("click", function (event) {
    if (modalRoot && modalRoot.innerHTML.trim() !== "") return;
    if (compareMode) return;
    if (event.target.closest(".node")) return;
    if (event.target.closest(".modal-overlay")) return;
    resetHighlight();
  });

  function showCompareModal(htmlBody, showCancel = false, onlyOk = false) {
    // Add test alert
    console.log('Showing modal:', htmlBody);
    
    modalRoot.innerHTML = `
      <div class="modal-overlay" id="compare-modal" style="user-select: none;">
        ${htmlBody}
        <div class="modal-action-row">
          ${
            showCancel && !onlyOk
              ? `<button class="cancel-btn" id="cancel-compare">Cancel</button>`
              : ""
          }
          ${onlyOk ? `<button id="close-compare-modal">OK</button>` : ""}
        </div>
      </div>
    `;
    makeModalDraggable(document.getElementById("compare-modal"));
    if (showCancel && !onlyOk)
      document.getElementById("cancel-compare").onclick = () => {
        console.log('Cancel button clicked');
        exitCompareMode();
      }
    if (onlyOk)
      document.getElementById("close-compare-modal").onclick = () => {
        console.log('OK button clicked');
        exitCompareMode();
      }
  }
  function makeModalDraggable(modalEl) {
    let isDragging = false,
      dragOffsetX = 0,
      dragOffsetY = 0;
    modalEl.addEventListener("mousedown", function (e) {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      isDragging = true;
      dragOffsetX = e.clientX - modalEl.getBoundingClientRect().left;
      dragOffsetY = e.clientY - modalEl.getBoundingClientRect().top;
      modalEl.style.cursor = "grabbing";
      e.preventDefault();
    });
    document.addEventListener("mousemove", function (e) {
      if (!isDragging) return;
      modalEl.style.left = e.clientX - dragOffsetX + "px";
      modalEl.style.top = e.clientY - dragOffsetY + "px";
      modalEl.style.position = "fixed";
      modalEl.style.transform = "none";
      modalEl.style.zIndex = 3000;
    });
    document.addEventListener("mouseup", function () {
      if (isDragging) {
        isDragging = false;
        modalEl.style.cursor = "grab";
      }
    });
    modalEl.addEventListener(
      "touchstart",
      function (e) {
        if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT")
          return;
        isDragging = true;
        const touch = e.touches[0];
        dragOffsetX = touch.clientX - modalEl.getBoundingClientRect().left;
        dragOffsetY = touch.clientY - modalEl.getBoundingClientRect().top;
        e.preventDefault();
      },
      { passive: false }
    );
    document.addEventListener(
      "touchmove",
      function (e) {
        if (!isDragging) return;
        const touch = e.touches[0];
        modalEl.style.left = touch.clientX - dragOffsetX + "px";
        modalEl.style.top = touch.clientY - dragOffsetY + "px";
      },
      { passive: false }
    );
    document.addEventListener("touchend", function () {
      if (isDragging) isDragging = false;
    });
  }
  function exitCompareMode() {
    compareMode = false;
    firstNode = null;
    modalRoot.innerHTML = "";
    selectedNode = null;
    updateActionButtons();
    if (comparisonTimeout) clearTimeout(comparisonTimeout);
  }
  // Only add event listener if the button exists
  if (compareBtn) {
    compareBtn.addEventListener("click", () => {
      if (!selectedNode) return;
      compareMode = true;
      firstNode = null;
      updateActionButtons();
      showCompareModal(
        `<div class="modal-title">Comparison Mode</div>
          <div class="modal-message">
            <span style="font-weight:bold;color:#0078d7;">Compare generations</span><br>
            Select <b>first node</b> in the tree to begin.<br>
          </div>`,
        true
      );
    });
  }

  document.body.addEventListener(
    "click",
    function (event) {
      if (!compareMode) return;
      let nodeEl = event.target.closest(".node");
      if (!nodeEl) return;
      let data = d3.select(nodeEl).datum();
      if (!firstNode) {
        firstNode = data;
        showCompareModal(
          `<div class="modal-title">Comparison Mode</div>
        <div class="modal-message">First node: <b>${data.data.name}</b><br>Now select <b>second node</b> to compare generations.</div>`,
          true
        );
        event.stopPropagation();
        return;
      } else {
        if (firstNode === data) {
          showCompareModal(
            `<div class="modal-title">Comparison Mode</div>
            <div class="modal-message" style="color:#c0392b;">Please select a <b>different node</b> for comparison.</div>`,
            true
          );
          event.stopPropagation();
          return;
        }

        const getPathToRoot = (node) => {
          let path = [];
          while (node) {
            path.push(node);
            node = node.parent;
          }
          return path.reverse();
        };
        const pathA = getPathToRoot(firstNode);
        const pathB = getPathToRoot(data);

        let lcaIndex = 0;
        while (
          lcaIndex < pathA.length &&
          lcaIndex < pathB.length &&
          pathA[lcaIndex] === pathB[lcaIndex]
        ) {
          lcaIndex++;
        }
        const stepsA = pathA.length - lcaIndex;
        const stepsB = pathB.length - lcaIndex;
        const gap = Math.max(stepsA, stepsB);

        showCompareModal(
          `<div class="modal-title">Comparison Result</div>
          <div class="modal-message" style="line-height:1.6;">
            <span style="color:#7d3c98;font-weight:bold;">${firstNode.data.name}</span>
            <span style="font-size:1.12em;"> vs. </span>
            <span style="color:#7d3c98;font-weight:bold;">${data.data.name}</span><br>
            <span style="font-size:115%;color:#0078d7">Generation gap after their common ancestor is <b>${gap}</b></span>
          </div>`,
          false,
          true
        );
        comparisonTimeout = setTimeout(() => {
          exitCompareMode();
        }, 12000);
        event.stopPropagation();
        return;
      }
    },
    true
  );

  // Only add event listener if the button exists
  if (correctionBtn) {
    correctionBtn.addEventListener("click", () => {
    if (!selectedNode) return;
    modalRoot.innerHTML = `
      <div class="modal-overlay" id="correction-modal">
        <div class="modal-title">Correction for: ${selectedNode.data.name}</div>
        <input id="corrected-name" type="text" placeholder="Type the corrected name here..." autocomplete="off" spellcheck="false" />
        <div class="modal-action-row">
          <button id="submit-correction">Submit</button>
          <button class="cancel-btn" id="cancel-correction">Cancel</button>
        </div>
      </div>
    `;
    makeModalDraggable(document.getElementById("correction-modal"));
    const input = document.getElementById("corrected-name");
    input.focus();
    input.select();
    document.getElementById("submit-correction").onclick = () => {
      const corrected = input.value.trim();
      if (corrected) {
        fetch("/submit-correction/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
          },
          body: JSON.stringify({ original: selectedNode.data.name, corrected }),
        })
          .then((response) => {
            if (!response.ok) {
              throw new Error("Network response was not ok");
            }
            return response;
          })
          .then(() => {
            modalRoot.innerHTML = "";
            alert("Correction submitted.");
            selectedNode = null;
            updateActionButtons();
          })
          .catch((error) => {
            console.error("Error submitting correction:", error);
            alert("Error submitting correction. Please try again.");
          });
      }
    };
    document.getElementById("cancel-correction").onclick = () =>
      (modalRoot.innerHTML = "");
    });
  }
  function getCSRFToken() {
    const cookie = document.cookie
      .split(";")
      .find((c) => c.trim().startsWith("csrftoken="));
    return cookie ? cookie.split("=")[1] : "";
  }
  document.getElementById("reset-zoom")?.addEventListener("click", resetZoom);
  document.getElementById("reload-tree")?.addEventListener("click", () => {
    loadTreeData();
    resetHighlight();
    selectedNode = null;
  });
  // expand all nodes function
  function expandAll(node) {
    if (node._children && node._children.length > 0) {
      node.children = node._children;
      node._children = [];
    }
    if (node.children) {
      node.children.forEach(expandAll);
    }
  }

  document.getElementById("expand-all")?.addEventListener("click", () => {
    console.log("Expanding all nodes");
    expandAll(rootData);
    renderTree(rootData);

    // Add this code to ensure visibility after expansion
    setTimeout(() => {
      const bounds = g.node().getBBox();
      const svgWidth = container.clientWidth;
      const svgHeight = container.clientHeight;

      // Use a very small scale to fit the entire expanded tree
      let scale =
        Math.min(
          svgWidth / (bounds.width + 200),
          svgHeight / (bounds.height + 200)
        ) * 0.9;
      scale = Math.max(scale, 0.05);

      const translateX =
        svgWidth / 2 - bounds.x * scale - (bounds.width * scale) / 2;
      const translateY = 50 - bounds.y * scale; // Position near top

      svg
        .transition()
        .duration(800)
        .call(
          zoom.transform,
          d3.zoomIdentity.translate(translateX, translateY).scale(scale)
        );
      currentZoomTransform = d3.zoomIdentity
        .translate(translateX, translateY)
        .scale(scale);
    }, 300);
  });

  document.getElementById("expand-all")?.addEventListener("click", () => {
    console.log("Expanding all nodes");
    expandAll(rootData);
    renderTree(rootData);
  });
  //collapse all nodes function
  // Add this function inside your DOMContentLoaded function
  function collapseAll(node) {
    if (node.children && node.children.length > 0) {
      node._children = node.children;
      node.children = [];
      node._children.forEach(collapseAll);
    } else if (node._children) {
      node._children.forEach(collapseAll);
    }
  }

  // Add this event listener inside your DOMContentLoaded function
  document.getElementById("collapse-all")?.addEventListener("click", () => {
    console.log("Collapsing all nodes");
    // Keep root node expanded, but collapse all its children
    if (rootData.children && rootData.children.length > 0) {
      rootData.children.forEach(collapseAll);
    }
    renderTree(rootData);
  });
  // function loadTreeData() {
  //   fetch("/data/")
  //     .then((res) => res.json())
  //     .then((data) => {
  //       rootData = data;

  //       // Create hierarchy without collapsing any nodes
  //       d3root = d3.hierarchy(rootData, d => d.children || d._children);
  //       renderTree(rootData);
  //     });
  // }

  function loadTreeData() {
    console.log('Loading tree data...');
    try {
      console.log("Loading tree data...");
      
      // Check if window.USER_TREE_DATA exists first
      if (window.USER_TREE_DATA) {
        console.log("Using USER_TREE_DATA");
        rootData = window.USER_TREE_DATA;
        
        // Safely process the tree data
        if (!rootData) {
          console.error("Tree data is null or undefined");
          return;
        }
        
        // Process the tree based on view type
        if (!window.IS_MY_TREE) {
          // For main tree view, show 3 generations from root
          function collapseDeep(node, depth) {
            if (!node) return;
            
            // Show first 3 generations (depth 0, 1, and 2)
            if (depth < 3) {
              // For root node (depth 0), show first 4 children
              if (depth === 0 && node.children && node.children.length > 4) {
                node._children = node.children.slice(4);
                node.children = node.children.slice(0, 4);
              }
              
              // For nodes in first 3 generations, keep their children visible
              if (node.children) {
                node.children.forEach(child => collapseDeep(child, depth + 1));
              }
            } else {
              // For nodes beyond 3rd generation, collapse their children
              if (node.children && node.children.length > 0) {
                node._children = node.children;
                node.children = [];
              }
            }
            
            // Handle any _children
            if (node._children) {
              node._children.forEach(child => collapseDeep(child, depth + 1));
            }
          }
          
          collapseDeep(rootData, 0);
        } else if (window.COLLAPSE_SIBLINGS) {
          // For my_tree view with collapsed siblings
          // The initial processing is done in the HTML template
          // We just need to make sure the current user's node is visible
          
          // Find the current user's node and highlight it
          function findUserNode(node) {
            if (!node) return null;
            
            if (node.is_current_user === true) {
              return node;
            }
            
            if (node.children) {
              for (let child of node.children) {
                const found = findUserNode(child);
                if (found) return found;
              }
            }
            
            return null;
          }
          
          // Find and select the user's node
          const userNode = findUserNode(rootData);
          if (userNode) {
            console.log("Found user node:", userNode.name);
            // We'll select this node after rendering
            window.userNodeId = userNode.id;
          }
        } else {
          // For my_tree view with all nodes expanded
          function expandAll(node) {
            if (!node) return;
            if (node._children && node._children.length > 0) {
              node.children = node._children;
              node._children = [];
            }
            if (node.children) {
              node.children.forEach(expandAll);
            }
          }
          
          // Make sure all nodes are expanded
          expandAll(rootData);
        }
        
        console.log("Tree data loaded successfully");
        
        // Create hierarchy with null check
        d3root = d3.hierarchy(rootData, (d) => {
          if (!d) return null;
          return d.children || d._children;
        });
        
        renderTree(rootData);
        
        // Make loadTreeData function available globally for reloading
        window.loadTreeData = loadTreeData;
      } else {
        console.log("Fetching tree data from server");
        // Use the standard data endpoint with full ancestry parameter for my_tree
        const url = window.IS_MY_TREE ? "/data/?full_ancestry=true" : "/data/";
        
        fetch(url)
          .then((res) => res.json())
          .then((data) => {
            rootData = data;
            
            if (!rootData) {
              console.error("Fetched tree data is null or undefined");
              return;
            }
            
            // For my_tree.html, don't collapse any nodes
            if (!window.IS_MY_TREE) {
              // For main tree view, show 3 generations from root
              function collapseDeep(node, depth) {
                if (!node) return;
                
                // Show first 3 generations (depth 0, 1, and 2)
                if (depth < 3) {
                  // For root node (depth 0), show first 4 children
                  if (depth === 0 && node.children && node.children.length > 4) {
                    node._children = node.children.slice(4);
                    node.children = node.children.slice(0, 4);
                  }
                  
                  // For nodes in first 3 generations, keep their children visible
                  if (node.children) {
                    node.children.forEach(child => collapseDeep(child, depth + 1));
                  }
                } else {
                  // For nodes beyond 3rd generation, collapse their children
                  if (node.children && node.children.length > 0) {
                    node._children = node.children;
                    node.children = [];
                  }
                }
                
                // Handle any _children
                if (node._children) {
                  node._children.forEach(child => collapseDeep(child, depth + 1));
                }
              }
              
              collapseDeep(rootData, 0);
            } else {
              // For my_tree view, make sure all nodes are expanded
              function expandAll(node) {
                if (!node) return;
                if (node._children && node._children.length > 0) {
                  node.children = node._children;
                  node._children = [];
                }
                if (node.children) {
                  node.children.forEach(expandAll);
                }
              }
              
              expandAll(rootData);
            }
            
            console.log("Tree data fetched successfully");
            
            // Create hierarchy with null check
            d3root = d3.hierarchy(rootData, (d) => {
              if (!d) return null;
              return d.children || d._children;
            });
            
            renderTree(rootData);
            
            // Make loadTreeData function available globally for reloading
            window.loadTreeData = loadTreeData;
          })
          .catch(err => console.error("Error loading tree data:", err));
      }
    } catch (error) {
      console.error("Error in loadTreeData:", error);
    }
  }

  loadTreeData();

  const addNameBtn = document.getElementById("add-name");
  if (addNameBtn) {
    addNameBtn.onclick = function () {
      window.location.href = this.dataset.addMemberUrl;
    };
  }

  function handleEditMemberClick(memberId) {
    console.log('Edit button clicked for member:', memberId);
    print('edit member click');
    
    if (!memberId) {
        console.error('No member ID provided');
        return;
    }
    
    if (!window.EDIT_MEMBER_URL) {
        console.error('EDIT_MEMBER_URL not defined');
        return;
    }
    
    const url = window.EDIT_MEMBER_URL.replace('{id}', memberId);
    console.log('Navigating to:', url);
    window.location.href = url;
  }

  // Function to show compare and correction buttons
  function showCompareCorrectionButtons() {
    document.getElementById('comparenode-btn')?.classList.add('show');
    document.getElementById('correctionname-btn')?.classList.add('show');
  }

  // Function to hide compare and correction buttons
  function hideCompareCorrectionButtons() {
    document.getElementById('comparenode-btn')?.classList.remove('show');
    document.getElementById('correctionname-btn')?.classList.remove('show');
  }

  // Show compare and correction buttons when needed
  document.addEventListener('nodeSelected', function(e) {
    if (e.detail && e.detail.selectedNodes && e.detail.selectedNodes.length >= 2) {
      showCompareCorrectionButtons();
    } else {
      hideCompareCorrectionButtons();
    }
  });

  // Add this at the end of the file or after the share-whatsapp-btn is created
  if (window.matchMedia) {
    const mq = window.matchMedia('(max-width: 768px)');
    function updateShareBtnStyle(e) {
      const shareBtn = document.querySelector('.share-tree-btn');
      if (!shareBtn) return;
      
      // Get viewport width
      const viewportWidth = window.innerWidth;
      
      // Hide button on mobile devices
      if (viewportWidth <= 768) {
          shareBtn.style.display = 'none';
      } else {
          // Make button smaller
          shareBtn.style.padding = '6px 12px';
          shareBtn.style.fontSize = '0.9rem';
          shareBtn.style.borderRadius = '4px';
          
          // Add hover effect
          shareBtn.style.transition = 'all 0.2s ease';
          shareBtn.addEventListener('mouseover', () => {
              shareBtn.style.transform = 'scale(1.05)';
              shareBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
          });
          shareBtn.addEventListener('mouseout', () => {
              shareBtn.style.transform = 'scale(1)';
              shareBtn.style.boxShadow = 'none';
          });
      }
    }
    mq.addEventListener('change', updateShareBtnStyle);
    updateShareBtnStyle(mq);
  }
});
