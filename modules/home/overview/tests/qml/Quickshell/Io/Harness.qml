pragma Singleton
import QtQuick
QtObject {
    property bool exitFirst: false
    property bool failStart: false
    property bool hang: false
    property string output: '[{"address":"0x1","workspace":{"id":1},"size":[640,480]}]'
    property int code: 0
    property int killed: 0
}
