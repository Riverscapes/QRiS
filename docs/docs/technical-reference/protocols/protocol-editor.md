---
title: Protocol Editor
sidebar_position: 2
---

The QRiS Protocol Editor is a simple user interface for editing protocol XML files. The goal is to make it easier to author QRiS Protocol XML by not having to learn the detailed XML specification. The software doesn't complete remove the need to understand the XML syntax. Users still must review the XML that they commit and push to GitHub manually. However, the software helps avoid silly mistakes and having to remember all the XML options.

## How It Works

Users must clone the [RiverscapesXML GitHub repository](https://github.com/Riverscapes/RiverscapesXML) to their local computer. They then launch the protocol editor software and point it to the `QriS/protocols` subfolder in this repository. The software then lets you pick an individual QRiS protocol XML file to edit and save changes. Finally, users review and commit their changes, before creating a pull request for the QRiS development team to review.

## Installation

The QRiS Protocol Editor is deistributed as a single executable for Windows. You can simply download this one file and place it anywhere on your computer. Double click it in Windows Explorer to run the software. The software does not need to be installed. (MacOS or Linux users should contact the QRiS devleopment team for a deployment.)

## Using the Software

When the software first opens you are presented with a file browser window for picking the folder where you have cloned the [RiverscapesXML GitHub repository](https://github.com/Riverscapes/RiverscapesXML) onto you computer. Pick the `QRiS/protocols` folder inside this local repo. The software will automatically look for the `protocol.xsd` rule file in the parent folder. Alternatively you can browse and use a different XSD file if you are developing or testing different versions of this file.

### Main Window

The main window is where you pick which protocol you want to edit, using the dropdown in the top left of the window. You can then edit the layers and metrics within the selected protocol by clicking on the desired item in the tree on the left. Properties are shown and edited on the right. Changes are saved to the XML file whenever the focus changes between controls. The XML file is validated with each change and warnings preventing you from proceeding until the problem is resolved.

![Main window](/images/technical-reference/protocol-editor/field-properties.png)

### Reviewing and Saving Changes

The QRis Protocol Editor is meant to help you produce QRiS protocols, but its vital that you review the XML that the software produces before committing and pushing your loca lcopy of the Riverscapes XML to GitHub. Use a visual difference tool such as [GitKraken](https://gitkraken.com/) or [GitGraph](https://marketplace.visualstudio.com/items?itemName=mhutchie.git-graph) in Visual Studio Code. Commit and push your code to trigger automated checks that ensure that the protocol XML files validate. Create a pull request to trigger a review by the QRiS development team who will integrate your changes once they have performed a final review.

