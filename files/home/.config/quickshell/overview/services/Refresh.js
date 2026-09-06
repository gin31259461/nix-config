// Private, pure refresh policy shared by QML and isolated event tests.
var queries = ["clients", "monitors", "layers", "workspaces", "activeworkspace"];

function queriesForEvent(name) {
    if (/^(openlayer|closelayer)$/.test(name)) return ["layers", "monitors"];
    if (/^(monitoradded(v2)?|monitorremoved|configreloaded)$/.test(name)) return queries.slice();
    if (/^(workspace(v2)?|focusedmon(v2)?|createworkspace(v2)?|destroyworkspace(v2)?|moveworkspace(v2)?|renameworkspace|activespecial(v2)?)$/.test(name))
        return ["clients", "workspaces", "activeworkspace", "monitors"];
    if (/^(openwindow|closewindow|movewindow(v2)?|activewindow(v2)?|changefloatingmode|fullscreen|pin|windowtitle(v2)?|urgent|minimize)$/.test(name))
        return ["clients"];
    // Unknown events may affect geometry; preserve correctness across upgrades.
    return queries.slice();
}

function createScheduler() {
    var dirty = {};
    var running = {};
    return {
        request: function (names) { names.forEach(function (name) { dirty[name] = true; }); },
        take: function () {
            return queries.filter(function (name) {
                if (!dirty[name] || running[name]) return false;
                delete dirty[name];
                running[name] = true;
                return true;
            });
        },
        complete: function (name) { delete running[name]; }
    };
}

function parseResult(query, text, code) {
    if (code !== 0) return null;
    try {
        var value = JSON.parse(text);
        var object = function (item) { return item !== null && typeof item === "object" && !Array.isArray(item); };
        if (query === "layers") return object(value) ? value : null;
        if (query === "activeworkspace") return object(value) && Number.isInteger(value.id) ? value : null;
        if (!Array.isArray(value)) return null;
        if (query === "clients") {
            return value.every(function (item) {
                return object(item) && typeof item.address === "string" && object(item.workspace)
                    && Number.isInteger(item.workspace.id) && Array.isArray(item.size)
                    && item.size.length === 2 && item.size.every(Number.isFinite);
            }) ? value : null;
        }
        return value.every(function (item) { return object(item) && Number.isInteger(item.id); }) ? value : null;
    } catch (_) {
        return null;
    }
}
