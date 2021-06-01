import QtQuick.Layouts 1.4
import QtQuick 2.4
import QtQuick.Controls 2.0
import org.kde.kirigami 2.4 as Kirigami

import Mycroft 1.0 as Mycroft

Mycroft.Delegate {
    id: systemTextFrame
    skillBackgroundColorOverlay: "#000000"
    property bool hasTitle: sessionData.title ? true : false
    
    Component.onCompleted: {
        console.log(hasTitle)
    }

    contentItem: ColumnLayout {
        Label {
            id: systemTextFrameTitle
            Layout.fillWidth: true
            Layout.preferredHeight: hasTitle ? parent.height / 3 : 0
            maximumLineCount: 2
            minimumPixelSize: 12
            fontSizeMode: Text.Fit
            font.pixelSize: height * 0.50
            wrapMode: Text.Wrap
            horizontalAlignment: Text.AlignHCenter
            visible: hasTitle
            enabled: hasTitle
            font.family: "Noto Sans"
            font.weight: Font.Bold
            text: sessionData.title
        }
        
       Label {
            id: systemTextFrameMainBody
            Layout.fillWidth: true
            Layout.fillHeight: true
            wrapMode: Text.Wrap
            font.family: "Noto Sans"
            font.weight: Font.Bold
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            minimumPixelSize: 12
            fontSizeMode: Text.Fit;
            font.pixelSize: 1024
            text: sessionData.text
        }
    }
}
 
