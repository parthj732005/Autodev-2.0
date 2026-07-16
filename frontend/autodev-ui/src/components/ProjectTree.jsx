import { useState } from "react";

function buildTree(files) {
  const tree = {};
  for (const path of files) {
    const parts = path.split("/");
    let node = tree;
    for (const part of parts) {
      node[part] = node[part] || {};
      node = node[part];
    }
  }
  return tree;
}

function TreeNode({ name, node, depth = 0 }) {
  const [open, setOpen] = useState(depth < 2);
  const isFolder = Object.keys(node).length > 0;

  return (
    <div>
      <button
        onClick={() => isFolder && setOpen((p) => !p)}
        className="flex items-center gap-1.5 w-full text-left py-0.5 hover:text-slate-100 transition-colors"
        style={{ paddingLeft: depth * 12 + 4 }}
      >
        {isFolder ? (
          <span className="text-slate-500 text-xs">{open ? "▼" : "▶"}</span>
        ) : (
          <span className="text-slate-600 text-xs">·</span>
        )}
        <span className={`text-xs font-mono ${isFolder ? "text-warning" : "text-slate-400"}`}>
          {name}
        </span>
      </button>
      {isFolder && open && (
        <div>
          {Object.entries(node).map(([child, childNode]) => (
            <TreeNode key={child} name={child} node={childNode} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProjectTree({ files = [], projectPath }) {
  const tree = buildTree(files);

  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Generated Files
        </h2>
        <span className="text-xs text-slate-600">{files.length} files</span>
      </div>

      {projectPath && (
        <div className="flex items-center gap-2 bg-surface-2 rounded-lg px-3 py-2">
          <span className="text-xs text-slate-500">Output:</span>
          <span className="text-xs font-mono text-success truncate">{projectPath}</span>
        </div>
      )}

      <div className="overflow-y-auto max-h-72">
        {Object.entries(tree).map(([name, node]) => (
          <TreeNode key={name} name={name} node={node} depth={0} />
        ))}
      </div>
    </div>
  );
}
