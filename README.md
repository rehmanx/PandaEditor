## A level / scene editor for Panda3d game engine with bare minimum features to provide an editor centric workflow.

### Current features
1. Object manipulation
2. Support for runtime user modules 
3. Editor plugin support
4. Properties panel 
5. File browser
6. Console panel

### Short term planned features
1. Gizmos needs improvement
2. Object manipulation needs improvement
3. A scene graph
4. Undo / redo system
5. Code cleanup

### Dependencies
1. WxPython
2. Python Watch dog

### Install
1. 

### Setting up a project 
1. PandaEditor is project based in order to work, you will first have to setup a project.
To setup a project go to **Menu bar > Project** set a project name and select an empty folder.

### Working in scene editor.
 
### Resources
Resources in PandaEditor are 3d models, audio, videos, python modules, shaders etc.
The **resources browser** panel displays contents from project path directory.
To import resources from outside into your current project.

**External resources**
PandaEditor has support to append resources outside of your current project directory.
Go to **Menu bar > Project > Append External Resources > select a resource directory** to append an external resource directory to your current project, PandaEditor will immediately start monitoring changes in any appended external resource directory.

### Properties panel.
Properties panel displays properties of the currently selected editor item, an editor item can be any scene object or editor resource.

### Object manipulation 
PandaEditor has bare minimum object manipulation you can add, remove and transform an object in scene view.

### User modules
are programming resources, written in pure python, they allow users to extend or program in PandaEditor.
PandaEditor has 2 types of user modules
1. Editor plugins and
2. User modules

#### Editor plugins
are extensions to extend PandaEditor with custom tools, they are executed in both editor and game modes.
Editor plugins inherit from PToolBase.
Format of editor plugin.
 
#### User modules
are executed only in runtime mode, they inherit from PModBase.
Format of user modules.
