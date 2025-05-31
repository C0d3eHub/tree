document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("tree-container");
  if (!container) return;

  const svg = d3.select("#tree-svg")
    .attr("width", container.clientWidth + 1000)
    .attr("height", container.clientHeight + 1000);

  svg.select("defs").remove();
  const defs = svg.append("defs");
  defs.append("marker")
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
  defs.append("filter")
    .attr("id", "button-shadow")
    .html(`<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#bbb" flood-opacity="0.6"/>`);

  let g = svg.append("g").attr("class", "tree-group");

  const MIN_NODE_WIDTH = 60, MIN_NODE_HEIGHT = 36;
  const NODE_HORIZ_PADDING = 18, NODE_VERT_PADDING = 14;
  const NODE_MARGIN_X = 10, NODE_MARGIN_Y = 36;

  let treeLayout, rootData, d3root;
  let selectedNode = null;
  let highlightMode = false;
  let compareMode = false, firstNode = null, comparisonTimeout = null;

  const compareBtn = document.getElementById("comparenode-btn");
  const correctionBtn = document.getElementById("correctionname-btn");
  const modalRoot = document.getElementById("dynamic-modal-root");

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

  function resetZoom() {
    const bounds = g.node().getBBox();
    const svgWidth = container.clientWidth, svgHeight = container.clientHeight;
    const scale = Math.min(svgWidth / bounds.width, svgHeight / bounds.height) * 0.85;
    const translateX = svgWidth / 2 - (bounds.x + bounds.width / 2) * scale;
    const translateY = svgHeight / 2 - (bounds.y + bounds.height / 2) * scale;
    svg.transition().duration(600)
      .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
  }

  function focusOnNodes(nodes) {
    if (!nodes.length) return;
    const minX = d3.min(nodes, d => d.x), maxX = d3.max(nodes, d => d.x);
    const minY = d3.min(nodes, d => d.y), maxY = d3.max(nodes, d => d.y);
    const padding = 80;
    const width = maxX - minX + padding * 2;
    const height = maxY - minY + padding * 2;
    const svgWidth = container.clientWidth, svgHeight = container.clientHeight;
    const scale = Math.min(svgWidth / width, svgHeight / height) * 0.85;
    const translateX = svgWidth / 2 - ((minX + maxX) / 2) * scale;
    const translateY = svgHeight / 2 - ((minY + maxY) / 2) * scale;
    svg.transition().duration(600)
      .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
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

  function copyCollapseState(source, target) {
    if (!source || !target) return;
    if (source._children) {
      target._children = target.children;
      target.children = null;
    }
    if (source.children && target.children) {
      for (let i = 0; i < source.children.length; i++) {
        copyCollapseState(source.children[i], target.children[i]);
      }
    } else if (source._children && target._children) {
      for (let i = 0; i < source._children.length; i++) {
        copyCollapseState(source._children[i], target._children[i]);
      }
    }
  }

  function collapseAllExceptRoot(node) {
    if (!node.children) return;
    node._children = node.children;
    node.children = null;
    if (node._children)
      node._children.forEach(collapseAllExceptRoot);
  }

  function renderTree(data, focusIdOrName, preserveZoom = false) {
    let previousRoot = null;
    if (rootData && rootData !== data) {
      previousRoot = d3.hierarchy(rootData, d => d.children || d._children || null);
    }
    d3root = d3.hierarchy(data, d => d.children || d._children || null);
    if (previousRoot) copyCollapseState(previousRoot, d3root);

    // Measure text
    const tempSvg = d3.select("body").append("svg").style("visibility", "hidden");
    (function recMeasure(node) {
      const textElem = tempSvg.append("text")
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

    let maxNodeWidth = Math.max(...d3root.descendants().map(d => Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH)));
    let maxNodeHeight = Math.max(...d3root.descendants().map(d => Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT)));
    treeLayout = d3.tree().nodeSize([maxNodeWidth + NODE_MARGIN_X, maxNodeHeight + NODE_MARGIN_Y]);
    treeLayout(d3root);
    drawNodesAndLinks(d3root);

    if (!preserveZoom) {
      setTimeout(() => {
        let node = d3root;
        if (focusIdOrName) {
          node = d3root.descendants().find(n => n.data.id === focusIdOrName || n.data.name === focusIdOrName) || d3root;
        }
        const bounds = g.node().getBBox();
        const svgWidth = container.clientWidth, svgHeight = container.clientHeight;
        const scale = Math.min(svgWidth / bounds.width, svgHeight / bounds.height) * 0.85;
        const translateX = svgWidth / 2 - (bounds.x + bounds.width / 2) * scale;
        const translateY = svgHeight / 2 - (bounds.y + bounds.height / 2) * scale;
        svg.transition().duration(500)
          .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
      }, 0);
    }
    updateActionButtons();
  }

  function drawNodesAndLinks(root, spine = [], subtree = []) {
    g.selectAll("*").remove();

    const visibleNodes = [];
    function collectVisible(node) {
      visibleNodes.push(node);
      if (node.children && node.children.length)
        node.children.forEach(collectVisible);
    }
    collectVisible(root);

    const visibleLinks = [];
    visibleNodes.forEach(node => {
      if (node.children) {
        node.children.forEach(child => {
          visibleLinks.push({ source: node, target: child });
        });
      }
    });

    g.selectAll(".link").data(visibleLinks)
      .enter().append("path")
      .attr("class", "link")
      .attr("fill", "none")
      .attr("stroke", d => {
        if (spine.includes(d.source) && spine.includes(d.target)) return "lime";
        if (subtree.includes(d.source) && subtree.includes(d.target)) return "#ff0";
        return getDarkerColor(getColorByDepth(d.source.depth));
      })
      .attr("stroke-width", d => {
        if (spine.includes(d.source) && spine.includes(d.target)) return 3;
        if (subtree.includes(d.source) && subtree.includes(d.target)) return 2;
        return 2;
      })
      .attr("opacity", d =>
        (spine.length > 0)
          ? ((spine.includes(d.source) && spine.includes(d.target)) ||
             (subtree.includes(d.source) && subtree.includes(d.target))
            ? 1 : 0.08)
          : 1
      )
      .attr("marker-end", "url(#arrowhead)")
      .attr("d", function (d) {
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
      .data(visibleNodes)
      .enter().append("g")
      .attr("class", "node")
      .attr("transform", d => `translate(${d.x},${d.y})`)
      .style("cursor", "pointer")
      .on("click", function (event, d) {
        if (compareMode) return;
        if (!highlightMode || !selectedNode || selectedNode.data.id !== d.data.id) {
          selectedNode = d;
          highlightSpineAndSubtree(d);
          updateActionButtons();
          if (modalRoot) modalRoot.innerHTML = "";
        }
        event.stopPropagation();
      });

    nodes.insert("rect", "text")
      .attr("x", d => -Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH) / 2)
      .attr("y", d => -Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT) / 2)
      .attr("width", d => Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH))
      .attr("height", d => Math.max(d.data._textHeight + NODE_VERT_PADDING, MIN_NODE_HEIGHT))
      .attr("rx", 10)
      .attr("fill", d => getColorByDepth(d.depth))
      .attr("stroke", d => {
        if (spine.includes(d)) return "lime";
        if (subtree.includes(d)) return "#ff0";
        return null;
      })
      .attr("stroke-width", d => {
        if (spine.includes(d)) return 3;
        if (subtree.includes(d)) return 2;
        return null;
      });

    nodes.append("text")
      .attr("dy", 5)
      .attr("text-anchor", "middle")
      .attr("fill", "#fff")
      .attr("font-family", "sans-serif")
      .attr("font-size", 16)
      .text(d => d.data.name);

    nodes.filter(d => (d.children && d.children.length) || (d._children && d._children.length))
      .append("g")
      .attr("class", "collapse-btn")
      .attr("transform", d => `translate(${Math.max(d.data._textWidth + NODE_HORIZ_PADDING, MIN_NODE_WIDTH)/2 + 18},0)`)
      .style("cursor", "pointer")
      .each(function(d) {
        d3.select(this)
          .append("circle")
          .attr("r", 13)
          .attr("fill", "#fff")
          .attr("stroke", "#888")
          .attr("stroke-width", 2)
          .attr("filter", "url(#button-shadow)");
        d3.select(this)
          .append("text")
          .attr("text-anchor", "middle")
          .attr("dy", 6)
          .attr("font-size", 18)
          .attr("font-weight", 700)
          .attr("fill", "#333")
          .text(d => d.children && d.children.length ? "−" : "+");
      })
      .on("click", function(event, d) {
        event.stopPropagation();
        if (d.children && d.children.length) {
          d._children = d.children;
          d.children = null;
        } else if (d._children && d._children.length) {
          d.children = d._children;
          d._children = null;
        }
        renderTree(rootData, d.data.id, true);
        // --- Fix: If this node was highlighted, re-highlight after redraw
        if (selectedNode && selectedNode.data.id === d.data.id) {
          // Find the corresponding node in new tree
          const newSelected = d3root.descendants().find(n => n.data.id === d.data.id);
          if (newSelected) {
            selectedNode = newSelected;
            highlightSpineAndSubtree(selectedNode);
          }
        }
      });
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
    selectedNode.each(n => subtree.push(n));
    let subtreeRoot = d3.hierarchy(selectedNode.data, d => d.children || d._children);
    const tempSvg = d3.select("body").append("svg").style("visibility", "hidden");
    (function recMeasure(node) {
      const textElem = tempSvg.append("text")
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
    const subtreeTree = d3.tree().nodeSize([MIN_NODE_WIDTH + NODE_MARGIN_X, MIN_NODE_HEIGHT + NODE_MARGIN_Y]);
    subtreeTree(subtreeRoot);
    let yOffset = spine[spine.length - 1].y;
    let xOffset = x0 + MIN_NODE_WIDTH + 80;
    subtreeRoot.each((d, i) => {
      if (i === 0) return;
      let realNode = subtree.find(n => n.data.name === d.data.name && n.depth === (selectedNode.depth + d.depth));
      if (realNode) {
        realNode.x = xOffset + d.x;
        realNode.y = yOffset + d.y;
      }
    });

    drawNodesAndLinks(d3root, spine, subtree);

    g.selectAll(".highlight-spine").remove();
    g.append("line")
      .attr("class", "highlight-spine")
      .attr("x1", x0).attr("x2", x0)
      .attr("y1", spine[0].y)
      .attr("y2", spine[spine.length - 1].y)
      .attr("stroke", "lime").attr("stroke-width", 7).attr("opacity", 0.18).lower();

    g.selectAll(".node rect").attr("opacity", d =>
      (spine.includes(d) || subtree.includes(d)) ? 1 : 0.35
    );
    g.selectAll(".link").attr("opacity", d =>
      (spine.includes(d.source) && spine.includes(d.target)) ||
      (subtree.includes(d.source) && subtree.includes(d.target))
        ? 1 : 0.25
    );
    g.selectAll("text").attr("opacity", d =>
      (spine.includes(d) || subtree.includes(d)) ? 1 : 0.38
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

  // Only reset highlight when NOT in compare mode, NOT clicking modal, and NOT inside a node
  document.addEventListener("click", function (event) {
    if (modalRoot && modalRoot.innerHTML.trim() !== "") return;
    if (compareMode) return;
    if (event.target.closest(".node")) return;
    if (event.target.closest(".modal-overlay")) return;
    resetHighlight();
  });

  // --- Compare and Correction Modal Logic and event handlers, unchanged from previous versions ---

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

  document.body.addEventListener("click", function (event) {
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

      const getPathToRoot = node => {
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
        false, true
      );
      comparisonTimeout = setTimeout(() => {
        exitCompareMode();
      }, 12000);
      event.stopPropagation();
      return;
    }
  }, true);

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

  document.getElementById("reset-zoom")?.addEventListener("click", resetZoom);
  document.getElementById("reload-tree")?.addEventListener("click", () => {
    loadTreeData();
    resetHighlight();
    selectedNode = null;
  });

  function loadTreeData() {
    fetch("/data/")
      .then((res) => res.json())
      .then((data) => {
        if (!rootData) {
          collapseAllExceptRoot(data);
        }
        rootData = data;
        renderTree(rootData);
      });
  }

  loadTreeData();

  document.getElementById('add-name').onclick = function() {
    window.location.href = this.dataset.addMemberUrl;
  };
});