pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Hyprland
import "Refresh.js" as Refresh

Singleton {
    id: root
    property var windowList: []
    property var addresses: []
    property var windowByAddress: ({})
    property var workspaces: []
    property var workspaceIds: []
    property var workspaceById: ({})
    property var activeWorkspace: null
    property var monitors: []
    property var layers: ({})
    property var scheduler: Refresh.createScheduler()

    function request(names) {
        scheduler.request(names);
        // Start, not restart: sustained events cannot postpone refresh forever.
        if (!flush.running) flush.start();
    }

    function updateWindowList() { request(["clients"]); }
    function updateLayers() { request(["layers"]); }
    function updateMonitors() { request(["monitors"]); }
    function updateWorkspaces() { request(["workspaces", "activeworkspace"]); }
    function updateAll() { request(Refresh.queries); }

    function accept(query, value) {
        scheduler.complete(query);
        if (value !== null) {
            if (query === "clients") {
                const index = {};
                value.forEach(win => index[win.address] = win);
                windowByAddress = index;
                windowList = value;
                addresses = value.map(win => win.address);
            } else if (query === "workspaces") {
                const index = {};
                value.forEach(workspace => index[workspace.id] = workspace);
                workspaceById = index;
                workspaces = value;
                workspaceIds = value.map(workspace => workspace.id);
            } else if (query === "activeworkspace") activeWorkspace = value;
            else if (query === "monitors") monitors = value;
            else if (query === "layers") layers = value;
        }
        // Finish a dirty in-flight query once more; no event gets lost.
        if (!flush.running) flush.start();
    }

    function biggestWindowForWorkspace(workspaceId) {
        return windowList.filter(w => w.workspace.id === workspaceId).reduce((largest, window) => {
            const area = (window.size?.[0] ?? 0) * (window.size?.[1] ?? 0);
            const largestArea = (largest?.size?.[0] ?? 0) * (largest?.size?.[1] ?? 0);
            return area > largestArea ? window : largest;
        }, null);
    }

    Component.onCompleted: updateAll()
    Connections {
        target: Hyprland
        function onRawEvent(event) { root.request(Refresh.queriesForEvent(event.name)); }
    }
    Timer {
        id: flush
        interval: 40
        onTriggered: {
            const processes = {clients: clients, monitors: monitorsQuery, layers: layersQuery,
                workspaces: workspacesQuery, activeworkspace: activeWorkspaceQuery};
            root.scheduler.take().forEach(name => processes[name].request());
        }
    }
    HyprlandQuery { id: clients; query: "clients"; onCompleted: (query, value) => root.accept(query, value) }
    HyprlandQuery { id: monitorsQuery; query: "monitors"; onCompleted: (query, value) => root.accept(query, value) }
    HyprlandQuery { id: layersQuery; query: "layers"; onCompleted: (query, value) => root.accept(query, value) }
    HyprlandQuery { id: workspacesQuery; query: "workspaces"; onCompleted: (query, value) => root.accept(query, value) }
    HyprlandQuery { id: activeWorkspaceQuery; query: "activeworkspace"; onCompleted: (query, value) => root.accept(query, value) }
}
