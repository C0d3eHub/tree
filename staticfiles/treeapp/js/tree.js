document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("tree-container");
  if (!container) return;

  const svg = d3.select("#tree-svg")
    .attr("width", container.clientWidth + 1000)
    .attr("height", container.clientHeight + 1000);

  svg.select("defs").remove();
  svg.append("defs").append("marker")
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

  let g = svg.append("g").attr("class", "tree-group");

  // Compact, nice node sizing
  const MIN_NODE_WIDTH = 60, MIN_NODE_HEIGHT = 36;
  const NODE_HORIZ_PADDING = 18, NODE_VERT_PADDING = 14;
  const NODE_MARGIN_X = 10, NODE_MARGIN_Y = 16;

  let treeLayout, rootData, d3root, originalPositions = null;
  let compareMode = false, firstNode = null, selectedNode = null, comparisonTimeout;
  const compareBtn = document.getElementById("comparenode-btn");
  const correctionBtn = document.getElementById("correctionname-btn");
  const modalRoot = document.getElementById("dynamic-modal-root");

  // Zoom/pan
  const zoom = d3.zoom()
    .scaleExtent([0.05, 25])
    .translateExtent([[-20000, -20000], [20000, 20000]])
    .on("zoom", (event) => g.attr("transform", event.transform));
  svg.call(zoom);

  function getColorByDepth(depth) {
    const colors = [
      "#1abc9c", "#3498db", "#e67e22",
      "#9b59b6", "#e74c3c", "#f1c40f"
    ];
    return colors[depth % colors.length];
  }
  function getDarkerColor(hex) {
    return d3.color(hex).darker(1.5).toString();
  }
  function updateActionButtons() {
    if (selectedNode && !compareMode) {
      compareBtn.style.display = "inline-block";
      correctionBtn.style.display = "inline-block";
    } else {
      compareBtn.style.display = "none";
      correctionBtn.style.display = "none";
    }
  }
  function resetZoom() {
    const svgWidth = container.clientWidth, svgHeight = container.clientHeight;
    const bounds = g.node().getBBox();
    const scale = Math.min(svgWidth / bounds.width, svgHeight / bounds.height) * 0.85;
    const translateX = svgWidth / 2 - (bounds.x + bounds.width / 2) * scale;
    const translateY = svgHeight / 2 - (bounds.y + bounds.height / 2) * scale;
    svg.transition().duration(600)
      .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
  }

  // Collapse/expand: children in d._children, visible children in d.children
  function toggleCollapse(d) {
    if (d.children) {
      d._children = d.children;
      d.children = null;
    } else if (d._children) {
      d.children = d._children;
      d._children = null;
    }
    renderTree(rootData, d.data.id ? d.data.id : d.data.name, true);
  }

  // Highlight: ancestors+subtree, all in a vertical line (same X)
  function highlightAncestorsAndSubtree(selectedNode) {
    if (!originalPositions) {
      originalPositions = d3root.descendants().map(d => ({ d, x: d.x, y: d.y }));
    }
    // 1. Find all ancestors (root to selected)
    let ancestors = [];
    let curr = selectedNode;
    while (curr) {
      ancestors.push(curr);
      curr = curr.parent;
    }
    ancestors = ancestors.reverse();
    // 2. All descendants (including selected)
    const descendants = [];
    selectedNode.each(n => descendants.push(n));
    // 3. Union: root to selected + selected's descendants
    const highlightNodes = Array.from(new Set([...ancestors, ...descendants]));
    // 4. Align all highlight nodes to same x (selectedNode.x)
    highlightNodes.forEach(n => n.x = selectedNode.x);

    drawNodesAndLinks(d3root);

    g.selectAll(".node rect").attr("opacity", d => highlightNodes.includes(d) ? 1 : 0.2)
      .attr("stroke", d => highlightNodes.includes(d) ? "lime" : null)
      .attr("stroke-width", d => highlightNodes.includes(d) ? 3 : null);
    g.selectAll(".link")
      .attr("opacity", d => highlightNodes.includes(d.target) && highlightNodes.includes(d.source) ? 1 : 0.1)
      .attr("stroke", d => highlightNodes.includes(d.target) && highlightNodes.includes(d.source) ? "lime" : getDarkerColor(getColorByDepth(d.source.depth)))
      .attr("stroke-width", d => highlightNodes.includes(d.target) && highlightNodes.includes(d.source) ? 3 : 2);

    // Vertical spine: from root's y to lowest descendant's y, at selectedNode.x
    g.selectAll(".highlight-spine").remove();
    const y1 = highlightNodes[0].y - (highlightNodes[0].data._textHeight + NODE_VERT_PADDING) / 2;
    const y2 = d3.max(highlightNodes, d => d.y + (d.data._textHeight + NODE_VERT_PADDING) / 2);
    g.append("line").attr("class", "highlight-spine")
      .attr("x1", selectedNode.x).attr("x2", selectedNode.x)
      .attr("y1", y1).attr("y2", y2)
      .attr("stroke", "lime").attr("stroke-width", 7).attr("opacity", 0.18).lower();
  }

  function resetHighlight() {
    if (originalPositions) {
      originalPositions.forEach(obj => { obj.d.x = obj.x; obj.d.y = obj.y; });
      originalPositions = null;
      drawNodesAndLinks(d3root);
    }
    g.selectAll(".highlight-spine").remove();
    g.selectAll(".node rect").attr("opacity", 1).attr("stroke", null).attr("stroke-width", null);
    g.selectAll(".link")
      .attr("opacity", 1)
      .attr("stroke", (d) => getDarkerColor(getColorByDepth(d.source.depth)))
      .attr("stroke-width", 2);
  }

  svg.on("click", () => {
    if (compareMode) return;
    resetHighlight(); selectedNode = null; updateActionButtons(); modalRoot.innerHTML = "";
  });

  function drawNodesAndLinks(root) {
    g.selectAll("*").remove();

    g.selectAll(".link").data(root.links())
      .enter().append("path")
      .attr("class", "link")
      .attr("fill", "none")
      .attr("stroke", d => getDarkerColor(getColorByDepth(d.source.depth)))
      .attr("stroke-width", 2)
      .attr("marker-end", "url(#arrowhead)")
      .attr("d", function (d) {
        // 3px gap to top
        const sourceWidth = Math.max(d.source.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH);
        const sourceHeight = Math.max(d.source.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT);
        const targetWidth = Math.max(d.target.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH);
        const targetHeight = Math.max(d.target.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT);
        const startX = d.source.x;
        const startY = d.source.y + sourceHeight / 2 - 3;
        const endX = d.target.x;
        const endY = d.target.y - targetHeight / 2 - 3;
        const elbowY = (startY + endY) / 2;
        return `M${startX},${startY} V${elbowY} H${endX} V${endY}`;
      });

    const nodes = g.selectAll(".node")
      .data(root.descendants())
      .enter().append("g")
      .attr("class", "node")
      .attr("transform", d => `translate(${d.x},${d.y})`)
      .on("click", function (event, d) {
        if (event.target.classList.contains('collapser')) return;
        event.stopPropagation();
        selectedNode = d;
        resetHighlight();
        highlightAncestorsAndSubtree(d);
        updateActionButtons();
        modalRoot.innerHTML = "";
      });

    nodes.insert("rect", "text")
      .attr("x", d => -Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH) / 2)
      .attr("y", d => -Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT) / 2)
      .attr("width", d => Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH))
      .attr("height", d => Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT))
      .attr("rx", 10)
      .attr("fill", d => getColorByDepth(d.depth));

    nodes.append("text")
      .attr("dy", 5)
      .attr("text-anchor", "middle")
      .attr("fill", "#fff")
      .attr("font-family", "sans-serif")
      .attr("font-size", 16)
      .text(d => d.data.name);

    nodes.filter(d => (d.children && d.children.length) || (d._children && d._children.length))
      .append("g")
      .attr("class", "collapser")
      .attr("transform", d => {
        let w = Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH);
        return `translate(${w / 2 + 19},0)`;
      })
      .style("cursor", "pointer")
      .each(function (d) {
        d3.select(this).append("circle")
          .attr("r", 10)
          .attr("fill", "#fff")
          .attr("stroke", "#888")
          .attr("stroke-width", 2)
          .attr("class", "collapser");
        if (d.children) {
          d3.select(this).append("line")
            .attr("x1", -5).attr("x2", 5).attr("y1", 0).attr("y2", 0)
            .attr("stroke", "#888").attr("stroke-width", 2)
            .attr("class", "collapser");
        } else {
          d3.select(this).append("line")
            .attr("x1", -5).attr("x2", 5).attr("y1", 0).attr("y2", 0)
            .attr("stroke", "#888").attr("stroke-width", 2)
            .attr("class", "collapser");
          d3.select(this).append("line")
            .attr("x1", 0).attr("x2", 0).attr("y1", -5).attr("y2", 5)
            .attr("stroke", "#888").attr("stroke-width", 2)
            .attr("class", "collapser");
        }
        d3.select(this).on("click", function (event) {
          event.stopPropagation();
          resetHighlight();
          toggleCollapse(d);
        });
      });
  }

  function renderTree(data, focusIdOrName, preserveZoom = false) {
    rootData = data;
    d3root = d3.hierarchy(data, d => d.children ? d.children : d._children);
    // Measure text
    const tempSvg = d3.select("body").append("svg").style("visibility", "hidden");
    d3root.descendants().forEach(d => {
      const textElem = tempSvg.append("text")
        .attr("font-family", "sans-serif")
        .attr("font-size", 16)
        .text(d.data.name);
      const bbox = textElem.node().getBBox();
      d.data._textWidth = bbox.width;
      d.data._textHeight = bbox.height;
      textElem.remove();
    });
    tempSvg.remove();

    let maxNodeWidth = d3.max(d3root.descendants(), d => Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH));
    let maxNodeHeight = d3.max(d3root.descendants(), d => Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT));
    treeLayout = d3.tree().nodeSize([maxNodeWidth + NODE_MARGIN_X, maxNodeHeight + NODE_MARGIN_Y]);
    treeLayout(d3root);
    drawNodesAndLinks(d3root);

    // Only reset zoom if not preserving it (default: only on reload)
    if (!preserveZoom) {
      setTimeout(() => {
        let node = d3root;
        if (focusIdOrName) {
          node = d3root.descendants().find(n => n.data.id === focusIdOrName || n.data.name === focusIdOrName) || d3root;
        }
        const svgWidth = container.clientWidth, svgHeight = container.clientHeight;
        const bounds = g.node().getBBox();
        const scale = Math.min(svgWidth / bounds.width, svgHeight / bounds.height) * 0.85;
        const translateX = svgWidth / 2 - (bounds.x + bounds.width / 2) * scale;
        const translateY = svgHeight / 2 - (bounds.y + bounds.height / 2) * scale;
        svg.transition().duration(500)
          .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
      }, 0);
    }
  }

  // Modal, compare, correction logic unchanged...

  function showCompareModal(htmlBody, showCancel = false, onlyOk = false) {
    modalRoot.innerHTML = `
      <div class="modal-overlay" id="compare-modal" style="user-select: none;">
        ${htmlBody}
        <div class="modal-action-row">
          ${showCancel && !onlyOk ? `<button class="cancel-btn" id="cancel-compare">Cancel</button>` : ""}
          ${onlyOk ? `<button id="close-compare-modal">OK</button>` : ""}
        </div>
      </div>
    `;
    makeModalDraggable(document.getElementById("compare-modal"));
    if (showCancel && !onlyOk) document.getElementById("cancel-compare").onclick = () => exitCompareMode();
    if (onlyOk) document.getElementById("close-compare-modal").onclick = () => exitCompareMode();
  }
  function makeModalDraggable(modalEl) {
    let isDragging = false, dragOffsetX = 0, dragOffsetY = 0;
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
      if (isDragging) { isDragging = false; modalEl.style.cursor = "grab"; }
    });
    modalEl.addEventListener("touchstart", function (e) {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      isDragging = true;
      const touch = e.touches[0];
      dragOffsetX = touch.clientX - modalEl.getBoundingClientRect().left;
      dragOffsetY = touch.clientY - modalEl.getBoundingClientRect().top;
      e.preventDefault();
    }, { passive: false });
    document.addEventListener("touchmove", function (e) {
      if (!isDragging) return;
      const touch = e.touches[0];
      modalEl.style.left = touch.clientX - dragOffsetX + "px";
      modalEl.style.top = touch.clientY - dragOffsetY + "px";
    }, { passive: false });
    document.addEventListener("touchend", function () { if (isDragging) isDragging = false; });
  }
  function exitCompareMode() {
    compareMode = false;
    firstNode = null;
    modalRoot.innerHTML = "";
    selectedNode = null;
    updateActionButtons();
    resetHighlight();
    if (comparisonTimeout) clearTimeout(comparisonTimeout);
  }
  compareBtn.addEventListener("click", () => {
    if (!selectedNode) return;
    compareMode = true; firstNode = null; updateActionButtons();
    showCompareModal(
      `<div class="modal-title">Comparison Mode</div>
        <div class="modal-message">
          <span style="font-weight:bold;color:#0078d7;">Compare generations</span><br>
          Select <b>first node</b> in the tree to begin.<br>
        </div>`,
      true
    );
  });
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
    input.focus(); input.select();
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
        }).then(() => {
          modalRoot.innerHTML = "";
          alert("Correction submitted.");
          selectedNode = null;
          updateActionButtons();
        });
      }
    };
    document.getElementById("cancel-correction").onclick = () => (modalRoot.innerHTML = "");
  });
  function getCSRFToken() {
    const cookie = document.cookie.split(";").find((c) => c.trim().startsWith("csrftoken="));
    return cookie ? cookie.split("=")[1] : "";
  }
  function loadTreeData() {
    fetch("/data/")
      .then((res) => res.json())
      .then((data) => renderTree(data));
  }
  document.getElementById("reset-zoom")?.addEventListener("click", resetZoom);
  document.getElementById("reload-tree")?.addEventListener("click", () => {
    loadTreeData();
    resetHighlight();
    selectedNode = null;
    updateActionButtons();
  });

  loadTreeData();
  updateActionButtons();
});
document.getElementById('add-name').onclick = function() {
  window.location.href = this.dataset.addMemberUrl;
};