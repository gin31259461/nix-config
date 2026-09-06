import QtQuick
import QtTest
import Quickshell.Io
import "subject"

TestCase {
    id: test
    name: "OverviewQuery"
    property int completions: 0
    property var result: null
    HyprlandQuery {
        id: query
        query: "clients"
        onCompleted: (name, value) => { test.completions += 1; test.result = value; }
    }
    function init() {
        completions = 0;
        result = null;
        Harness.exitFirst = false;
        Harness.failStart = false;
        Harness.hang = false;
        Harness.code = 0;
        Harness.output = '[{"address":"0x1","workspace":{"id":1},"size":[640,480]}]';
        Harness.killed = 0;
    }
    function test_signal_order_data() { return [{tag: "stream first", exitFirst: false}, {tag: "exit first", exitFirst: true}]; }
    function test_signal_order(data) {
        Harness.exitFirst = data.exitFirst;
        query.request();
        tryCompare(test, "completions", 1);
        compare(result[0].workspace.id, 1);
        compare(query.pending, false);
    }
    function test_invalid_output() {
        Harness.output = "private invalid json";
        query.request();
        tryCompare(test, "completions", 1);
        compare(result, null);
    }
    function test_watchdog_data() { return [{tag: "failed start", failStart: true}, {tag: "hung command", failStart: false}]; }
    function test_watchdog(data) {
        Harness.failStart = data.failStart;
        Harness.hang = !data.failStart;
        query.request();
        tryCompare(test, "completions", 1, 4500);
        compare(result, null);
        compare(query.pending, false);
        compare(Harness.killed, data.failStart ? 0 : 1);
    }
}
