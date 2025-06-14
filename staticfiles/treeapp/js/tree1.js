document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("tree-container");
  if (!container) return;

  const svg = d3
    .select("#tree-svg")
    .attr("width", container.clientWidth + 1000)
    .attr("height", container.clientHeight + 1000);

  // ---- ARROWHEAD DEFINITION: Best practice ----
  svg.append("defs").append("marker")
    .attr("id", "arrowhead")
    .attr("viewBox", "0 -6 12 12")
    .attr("refX", 11) // tip of arrow at end of line
    .attr("refY", 0)
    .attr("markerWidth", 12)
    .attr("markerHeight", 12)
    .attr("orient", "auto")
    .attr("markerUnits", "userSpaceOnUse")
    .append("path")
    .attr("d", "M0,-6L12,0L0,6Z")
    .attr("fill", "#cc3366");
  // ---- END ARROWHEAD ----

  const g = svg.append("g").attr("class", "tree-group");

  const zoom = d3
    .zoom()
    .scaleExtent([0.05, 25])
    .translateExtent([
      [-5000, -5000],
      [5000, 5000],
    ])
    .on("zoom", (event) => g.attr("transform", event.transform));
  svg.call(zoom);

  // Horizontal layout: [vertical_gap, horizontal_gap]
  const treeLayout = d3.tree().nodeSize([150, 100]);

  const compareBtn = document.getElementById("comparenode-btn");
  const correctionBtn = document.getElementById("correctionname-btn");
  const modalRoot = document.getElementById("dynamic-modal-root");

  let compareMode = false;
  let firstNode = null;
  let selectedNode = null;
  let comparisonTimeout;

  function updateActionButtons() {
    if (selectedNode && !compareMode) {
      compareBtn.style.display = "inline-block";
      correctionBtn.style.display = "inline-block";
    } else {
      compareBtn.style.display = "none";
      correctionBtn.style.display = "none";
    }
  }

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
    const svgWidth = container.clientWidth;
    const svgHeight = container.clientHeight;
    const bounds = g.node().getBBox();
    const scale =
      Math.min(svgWidth / bounds.width, svgHeight / bounds.height) * 0.8;
    const translateX = svgWidth / 2 - (bounds.x + bounds.width / 2) * scale;
    const translateY = svgHeight / 2 - (bounds.y + bounds.height / 2) * scale;

    svg
      .transition()
      .duration(600)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(translateX, translateY).scale(scale)
      );
  }

  function highlightSubtree(selectedNode) {
    g.selectAll(".node rect").attr("opacity", 0.3);
    g.selectAll(".link").attr("opacity", 0.1);

    const allNodes = new Set();
    const allLinks = new Set();

    selectedNode.each((n) => allNodes.add(n));
    let current = selectedNode;
    while (current) {
      allNodes.add(current);
      current = current.parent;
    }

    g.selectAll(".link").each(function (d) {
      if (allNodes.has(d.source) && allNodes.has(d.target)) {
        allLinks.add(this);
      }
    });

    g.selectAll(".node").each(function (d) {
      if (allNodes.has(d)) {
        d3.select(this)
          .select("rect")
          .attr("opacity", 1)
          .attr("stroke", "lime")
          .attr("stroke-width", 3);
      }
    });

    allLinks.forEach((link) => {
      d3.select(link)
        .attr("opacity", 1)
        .attr("stroke", "lime")
        .attr("stroke-width", 3);
    });
  }

  function resetHighlight() {
    g.selectAll(".node rect")
      .attr("opacity", 1)
      .attr("stroke", null)
      .attr("stroke-width", null);
    g.selectAll(".link")
      .attr("opacity", 1)
      .attr("stroke", (d) => getDarkerColor(getColorByDepth(d.source.depth)))
      .attr("stroke-width", 2);
  }

  svg.on("click", () => {
    if (compareMode) return;
    resetHighlight();
    selectedNode = null;
    updateActionButtons();
    modalRoot.innerHTML = "";
  });

  function renderTree(data) {
    g.selectAll("*").remove();

    const root = d3.hierarchy(data);
    treeLayout(root);

    // Swap x and y for horizontal layout
    root.each(function (d) {
      const oldX = d.x;
      d.x = d.y;
      d.y = oldX;
    });

    const xExtent = d3.extent(root.descendants(), (d) => d.x);
    const yExtent = d3.extent(root.descendants(), (d) => d.y);
    const centerX = (xExtent[0] + xExtent[1]) / 2;
    const centerY = (yExtent[0] + yExtent[1]) / 2;

    svg
      .transition()
      .duration(500)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(
          svg.node().clientWidth / 4,
          svg.node().clientHeight / 2 - centerY
        )
      );

    // Draw curved links (cubic Bezier, left to right)
    g.selectAll(".link")
      .data(root.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr("fill", "none")
      .attr("stroke", (d) => getDarkerColor(getColorByDepth(d.source.depth)))
      .attr("stroke-width", 2)
      .attr("marker-end", "url(#arrowhead1)")
      .attr("d", (d) => {
        const rectWidth = 80;
        const rectHalfWidth = rectWidth / 2;
        // start at right edge of source, centered vertically
        const startX = d.source.x + rectHalfWidth;
        const startY = d.source.y;
        // end at left edge of target, centered vertically
        const endX = d.target.x - rectHalfWidth;
        const endY = d.target.y;
        const midX = (startX + endX) / 2;
        return [
          `M${startX},${startY}`,
          `C${midX},${startY} ${midX},${endY} ${endX},${endY}`,
        ].join(" ");
      });

    // Draw nodes
    const nodes = g
      .selectAll(".node")
      .data(root.descendants())
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`)
      .on("click", (event, d) => {
        event.stopPropagation();

        // If in compare mode
        if (compareMode) {
          if (!firstNode) {
            firstNode = d;
            showCompareModal(
              `<div class="modal-title">Comparison Mode</div>
                             <div class="modal-message">First node: <b>${d.data.name}</b><br>Select <b>second node</b> to compare generations.</div>`,
              true
            );
            return;
          } else {
            if (firstNode === d) {
              showCompareModal(
                `<div class="modal-title">Comparison Mode</div>
                                 <div class="modal-message" style="color:#c0392b;">Please select a <b>different node</b> for comparison.</div>`,
                true
              );
              return;
            }
            // Calculate generation difference
            const diff = Math.abs(firstNode.depth - d.depth);
            showCompareModal(
              `<div class="modal-title">Comparison Result</div>
                             <div class="modal-message" style="line-height:1.6;">
                                <span style="color:#7d3c98;font-weight:bold;">${firstNode.data.name}</span>
                                <span style="font-size:1.12em;"> vs. </span>
                                <span style="color:#7d3c98;font-weight:bold;">${d.data.name}</span><br>
                                <span style="font-size:115%;color:#0078d7">Generation difference is <b>${diff}</b></span>
                             </div>`,
              false,
              true
            );
            comparisonTimeout = setTimeout(() => {
              exitCompareMode();
            }, 12000);
            return;
          }
        }

        // Node selection
        selectedNode = d;
        resetHighlight();
        highlightSubtree(d);
        updateActionButtons();
        modalRoot.innerHTML = "";
      });

    nodes
      .append("rect")
      .attr("x", -40)
      .attr("y", -30)
      .attr("width", 80)
      .attr("height", 60)
      .attr("rx", 10)
      .attr("fill", (d) => getColorByDepth(d.depth));

    nodes
      .append("text")
      .attr("dy", 5)
      .attr("text-anchor", "middle")
      .attr("fill", "#fff")
      .text((d) => d.data.name);
  }

  // --- Compare Mode Modal ---
  function showCompareModal(htmlBody, showCancel = false, onlyOk = false) {
    modalRoot.innerHTML = `
            <div class="modal-overlay" id="compare-modal" style="user-select: none;">
                ${htmlBody}
                <div class="modal-action-row">
                    ${
                      showCancel && !onlyOk
                        ? `<button class="cancel-btn" id="cancel-compare">Cancel</button>`
                        : ""
                    }
                    ${
                      onlyOk
                        ? `<button id="close-compare-modal">OK</button>`
                        : ""
                    }
                </div>
            </div>
        `;
    makeModalDraggable(document.getElementById("compare-modal"));

    if (showCancel && !onlyOk) {
      document.getElementById("cancel-compare").onclick = () => {
        exitCompareMode();
      };
    }
    if (onlyOk) {
      document.getElementById("close-compare-modal").onclick = () => {
        exitCompareMode();
      };
    }
  }

  function makeModalDraggable(modalEl) {
    let isDragging = false;
    let dragOffsetX = 0,
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
      modalEl.style.left = "unset";
      modalEl.style.top = "unset";
      modalEl.style.right = "unset";
      modalEl.style.bottom = "unset";
      modalEl.style.position = "fixed";
      modalEl.style.transform = "none";
      modalEl.style.zIndex = 3000;
      modalEl.style.margin = 0;
      modalEl.style.left = e.clientX - dragOffsetX + "px";
      modalEl.style.top = e.clientY - dragOffsetY + "px";
    });
    document.addEventListener("mouseup", function () {
      if (isDragging) {
        isDragging = false;
        modalEl.style.cursor = "grab";
      }
    });

    // Touch events for mobile
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
      if (isDragging) {
        isDragging = false;
      }
    });
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
        }).then(() => {
          modalRoot.innerHTML = "";
          alert("Correction submitted.");
          selectedNode = null;
          updateActionButtons();
        });
      }
    };
    document.getElementById("cancel-correction").onclick = () =>
      (modalRoot.innerHTML = "");
  });

  function getCSRFToken() {
    const cookie = document.cookie
      .split(";")
      .find((c) => c.trim().startsWith("csrftoken="));
    return cookie ? cookie.split("=")[1] : "";
  }

  function loadTreeData() {
    fetch("/data/")
      .then((res) => res.json())
      .then((data) => renderTree(data));
  }

  document.getElementById("reset-zoom")?.addEventListener("click", resetZoom);
  document
    .getElementById("reload-tree")
    ?.addEventListener("click", loadTreeData);

  loadTreeData();
  updateActionButtons();
});