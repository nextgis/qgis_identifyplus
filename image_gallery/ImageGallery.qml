import QtQuick 1.0

Rectangle {

    color: "#000000"
    
    Component {
        id: dndDelegate
        
        Item {
            id: imageCardItem
            width: dndGrid.cellWidth
            height: dndGrid.cellHeight
            
            Rectangle {
            	id: imageCard
            	
                anchors.centerIn: parent;
                width: dndGrid.cellWidth - 5
                height: dndGrid.cellHeight - 5
                border.width: 1
                border.color: "#777"
                color: "black"
                
                Rectangle {
                    id: image
                    
                    anchors.top: imageCard.top;
                    anchors.horizontalCenter: imageCard.horizontalCenter;
                    anchors.topMargin: 1;
                    
                    width: dndGrid.cellWidth - 5 - 10
                    height: dndGrid.cellHeight -5 -20
                    
                    color: "black"
                
	                Image {
	                    id: itemImage
	                    source: model.image.url_preview
	                    //anchors.centerIn: parent;
	                    anchors.fill: parent;
	                    smooth: true
	                    fillMode: Image.PreserveAspectFit
	                }
                }
                
                Rectangle {
                    id: controls
                    
                    anchors.bottom: imageCard.bottom;
                    anchors.horizontalCenter: imageCard.horizontalCenter;
                    
                    width: dndGrid.cellWidth - 5 - 10
                    height: 20
                    
                    color: "black"
                    
	                Rectangle
	                {
	                    id: deleteButton
	                    anchors.bottom: parent.bottom
	                    anchors.right: parent.right
	                    
	                    anchors.bottomMargin: 5;
	                    anchors.rightMargin: 2;
	                    
	                    width: 17
	                    height: 17
	                    color: "#000"
	                    
	                    Image {
	                        id: deleteButtonImage
	                        //anchors.fill: parent
	                        anchors.centerIn: parent;
	                        width: 16
	                        height: 16
	                        source: "icons/image_delete.png"
	                        smooth: true
	                        fillMode: Image.PreserveAspectFit                        
	                    }
	                    
	                    MouseArea {
	                        id: deleteButtonMouseArea
	                        anchors.fill: parent
	                        
	                        onClicked:
	                        {
	                            controller.deleteImageSlot(model.image)
	                        }
	                        onPressed:
	                        {
	                            parent.border.color = "#777"
	                        }
	                        onEntered:
	                        {
	                            parent.border.width = 1
	                            parent.border.color = "#fff"
	                        }
	                        onExited:
	                        {
	                            parent.border.width = 0
	                            parent.border.color = "#000"
	                        }
	                        hoverEnabled: true
	                    }
	                }
	                
	                Rectangle
	                {
	                    id: downloadButton
	                    anchors.bottom: parent.bottom
	                    anchors.right: deleteButton.left
	                    
	                    anchors.bottomMargin: 5;
	                    anchors.rightMargin: 2;
	                    
	                    width: 17
	                    height: 17
	                    color: "#000"
	                    
	                    Image {
	                        id: downloadButtonImage
	                        //anchors.fill: parent
	                        anchors.centerIn: parent;
	                        width: 16
	                        height: 16
	                        source: "icons/disk.png"
	                        smooth: true
	                        fillMode: Image.PreserveAspectFit
	                    }
	                    
	                    MouseArea {
	                        id: downloadButtonMouseArea
	                        anchors.fill: parent
	                        
	                        onClicked:
	                        {
	                            controller.downloadImageSlot(model.image)
	                        }
	                        
	                        onPressed:
	                        {
	                            parent.border.color = "#777"
	                        }
	                        onEntered:
	                        {
	                            parent.border.width = 1
	                            parent.border.color = "#fff"
	                        }
	                        onExited:
	                        {
	                            parent.border.width = 0
	                            parent.border.color = "#000"
	                        }
	                        
	                        hoverEnabled: true
	                    }
	                }
                }
            }
        }
    }

	function updateGallery()
	{
		console.log( "updateGallery" )
		console.log( dndGrid.model.count )
		if(dndGrid.model.count==0)
    	{
    		message.opacity = 1
    	}
    	else
    	{
    		message.opacity = 0
    	}
	}
	
    Rectangle 
    {
        id: gallery
        color: "#222222"
        anchors.fill: parent
    	
        GridView {
            id: dndGrid
            anchors.fill: parent
            anchors.margins: 10
            cellWidth: 150
            cellHeight: 150
            model: photoGalleryModel
            delegate: dndDelegate 
            
            /*
            onReset:
            {
            	console.log("QML. ModelReset" );
            	if(dndGrid.model.count==0)
            	{
            		message.opacity = 1
            	}
            	else
            	{
            		message.opacity = 0
            	}
            }
           	*/
            states: 
            [
            	State 
            	{
                	name: "ShowBars"
                	when: dndGrid.movingVertically
                	PropertyChanges { target: verticalScrollBar; opacity: 1 }
            	}
            	/*
            	,State 
            	{
                	name: "NoImages"
                	when:  {if(dndGrid.model.count==0) true}
                	PropertyChanges { target: message; opacity: 1 }
            	}
            	*/
            ]
        
        	
        }
		
		Text 
    	{
    		id: message
    		color: "#fff"
    		opacity: 0
        	anchors.centerIn: parent;
        	text: no_images_message
    	}
		
    	
         ScrollBar {
             id: verticalScrollBar
             width: 12; height: dndGrid.height-12
             anchors.right: dndGrid.right
             anchors.top: dndGrid.top
             opacity: 0
             orientation: Qt.Vertical
             position: dndGrid.visibleArea.yPosition
             pageSize: dndGrid.visibleArea.heightRatio
         }
        
        
    }

}