"""Assemble explainer.html from the kit engine (engine_head.txt), the scene (scene.js) and the input data,
then check the scene's two gate functions against all 22 recorded decisions with node."""
import json, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parents[4] / "visual-skills" / "evals" / "guardrail-gates" / "files" / "data.json"
data = json.loads(SRC.read_text(encoding="utf-8"))
keys = data["gates"]
slim = {
    "requests": [{"id": r["id"], "operation": r["operation"], "target": r["target"], "expected_allow": r["expected_allow"],
                  "d": [int(r["decisions"][g]) for g in keys]} for r in data["requests"]],
    "summary": data["summary"],
    "broker_audit": data["broker_audit"],
}
assert keys == ["observe only", "lexical prefix", "scoped capabilities", "read only", "approval bound"]
scene = (HERE / "scene.js").read_text(encoding="utf-8").replace("/*DATA*/null", json.dumps(slim, ensure_ascii=False))
html = (HERE / "engine_head.txt").read_text(encoding="utf-8") + scene + "\n</script>\n</body></html>\n"
(HERE / "explainer.html").write_text(html, encoding="utf-8")
print("wrote explainer.html", len(html), "bytes")

# check the lesson's gate functions reproduce every recorded decision of every gate
start, end = scene.index("// GATES-BEGIN"), scene.index("// GATES-END")
test = "const DATA=" + json.dumps(slim) + ";\n" + scene[start:end] + r"""
let bad = 0;
for (const r of DATA.requests) {
  const ap = r.id !== 'untrusted_approval';
  const mine = [1, +prefixGate(r.operation, r.target, ap).ok, +scopedGate(r.operation, r.target, ap).ok,
                +scopedGate(r.operation, r.target, ap, true).ok, +scopedGate(r.operation, r.target, ap).ok];
  if (mine.join() !== r.d.join()) { bad++; console.log('MISMATCH', r.id, mine.join(), 'recorded', r.d.join()); }
}
for (const id of ['traversal','linked_target','link_then_parent']) { const r = DATA.requests.find(x => x.id === id); console.log(id, '->', resolvePath(r.target).end); }
console.log(bad ? bad + ' mismatches' : 'all 22 x 5 decisions reproduced');
process.exit(bad ? 1 : 0);
"""
res = subprocess.run(["node", "-e", test], capture_output=True, text=True)
print(res.stdout, res.stderr)
sys.exit(res.returncode)
