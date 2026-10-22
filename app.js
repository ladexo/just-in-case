// Rendering only. All planning decisions come from the real Python agent (agent/) running in Pyodide.
const $ = (id) => document.getElementById(id);
const LABELS = {ride_home:"Ride home", pet_care:"Pet care", home_access:"Home access", power_outage:"Power outage", fall:"If I fall"};
const ROUTE = {service:"Service", preparation:"Preparation", person:"Person you chose", blank:"Not covered yet"};
const COST = {free:"Free", low:"Low cost", paid:"Paid"};
let py = null, plan = null;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const label = (n) => LABELS[n] || n.replace(/_/g," ").replace(/^./, c => c.toUpperCase());

async function boot() {
  $("app").classList.add("busy");
  py = await loadPyodide();
  const files = (await (await fetch("py/manifest.txt")).text()).trim().split("\n");
  py.FS.mkdirTree("/home/pyodide/jic/agent");
  for (const f of files) py.FS.writeFile("/home/pyodide/jic/" + f, await (await fetch("py/" + f)).text());
  py.FS.writeFile("/home/pyodide/jic/bridge.py", await (await fetch("bridge.py")).text());
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide/jic'); import bridge");
  $("loading").hidden = true; $("app").classList.remove("busy");
  say("bot", "Hello. I'm a planning helper. I can't call anyone or send anything. Let's make a simple plan together.");
  runAgent("");
}

function form(message) {
  return {name:$("f-name").value.trim(), date:$("f-date").value, pet:$("f-pet").value.trim(), friends:$("f-friends").value,
          burden:$("f-burden").checked, escort:$("f-escort").checked, message};
}

function runAgent(message) {
  const fn = py.globals.get("bridge").plan_json;
  plan = JSON.parse(fn(JSON.stringify(form(message))));
  if (message) {
    const r = plan.replies.length ? plan.replies : ["I've updated your plan on the right."];
    r.forEach(t => say("bot", t));
  }
  render();
}

function say(who, text) {
  const d = document.createElement("div"); d.className = "msg " + who;
  d.innerHTML = `<b>${who === "you" ? esc($("f-name").value || "You") : "Just in Case"}</b>${esc(text)}`;
  $("log").appendChild(d); $("log").scrollTop = $("log").scrollHeight;
}

function render() {
  const el = $("plan");
  if (plan.paused) {
    el.innerHTML = `<div class="card paused"><h3>Plan set aside for now</h3><p>${esc(plan.replies[0])}</p>
      <p><strong>Call or text 988</strong> any time. In danger, call <strong>911</strong>.</p></div>`;
    $("note").hidden = true; return;
  }
  el.innerHTML = plan.needs.map(n => {
    const svcs = n.services.map(s => {
      const flags = [s.call_to_confirm && "Call to confirm", s.waitlist && "Waitlist", s.stale && "Info may be old"].filter(Boolean);
      const contact = s.phone ? `<a href="tel:${esc(s.phone.replace(/[^0-9]/g,""))}">${esc(s.phone)}</a>` : `<a href="${esc(s.url)}" target="_blank" rel="noopener">see website</a>`;
      return `<div class="svc"><div class="nm">${esc(s.name)}</div><div>Phone: ${contact}</div>
        ${COST[s.cost] ? `<span class="tag cost">${COST[s.cost]}</span>` : `<span class="tag">Cost: ${esc(s.cost)}</span>`}
        ${flags.map(f => `<span class="tag flag">⚑ ${f}</span>`).join("")}</div>`;
    }).join("");
    const notes = n.notes.map(t => `<p>${/escort rule/i.test(t) ? '<span class="tag flag">⚑ Escort rule</span> ' : '<span class="tag flag">⚑</span> '}${esc(t)}</p>`).join("");
    return `<article class="card need"><h3>${esc(label(n.need))} <span class="route">${ROUTE[n.status] || esc(n.status)}</span></h3>
      ${svcs}${n.preparations.length ? `<p><strong>Prepare:</strong></p><ul>${n.preparations.map(p => `<li>${esc(p)}</li>`).join("")}</ul>` : ""}
      ${n.person ? `<p><strong>Helper you chose:</strong> ${esc(n.person.join(", "))}</p>` : ""}${notes}</article>`;
  }).join("") + `<div class="card">${plan.footer.map(f => `<p>${esc(f)}</p>`).join("")}</div>`;
  renderNote();
}

function renderNote() {
  const box = $("note");
  if (!plan.note) { box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = `<h2>Draft note (not sent)</h2><p>For: ${esc(plan.approval.recipients.join(", "))}</p><pre>${esc(plan.note)}</pre>
    <p>This app never sends anything. If you like it, you send it yourself.</p>
    <button class="primary" id="ap">Approve for me to send myself</button> <button class="secondary" id="dc">Decline</button>`;
  $("ap").onclick = () => {
    const res = JSON.parse(py.globals.get("bridge").approve_json(plan.approval.id));
    box.innerHTML = `<h2>Approved — for you to send yourself</h2><pre id="nt">${esc(plan.note)}</pre>
      <p><strong>Nothing was sent.</strong> ${esc(res.send_refused || "")}</p><button class="primary" id="cp">Copy text</button> <span id="cpok" role="status"></span>`;
    $("cp").onclick = async () => { try { await navigator.clipboard.writeText(plan.note); $("cpok").textContent = "Copied."; } catch { $("cpok").textContent = "Select the text above and copy it."; } };
  };
  $("dc").onclick = () => { box.innerHTML = `<h2>Note declined</h2><p>No problem. Nothing was shared. Your plan still works without it.</p>`; };
}

// Mirrors card/make_card.py card_lines(): only plan fields, fixed template labels.
function cardLines(p) {
  const out = [["h1", `${p.user || ""}'s Just in Case card`]];
  for (const n of p.needs || []) {
    out.push(["h2", label(n.need)]);
    for (const s of (n.services || []).slice(0,1)) { out.push(["b", `${s.name}  —  ${s.phone || "see website"}`]); if (s.call_to_confirm) out.push(["t","Call to confirm first."]); }
    if (n.person) out.push(["t", "Helper: " + n.person.join(", ")]);
    for (const x of (n.preparations || []).slice(0,1)) out.push(["t", x]);
    for (const x of n.notes || []) out.push(["t", x]);
  }
  for (const f of p.footer || []) if (!f.includes("911")) out.push(["s", f]);
  return out;
}
function showCard() {
  const tag = {h1:"h1", h2:"h2", b:"p><strong", t:"p", s:"p class='fr-s'"};
  const body = cardLines(plan).map(([st,t]) => st === "b" ? `<p><strong>${esc(t)}</strong></p>` : st === "s" ? `<p class="fr-s">${esc(t)}</p>` : `<${st === "t" ? "p" : st}>${esc(t)}</${st === "t" ? "p" : st}>`).join("");
  $("fridge").innerHTML = `<div class="fr-actions"><button class="primary" onclick="window.print()">Print</button><button class="secondary" id="back">Back to plan</button></div>
    <div class="fr-911">EMERGENCY: CALL 911</div><div class="fr-988">Feeling unsafe or alone? Call or text 988, any time.</div>${body}`;
  document.body.classList.add("cardview"); $("back").onclick = () => document.body.classList.remove("cardview");
}

$("intake").onsubmit = (e) => { e.preventDefault(); say("you", "Please update my plan."); runAgent(""); say("bot", plan.paused ? plan.replies[0] : "I've updated your plan on the right."); };
$("chatform").onsubmit = (e) => { e.preventDefault(); const t = $("msg").value.trim(); if (!t) return; $("msg").value = ""; say("you", t); runAgent(t); };
document.querySelectorAll(".chip").forEach(b => b.onclick = () => { say("you", b.textContent); runAgent(b.textContent); });
$("printbtn").onclick = () => { if (plan && !plan.paused) showCard(); };
const d = new Date(); d.setMonth(d.getMonth() + 1); $("f-date").value = d.toISOString().slice(0,10);
boot().catch(e => { $("loading").textContent = "Sorry, the planner could not load. Please refresh the page. (" + e.message + ")"; console.error(e); });
