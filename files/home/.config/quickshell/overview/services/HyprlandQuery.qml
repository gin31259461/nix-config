import QtQuick
import Quickshell
import Quickshell.Io
import "Refresh.js" as Refresh

Scope {
    id: root
    required property string query
    property bool streamDone: false
    property bool exitDone: false
    property bool pending: false
    property int exitCode: -1
    property string output: ""
    signal completed(string query, var value)

    function request() {
        if (pending) return;
        streamDone = false;
        exitDone = false;
        exitCode = -1;
        output = "";
        pending = true;
        watchdog.start();
        process.running = true;
    }

    function finish() {
        if (!pending || !streamDone || !exitDone) return;
        watchdog.stop();
        pending = false;
        const value = Refresh.parseResult(query, output, exitCode);
        if (value === null) console.warn("Overview query failed: " + query);
        completed(query, value);
    }

    Timer {
        id: watchdog
        interval: 3000
        onTriggered: {
            if (process.running) {
                process.signal(9);
            } else {
                root.exitDone = true;
                root.streamDone = true;
                root.exitCode = -1;
                root.finish();
            }
        }
    }

    Process {
        id: process
        command: ["/usr/bin/hyprctl", root.query, "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                root.output = text;
                root.streamDone = true;
                root.finish();
            }
        }
        onExited: (code, status) => {
            root.exitCode = status === 0 ? code : -1;
            root.exitDone = true;
            root.finish();
        }
    }
}
