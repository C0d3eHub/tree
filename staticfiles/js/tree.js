document.addEventListener("DOMContentLoaded", () => {
    const svg = d3.select("#tree-svg");
    const g = svg.append("g").attr("class", "tree-group");

    const container = document.getElementById("tree-container");
    const navHeight = document.querySelector("nav").offsetHeight;
    const footerHeight = document.querySelector("footer").offsetHeight;

    const zoom = d3.zoom()
        .scaleExtent([0.1, 3])
        .translateExtent([
            [-1000, -1000],
            [container.clientWidth + 1000, container.clientHeight + 1000]
        ])
        .on("zoom", (event) => {
            const t = event.transform;
            const yMin = navHeight - 50;
            const yMax = container.clientHeight - footerHeight + 50;
            if (t.y > yMin && t.y < yMax) {
                g.attr("transform", t);
            }
        });
    svg.call(zoom);

    const treeLayout = d3.tree().nodeSize([100, 150]);

    svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "0 -3 10 6")
        .attr("refX", 10)
        .attr("refY", 0)
        .attr("markerWidth", 5)
        .attr("markerHeight", 5)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-3L10,0L0,3")
        .attr("fill", "#cc3366");

    function getColorByDepth(depth) {
        const colors = ['#1abc9c', '#3498db', '#e67e22', '#9b59b6', '#e74c3c', '#f1c40f'];
        return colors[depth % colors.length];
    }

    function getDarkerColor(hex) {
        return d3.color(hex).darker(1.5).toString();
    }

    function renderTree(data) {
        g.selectAll("*").remove();
        const root = d3.hierarchy(data);
        treeLayout(root);

        // Centering logic
        const bounds = d3.extent(root.descendants(), d => d.x);
        const centerX = (bounds[0] + bounds[1]) / 2;
        const centerY = 0;

        svg.transition().duration(500)
            .call(zoom.transform, d3.zoomIdentity.translate(
                svg.node().clientWidth / 2 - centerX,
                svg.node().clientHeight / 4
            ));

        g.selectAll(".link")
            .data(root.links())
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("fill", "none")
            .attr("stroke", d => getDarkerColor(getColorByDepth(d.source.depth)))
            .attr("stroke-width", 2)
            .attr("marker-end", "url(#arrowhead)")
            .attr("d", d => {
                const startX = d.source.x;
                const startY = d.source.y + 30;
                const endX = d.target.x;
                const endY = d.target.y - 30;
                return `M${startX},${startY} 
                        V${(startY + endY) / 2} 
                        H${endX} 
                        V${endY}`;
            });

        const nodes = g.selectAll(".node")
            .data(root.descendants())
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.x},${d.y})`)
            .on("click", (event, d) => {
                event.stopPropagation();
                highlightSubtree(d);
            });

        nodes.append("rect")
            .attr("x", -40)
            .attr("y", -30)
            .attr("width", 80)
            .attr("height", 60)
            .attr("rx", 10)
            .attr("fill", d => getColorByDepth(d.depth));

        nodes.append("text")
            .attr("dy", 5)
            .attr("text-anchor", "middle")
            .attr("fill", "#fff")
            .text(d => d.data.name);
    }

    function loadTreeData() {
        fetch("/data/")
            .then(res => res.json())
            .then(data => renderTree(data));
    }

    loadTreeData();
});
