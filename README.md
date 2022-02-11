Simple level / scene editor for Panda3d game engine with bare minimum features to provide a Unity engine style editor centric workflow.

Features
1. Gizmos for object manipulation
2. Support for runtime user modules 
3. Editor plugin support
4. Properties panel 
5. File browser
6. Console 

Short term planned features
1. Gizmos needs improvement
2. A scene graph
3. Undo / redo system
4. Code cleanup

Dependencies
1. WxPython
2. Python Watch dog

Install
1. 

Setting up a project 
1. PandaEditor is project based in order to work, you will first have to setup a project.
To setup a project go to **Menu bar > Project** set a project name and select an empty folder.

Working in scene editor.
 

Editor resources
Resources in PandaEditor are 3d models, audio, videos, python modules, shaders etc.
The **resources browser** panel displays contents from project path folder.
To import resources from outside to your current project , PandaEditor will immediately start monitoring changes in any appended library.

Properties panel.
Properties panel displays properties of the currently selected editor item, an editor item can be any scene object or editor resource.

Libraries.
PandaEditor has support for libraries, libraries are resources outside of your current project folder.
Go to **Menu bar > Project > Append library** to append a library to your current project

Object manipulation 
PandaEditor has bare minimum object manipulation you can add, remove and transform an object in scene view.


User modules
are programming resources, written in pure python, they allow users to extend or program in PandaEditor.
PandaEditor has 2 types of user modules
1. Editor plugins
2. User modules

Editor plugins
are extensions to extend PandaEditor with custom tools, they are executed in both editor and game modes.
Editor plugins inherit from PToolBase.
Format of editor plugin.
 
User modules
are executed only in runtime mode, they inherit from PModBase.
Format of user modules.

