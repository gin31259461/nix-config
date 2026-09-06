import QtQuick
QtObject {
    id: root
    property bool running: false
    property var command: []
    property QtObject stdout
    signal exited(int exitCode, int exitStatus)
    function finish() {
        stdout.text = Harness.output;
        if (Harness.exitFirst) exited(Harness.code, 0);
        stdout.streamFinished();
        if (!Harness.exitFirst) exited(Harness.code, 0);
        running = false;
    }
    function signal(number) {
        Harness.killed += 1;
        Harness.code = number;
        finish();
    }
    onRunningChanged: {
        if (!running) return;
        if (Harness.failStart) { running = false; return; }
        if (!Harness.hang) Qt.callLater(root.finish);
    }
}
